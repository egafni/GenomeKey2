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

import jinja2
from cosmos.api import NOOP
from cosmos.util.iterstuff import partition
from . import cmd as s3cmd

opj = os.path.join


def can_stream(input_param_names):
    # note must be the outer most decorator
    if not isinstance(input_param_names, list) and not isinstance(input_param_names, tuple):
        input_param_names = [input_param_names]

    def wrapper(fxn):
        fxn.can_stream = input_param_names
        return fxn

    return wrapper


# def skip_pull(input_param_names):
# if not isinstance(input_param_names, list) and not isinstance(input_param_names, tuple):
# input_param_names = [input_param_names]
#
# def wrapper(fxn):
# fxn.skip_pulls = input_param_names
# return fxn
#
# return wrapper


import funcsigs
from cosmos.core.cmd_fxn.signature import default_prepend


def shared_fs_cmd_fxn_wrapper(task, stage_name, input_map, output_map):
    """
    WARNING this function signature is not set in stone yet and may change, replace at your own risk.

    :param task:
    :param input_map:
    :param output_map:
    :return:
    """

    def real_decorator(fxn, *args, **kwargs):
        fxn_sig = funcsigs.signature(fxn)

        # for some reason decorator.decorator is using args instead of kwargs..
        # repopulate kwargs manually.
        for i, (k, parameter) in enumerate(fxn_sig.parameters.items()):
            kwargs[k] = args[i]

        def to_stream(value):
            if value.startswith('s3://'):
                return s3cmd.stream_in(value)
            else:
                return '<(%s)' % value

        # def to_pull(value):
        #     if value.startswith('s3://'):
        #         tmp_file = 'tmp-%s__%s' % (random_str(6), os.path.basename(value))
        #         s3_pull_path = value
        #         return s3cmd.cp(s3_pull_path, tmp_file, chrom=task.tags.get('contig')), tmp_file



        for key, value in input_map.items():
            if key in getattr(fxn, 'can_stream', []):
                if isinstance(value, list):
                    kwargs[key] = map(to_stream, value)
                else:
                    kwargs[key] = to_stream(value)
            # else:
            #     if isinstance(value, list):
            #         kwargs[key] = map(to_pull, value)
            #     else:
            #         kwargs[key] = to_stream(to_pull)

        r = fxn(**kwargs)
        if r is None:
            return NOOP
        else:
            return default_prepend(task.execution.output_dir, task.output_dir) + r

    return decorator.decorator(real_decorator)


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
                    can_stream = input_param_name in getattr(fxn, 'can_stream', [])
                    if file_path.startswith('s3://'):
                        local_path = 'tmp-%s__%s' % (random_str(6), os.path.basename(file_path))
                        s3_pull_path = file_path
                    else:
                        local_path = file_path
                        s3_pull_path = opj(s3_path, file_path)

                    if can_stream:
                        return None, s3cmd.stream_in(s3_pull_path)
                        # return 'mkfifo {fifo_path} && {cp} > {fifo_path}'.format(fifo_path=local_path, cp=s3cmd.cp(s3_pull_path, '-')), local_path
                    else:
                        # pull to cwd as a s3_pull_path file (it'll get deleted when $TMP_DIR is deleted)
                        return s3cmd.cp(s3_pull_path, local_path, chrom=task.tags.get('contig')), local_path

                s3_pull_all_inputs = []

                def skip_bai(input_value):
                    # since we are going to be slicing, we do not want the bai
                    return task.tags.get('contig') and input_value.endswith('.bai')

                for input_name, input_value in input_map.items():
                    if isinstance(input_value, list):
                        if skip_bai(input_value[0]): continue
                        cp_cmds, new_input_value_list = zip(*(process_input_value(input_name, iv) for iv in input_value))
                        s3_pull_all_inputs += cp_cmds
                        kwargs[input_name] = new_input_value_list
                    else:
                        if skip_bai(input_value): continue
                        cp_cmd, new_input_value = process_input_value(input_name, input_value)
                        s3_pull_all_inputs.append(cp_cmd)
                        kwargs[input_name] = new_input_value

                fifo_lines, pull_lines = partition(lambda cmd: cmd.startswith('mkfifo'), filter(bool, s3_pull_all_inputs))

                return list(fifo_lines), list(pull_lines)

            fifo_lines, s3_pull_cmds = process_input_map()
            # s3_pull_all_inputs_cmd = "\n".join('/usr/bin/time -f "s3 pull #{0} %E" {1}  2>&1 &'.format(i, l) for i, l in enumerate(s3_push_cmds)) + '\nwait' if len(
            # s3_push_cmds) else ''
            fifo_cmds = "\n".join('%s &' % l for l in fifo_lines)


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
                                local_path = out_val
                                s3_push_path = opj(s3_path, out_val)
                                if output_name in getattr(fxn, 'can_stream', []):
                                    # yield 'mkfifo {fifo_path} && cat {fifo_path} | {cp}'.format(fifo_path=local_path, cp=s3cmd.cp('-', s3_push_path))
                                    kwargs[output_name] = s3cmd.stream_out(opj(s3_path, out_val))
                                    # do not push since we're streaming
                                else:
                                    yield s3cmd.cp(out_val, s3_push_path)

            fifo_lines, s3_push_cmds = partition(lambda cmd: cmd.startswith('mkfifo'), filter(bool, gen_pushes()))
            fifo_lines, s3_push_cmds = list(fifo_lines), list(s3_push_cmds)
            # s3_push_all_outputs = "\n".join('/usr/bin/time -f "s3 push #{0} %E" {1}  2>&1 &'.format(i, l) for i, l in enumerate(cp_lines)) + '\nwait' if len(
            # cp_lines) else ''
            fifo_cmds += "\n".join('%s &' % l for l in fifo_lines) + "\n" if len(fifo_lines) else ''

            r = fxn(**kwargs)
            # print prepend, r, append
            # if 'bwa' in fxn.__name__:
            # raise



            if r == NOOP:
                return NOOP
            else:
                return jinja2.Template("""#!/bin/bash
set -e
set -o pipefail

TMP_DIR=`mktemp -d --tmpdir={{tmp_dir}} {{stage_name}}_XXXXXXXXX`
trap "rm -rf $TMP_DIR" EXIT

echo "Running on host: `hostname`"
echo "Created temp dir: $TMP_DIR"
echo "Mount space before pull: `df -h |grep scratch`"

cd $TMP_DIR
{{make_output_dir}}

{{s3pull}}

echo "S3 Pulled data size:" `du -hs .`
echo "Mount space before after pull: `df -h |grep scratch`"

{{r}}

{{ s3push }}
""").render(tmp_dir=s['gk']['tmp_dir'],
            s3pull=parallel.render(cmds=s3_pull_cmds),
            s3push=parallel.render(cmds=s3_push_cmds),
            stage_name=stage_name,
            fifo_cmds=fifo_cmds,
            r=r,
            s3_pull_cmds=s3_pull_cmds,
            s3_push_cmds=s3_push_cmds,
            make_output_dir='mkdir -p %s\n' % task.output_dir if task.output_dir and task.output_dir != '' else '')

        return decorator.decorator(wrapped)


    return s3_cmd_fxn_wrapper


parallel = jinja2.Template("""
{%- if cmds|length -%}
python - <<EOF
from genomekey.api import Parallel
with Parallel() as p:
{%- for cmd in cmds %}
    p.run('''{{cmd|safe}}''')
{%- endfor %}
EOF
{%- endif -%}""".strip())