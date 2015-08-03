import re
import os

from genomekey import settings as s


def cp(from_, to, is_dir=False):
    if is_dir:
        return 'aws s3 cp --quiet %s %s --recursive' % (from_, to)
    else:
        return 'aws s3 cp --quiet %s %s' % (from_, to)


def path_to_s3path(s3_root, taskfile):
    """
    gets the s3 path for a taskfile
    """
    if taskfile.path.startswith('s3://'):
        return taskfile.path
    else:
        return os.path.join(s3_root, taskfile.path)


def stream_in(path, md5=True):
    bucket, key = re.search('s3://(.+?)/(.+)', path).groups()
    md5 = ' ' if md5 else ' --no-md5'
    return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


def get_inputs(s3_root, input_taskfiles):
    """
    Downloads inputs from s3_root into their relative path on the filesystem
    """

    def g():
        for tf in input_taskfiles:
            yield cp(path_to_s3path(s3_root, tf), tf.path, is_dir=tf.format == 'dir')

    return "\n".join(g())


def push_outputs(s3_root, output_taskfiles):
    return "\n".join(cp(tf.path, path_to_s3path(s3_root, tf), is_dir=tf.format == 'dir') for tf in output_taskfiles)


from cosmos import Tool


class S3Tool(Tool):
    skip_s3_pull = False

    def before_cmd(self):
        if getattr(self.task.execution, 'use_s3', False):
            # TODO make sure the region in use has guaranteed consistency
            s3_root = self.task.execution.use_s3
            if not self.skip_s3_pull:
                s3_prepend = get_inputs(s3_root, self.task.input_files)
            else:
                s3_prepend = '# Skipping auto s3 pull because skip_s3_pull == True'

            return '#!/bin/bash\n' \
                   'set -e\n' \
                   'set -o pipefail\n\n' \
                   'TMP_DIR=`mktemp -d --tmpdir={s[gk][tmp_dir]} {self.task.execution.name}_{self.name}_XXXXXXXXX` \n' \
                   'echo "Created temp dir: $TMP_DIR" > /dev/stderr\n' \
                   'cd $TMP_DIR\n' \
                   '{make_output_dir}\n' \
                   '{s3_prepend}\n' \
                   '\n'.format(s=s,
                               make_output_dir='mkdir -p %s\n' % self.task.output_dir if self.task.output_dir != '' else '',
                               **locals())

        else:
            return super(S3Tool, self).before_cmd()

    def after_cmd(self):
        if getattr(self.task.execution, 'use_s3', False):
            bucket = self.task.execution.use_s3
            s3_append = push_outputs(bucket, self.task.output_files)

            return '\n\n' \
                   '{s3_append}\n' \
                   'rm -rf $TMP_DIR'.format(s=s, **locals())
        else:
            return super(S3Tool, self).after_cmd()


def pull_if_s3(taskfiles, local_dir='./'):
    """
    Pull from s3 if the path has s3:// in it
    """

    def check_for_s3(tf):
        if tf.path.startswith('s3://'):
            local_fastq_path = os.path.join(local_dir, os.path.basename(tf.path))
            return local_fastq_path, cp(tf.path, local_fastq_path) + "\n"
        else:
            return tf.path, ''

    local_path, s3_pull_cmds = zip(*[check_for_s3(tf) for tf in taskfiles])
    return local_path, ''.join(s3_pull_cmds).strip()