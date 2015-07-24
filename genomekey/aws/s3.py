import re
import os

from genomekey import settings as s


def cp(from_, to, is_dir=False):
    if is_dir:
        return 'aws s3 cp %s %s --recursive' % (from_, to)
    else:
        return 'aws s3 cp %s %s' % (from_, to)


def get_s3_path(bucket, taskfile):
    def get_rel_path(taskfile):
        """
        Converts /execution_outs/execution_name/path/to/file to
        execution_name/path/to/file
        """
        assert taskfile.path[0] != '/', 'not sure how to push/pull this from s3'
        return taskfile.path

    if taskfile.path.startswith('s3://'):
        return taskfile
    else:
        return os.path.join(bucket, get_rel_path(taskfile))


def stream_in(path, md5=True):
    bucket, key = re.search('s3://(.+?)/(.+)', path).groups()
    md5 = ' ' if md5 else ' --no-md5'
    return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


def get_inputs(bucket, input_taskfiles):
    """
    Downloads inputs from bucket into their relative path on the filesystem
    """

    def g():
        for tf in input_taskfiles:
            yield cp(get_s3_path(bucket, tf), tf.path, is_dir=tf.format == 'dir')

    return "\n".join(g())


def push_outputs(bucket, output_taskfiles):
    return "\n".join(cp(tf.path, get_s3_path(bucket, tf), is_dir=tf.format == 'dir') for tf in output_taskfiles)


from cosmos import Tool


class S3Tool(Tool):
    skip_s3_pull = False

    def before_cmd(self):
        if getattr(self.task.execution, 'use_s3', False):
            # TODO make sure the region in use has guaranteed consistency
            bucket = self.task.execution.use_s3
            if not self.skip_s3_pull:
                s3_prepend = get_inputs(bucket, self.task.input_files)
            else:
                s3_prepend = '# Skipping s3 pull because skip_s3_pull == True'

            return 'TMP_DIR=`mktemp -d --tmpdir={s[gk][tmp_dir]} {self.task.execution.name}_{self.name}_XXXXXXXXX` \n' \
                   'echo "Created temp dir: $TMP_DIR" > /dev/stderr\n' \
                   'cd $TMP_DIR\n' \
                   'mkdir -p {self.task.output_dir}\n' \
                   '{s3_prepend}\n' \
                   '\n'.format(s=s, **locals())

        else:
            return super(S3Tool, self).before_cmd(self)

    def after_cmd(self):
        if getattr(self.task.execution, 'use_s3', False):
            bucket = self.task.execution.use_s3
            s3_append = push_outputs(bucket, self.task.output_files)

            return '\n\n' \
                   '{s3_append}\n' \
                   'rm -rf $TMP_DIR'.format(s=s, **locals())
        else:
            return super(S3Tool, self).after_cmd(self)
