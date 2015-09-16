import re
import os
import decorator
import sys
from genomekey.api import settings as s
from cosmos.core.cmd_fxn.io import Forward
import random
import subprocess as sp
from cosmos.util.helpers import random_str
from functools import partial
import string
import sys

opj = os.path.join


def dir_exists(path):
    return sp.Popen('aws s3 ls %s' % path, shell=True, stdout=sp.PIPE).wait() == 0


def cp(from_, to, recursive=False, quiet=False, only_show_errors=True):
    # todo try switching to gof3r, may be much faster
    # if is_dir:
    if to.endswith('/') or from_.endswith('/'):
        recursive = True
    return 'aws s3 cp{quiet}{only_show_errors}{recursive} {from_} {to}'.format(
        from_=from_,
        to=to,
        quiet=' --quiet' if quiet else '',
        only_show_errors=' --only-show-errors' if only_show_errors else '',
        recursive=' --recursive' if recursive else ''
    )
    # else:
    # return 'aws s3 cp --quiet %s %s' % (from_, to)


# def path_to_s3path(s3_root, file_path):
# """
# gets the s3 path for a file_path
# """
# if file_path.startswith('s3://'):
# return file_path
# else:
# return opj(s3_root, file_path)

def split_bucket_key(s3_path):
    bucket, key = re.search('s3://(.+?)/(.+)', s3_path).groups()
    return bucket, key


def stream_in(path, md5=False):
    # bucket, key = split_bucket_key(path)
    return '<(aws s3 cp %s -)' % path
    # md5 = '' if md5 else ' --no-md5'
    # return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


def stream_out(path):
    return '>(aws s3 cp - %s)' % path


# def get_inputs(s3_root, input_file_paths):
# """
# Downloads inputs from s3_root into their relative path on the filesystem
#
# ex get_inputs("s3://bucket/folder", "a/b") would download file "b" into "a/b"
#     """
#
#     def g():
#         for path in input_file_paths:
#             yield cp(opj(s3_root, path), path)
#
#     return "\n".join(g())
#
#
# def push_outputs(s3_root, output_file_paths):
#     return "\n".join(cp(path, opj(s3_root, path)) for path in output_file_paths)


from cosmos.api import NOOP


def can_stream(input_param_names):
    if not isinstance(input_param_names, list) and not isinstance(input_param_names, tuple):
        input_param_names = [input_param_names]

    def wrapper(fxn):
        fxn.can_stream = input_param_names
        return fxn

    return wrapper


# def skip_pull(input_param_names):
#     if not isinstance(input_param_names, list) and not isinstance(input_param_names, tuple):
#         input_param_names = [input_param_names]
#
#     def wrapper(fxn):
#         fxn.skip_pulls = input_param_names
#         return fxn
#
#     return wrapper


from cosmos.core.cmd_fxn.signature import default_cmd_fxn_wrapper
import funcsigs


def make_s3_cmd_fxn_wrapper(s3_path):
    def s3_cmd_fxn_wrapper(task, stage_name, input_map, output_map):
        """
        Create and cd into a tmp dir
        Create the task's output_dir
        Pull inputs from S3
        Run the command
        Push outputs to S3
        delete the tmp_dir
        """

        def wrapped(fxn, *args, **kwargs):
            """
            1) If input starts with s3:// or s3_path is set, pull or stream
            3) If s3_path is set, push outputs to S3
            """
            fxn_sig = funcsigs.signature(fxn)

            # for some reason decorator.decorator is using args instead of kwargs..
            # repopulate kwargs manually.
            for i, (k, parameter) in enumerate(fxn_sig.parameters.items()):
                kwargs[k] = args[i]

            # HANDLE INPUTS

            def process_input_map():
                # TODO this function should probably be refactored for readability
                def process_input_value(input_param_name, file_path):
                    """
                    :returns: s3_copy_command, new_input_value
                    """
                    if input_param_name in getattr(fxn, 'can_stream', []):
                        # do not pull, change value to stream in
                        if file_path.startswith('s3://'):
                            return None, stream_in(file_path)
                        else:
                            return None, stream_in(opj(s3_path, file_path))
                    else:
                        if file_path.startswith('s3://'):
                            # pull to cwd as a temp file (it'll get deleted when $TMP_DIR is deleted)
                            basename = 'tmp-%s__%s' % (random_str(6), os.path.basename(file_path))
                            return cp(file_path, basename), basename
                        else:
                            # pull into relative path
                            return cp(opj(s3_path, file_path), file_path), file_path

                s3_pull_all_inputs = []

                for input_name, input_value in input_map.items():
                    if isinstance(input_value, list):
                        cp_strs, new_input_value = zip(*map(partial(process_input_value, input_name), input_value))
                        s3_pull_all_inputs += cp_strs
                        kwargs[input_name] = new_input_value
                    else:
                        cp_str, new_input_value = process_input_value(input_name, input_value)
                        s3_pull_all_inputs.append(cp_str)
                        kwargs[input_name] = new_input_value

                return "\n".join(filter(bool, s3_pull_all_inputs))  # remove the Nones for stream_in

            s3_pull_all_inputs_cmd = process_input_map() if not task.tags.get('skip_s3_pull', False) else ''

            prepend = """#!/bin/bash
set -e
set -o pipefail

TMP_DIR=`mktemp -d --tmpdir={s[gk][tmp_dir]} {stage_name}_XXXXXXXXX`
echo "Created temp dir: $TMP_DIR" > /dev/stderr
trap "rm -rf $TMP_DIR" EXIT
cd $TMP_DIR

{make_output_dir}
# S3: Pull inputs
{s3_pull_all_inputs}\n\n""".format(s=s,
                                   stage_name=stage_name,
                                   s3_pull_all_inputs=s3_pull_all_inputs_cmd,
                                   make_output_dir='mkdir -p %s\n' % task.output_dir if task.output_dir and task.output_dir != '' else '',
            )

            # HANDLE OUTPUTS

            def gen_pushes():
                if s3_path:
                    for output_name, output_vals in output_map.items():
                        if isinstance(fxn_sig.parameters[output_name].default, Forward):
                            # do not s3 push if this is a forwarded input
                            continue
                        else:
                            if not isinstance(output_vals, list):
                                output_vals = [output_vals]

                            for out_val in output_vals:
                                if output_name in getattr(fxn, 'can_stream', []):
                                    kwargs[output_name] = stream_out(opj(s3_path, out_val))
                                    # do not push since we're streaming
                                else:
                                    yield cp(out_val, opj(s3_path, out_val))

            append = '\n\n' \
                     '#S3: Push Outputs\n' \
                     '{s3_push_all_outputs}\n'.format(s=s,
                                                      s3_push_all_outputs="\n".join(gen_pushes()))

            r = fxn(**kwargs)
            # print prepend, r, append
            # if 'bwa' in fxn.__name__:
            #     raise

            if r == NOOP:
                return NOOP
            else:
                return prepend + r + append

        return decorator.decorator(wrapped)


    return s3_cmd_fxn_wrapper

    # def pull_if_s3(file_paths, local_dir='./'):

#     """
#     Pull from s3 if the path has s3:// in it
#     """
#
#     def check_for_s3(file_path):
#         if file_path.startswith('s3://'):
#             local_path = opj(local_dir, os.path.basename(file_path))
#             return local_path, cp(file_path, local_path) + "\n"
#         else:
#             return file_path, ''
#
#     local_path, s3_pull_cmds = zip(*[check_for_s3(tf) for tf in file_paths])
#     return local_path, ''.join(s3_pull_cmds).strip()


import subprocess


def delete_s3_dir(s3_path, skip_confirm=False):
    from cosmos.util.helpers import confirm

    if not skip_confirm:
        confirm("Are you sure you want to delete %s?" % s3_path)
    cmd = 'aws s3 rm %s --recursive --only-show-errors' % s3_path
    print >> sys.stderr, cmd
    subprocess.check_call(cmd, shell=True)