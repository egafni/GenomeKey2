import re
import os
import decorator
from genomekey import settings as s


def cp(from_, to):
    # if is_dir:
    return 'aws s3 cp --quiet %s %s --recursive' % (from_, to)
    # else:
    #     return 'aws s3 cp --quiet %s %s' % (from_, to)


def path_to_s3path(s3_root, file_path):
    """
    gets the s3 path for a file_path
    """
    if file_path.startswith('s3://'):
        return file_path
    else:
        return os.path.join(s3_root, file_path)


def stream_in(path, md5=True):
    bucket, key = re.search('s3://(.+?)/(.+)', path).groups()
    md5 = ' ' if md5 else ' --no-md5'
    return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


def get_inputs(s3_root, input_file_paths):
    """
    Downloads inputs from s3_root into their relative path on the filesystem
    """

    def g():
        for tf in input_file_paths:
            yield cp(path_to_s3path(s3_root, tf), tf)

    return "\n".join(g())


def push_outputs(s3_root, output_file_paths):
    return "\n".join(cp(tf, path_to_s3path(s3_root, tf)) for tf in output_file_paths)


def s3_cmd_fxn_wrapper(bucket):
    def _s3(fxn, **kwargs):
        input_files = {k: v for k, v in kwargs.items() if k.startswith('in_')}
        output_files = {k: v for k, v in kwargs.items() if k.startswith('out_')}

        if fxn.s3_stream:
            s3_prepend = '# Skipping auto s3 pull because s3_stream == True'
        else:
            s3_prepend = get_inputs(bucket, input_files)

        prepend = '#!/bin/bash\n' \
                  'set -e\n' \
                  'set -o pipefail\n\n' \
                  'TMP_DIR=`mktemp -d --tmpdir={s[gk][tmp_dir]} {self.task.execution.name}_{self.name}_XXXXXXXXX` \n' \
                  'echo "Created temp dir: $TMP_DIR" > /dev/stderr\n' \
                  'cd $TMP_DIR\n' \
                  '{make_output_dir}\n' \
                  '{s3_prepend}\n' \
                  '\n'.format(s=s,
                              make_output_dir='mkdir -p %s\n' % kwargs['out_dir'] if kwargs['out_dir'] != '' else '',
                              **locals())

        s3_append = push_outputs(bucket, output_files)
        append = '\n\n' \
                 '{s3_append}\n' \
                 'rm -rf $TMP_DIR'.format(s=s, **locals())

        return prepend + fxn(**kwargs) + append

    return decorator.decorator(_s3)


def pull_if_s3(file_paths, local_dir='./'):
    """
    Pull from s3 if the path has s3:// in it
    """

    def check_for_s3(tf):
        if tf.path.startswith('s3://'):
            local_fastq_path = os.path.join(local_dir, os.path.basename(tf.path))
            return local_fastq_path, cp(tf.path, local_fastq_path) + "\n"
        else:
            return tf.path, ''

    local_path, s3_pull_cmds = zip(*[check_for_s3(tf) for tf in file_paths])
    return local_path, ''.join(s3_pull_cmds).strip()