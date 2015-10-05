import subprocess
import subprocess as sp
import sys


def run(cmd):
    return sp.check_output(cmd, shell=True)


def delete_s3_dir(s3_path, skip_confirm=False):
    from cosmos.util.helpers import confirm

    if not skip_confirm:
        confirm("Are you sure you want to delete %s?" % s3_path)
    cmd = 'aws s3 rm %s --recursive --only-show-errors' % s3_path
    print >> sys.stderr, cmd
    run(cmd)


def path_exists(path):
    return sp.Popen('aws s3 ls %s' % path, shell=True, stdout=sp.PIPE).wait() == 0


def get_filesize(s3_path):
    return run('aws s3 ls %s' % s3_path).split()[2]
