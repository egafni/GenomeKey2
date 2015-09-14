import re
import os
import decorator
from genomekey import settings as s
import random
from cosmos.util.helpers import random_str
import string


def cp(from_, to, recursive=False, quiet=False):
    # if is_dir:
    if to.endswith('/') or from_.endswith('/'):
        recursive=True
    return 'aws s3 cp{quiet}{recursive} {from_} {to}'.format(
        from_=from_,
        to=to,
        quiet=' --quiet' if quiet else '',
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
#         return os.path.join(s3_root, file_path)

def split_bucket_key(s3_path):
    bucket, key = re.search('s3://(.+?)/(.+)', s3_path).groups()
    return bucket, key


def stream_in(path, md5=True):
    bucket, key = split_bucket_key(path)
    md5 = ' ' if md5 else ' --no-md5'
    return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


# def get_inputs(s3_root, input_file_paths):
#     """
#     Downloads inputs from s3_root into their relative path on the filesystem
#
#     ex get_inputs("s3://bucket/folder", "a/b") would download file "b" into "a/b"
#     """
#
#     def g():
#         for path in input_file_paths:
#             yield cp(os.path.join(s3_root, path), path)
#
#     return "\n".join(g())
#
#
# def push_outputs(s3_root, output_file_paths):
#     return "\n".join(cp(path, os.path.join(s3_root, path)) for path in output_file_paths)


from cosmos.api import NOOP


def can_stream(input_param_names):
    s3_streamables = input_param_names if isinstance(input_param_names, list) else [input_param_names]

    def wrapper(fxn, *args, **kwargs):
        # fxn.s3_streamables = s3_streamables
        return fxn(*args, **kwargs)

    wrapper.s3_streamables = s3_streamables
    return decorator.decorator(wrapper)


def skip_pull(input_param_names):
    def wrapper(fxn, *args, **kwargs):
        fxn.skip_pulls = input_param_names if isinstance(input_param_names, list) else [input_param_names]
        return fxn(*args, **kwargs)

    return decorator.decorator(wrapper)


from cosmos.core.cmd_fxn.signature import default_cmd_fxn_wrapper
import funcsigs


def make_wrapper(bucket):
    def s3_cmd_fxn_wrapper(task, input_map, output_map):
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
            1) If input starts with s3:// or bucket is set, pull or stream
            3) If bucket is set, push outputs to S3
            """

            s3_streamables = getattr(fxn, 's3_streammables', [])

            # for some reason decorator is using args instead of kwargs..
            # repopulate kwargs manually
            for i, (k, parameter) in enumerate(funcsigs.signature(fxn).parameters.items()):
                kwargs[k] = args[i]

            def process_input_map():
                def process_input_value(input_value):
                    """
                    :returns: s3_copy_command, new_input_value
                    """
                    if input_value in s3_streamables:
                        return None, stream_in(input_value)
                    else:
                        if input_value.startswith('s3://'):
                            basename = 'tmp-%s__%s' % (random_str(6), os.path.basename(input_value))
                            return cp(input_value, basename), basename
                        else:
                            return cp(os.path.join(bucket, input_value), input_value), input_value

                s3_pull_all_inputs = []

                if not task.tags.get('skip_s3_pull', False):
                    for input_name, input_value in input_map.items():
                        if isinstance(input_value, list):
                            cp_strs, new_input_value = zip(*map(process_input_value, input_value))
                            s3_pull_all_inputs += cp_strs
                            kwargs[input_name] = new_input_value
                        else:
                            cp_str, new_input_value = process_input_value(input_value)
                            s3_pull_all_inputs.append(cp_str)
                            kwargs[input_name] = new_input_value

                return "\n".join(s3_pull_all_inputs)

            s3_pull_all_inputs_cmd = process_input_map()

            prepend = '#!/bin/bash\n' \
                      'set -e\n' \
                      'set -o pipefail\n\n' \
                      'TMP_DIR=`mktemp -d --tmpdir={s[gk][tmp_dir]} {fxn.__name__}_XXXXXXXXX` \n' \
                      'echo "Created temp dir: $TMP_DIR" > /dev/stderr\n' \
                      'cd $TMP_DIR\n' \
                      '{make_output_dir}\n' \
                      '{s3_pull_all_inputs}\n' \
                      '\n'.format(s=s,
                                  fxn=fxn,
                                  s3_pull_all_inputs=s3_pull_all_inputs_cmd,
                                  make_output_dir='mkdir -p %s\n' % task.output_dir if task.output_dir and task.output_dir != '' else '',
            )

            def gen_pushes():
                if bucket:
                    for output_vals in output_map.values():
                        if not isinstance(output_vals, list):
                            output_vals = [output_vals]
                        for out in output_vals:
                            yield cp(out, os.path.join(bucket, out))

            append = '\n\n' \
                     '{s3_push_all_outputs}\n' \
                     'rm -rf $TMP_DIR'.format(s=s,
                                              s3_push_all_outputs="\n".join(gen_pushes()))
            # if 'fastqc' in fxn.__name__:
            #     raise

            r = fxn(**kwargs)

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
#             local_path = os.path.join(local_dir, os.path.basename(file_path))
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
    subprocess.check_call(cmd, shell=True)