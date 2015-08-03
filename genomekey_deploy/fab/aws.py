from fabric.context_managers import settings, hide
from fabric.contrib import files
from fabric.operations import run
from fabric.api import cd, task

from genomekey_deploy.fab.gk import install_genomekey
from genomekey_deploy.util import apt_update

# from genomekey_deploy.session import aws_credentials
#

__author__ = 'erik'


@task
def init_node():
    with hide('output'):
        # note can make an AMI to avoid doing this
        # TODO get rid of this pastebin
        run('wget "http://pastebin.com/raw.php?i=uzhrtg5M" -O /etc/apt/sources.list')

        if not ('Java(TM) SE Runtime Environment' in run('java -version')):
            run('add-apt-repository ppa:webupd8team/java -y')
            apt_update(force=True)

            # debconf so java install doesn't prompt for license confirmation
            run(
                'echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
            run('apt-get install oracle-java7-installer oracle-java7-set-default -y')

        run('mkdir -p /mnt/genomekey/scratch')
        run('chown genomekey:genomekey /mnt/genomekey/scratch')

        # if not files.exists('/scratch'):
        # run('mkdir -p /mnt/genomekey/scratch')
        #     run('ln -s /mnt/genomekey/scratch /scratch')
        #     run('chown genomekey:genomekey /mnt/genomekey/scratch')

        with settings(user='genomekey'):
            setup_aws_cli()
            # mount_genomekey_share()
            # if sync_genomekey_share:
            sync_genomekey_share()


@task
def init_master():
    with hide('output'):
        # update apt-list, starcluster AMI is out-of-date
        run('apt-get install graphviz graphviz-dev mbuffer -y')
        run('pip install awscli')

        with settings(user='genomekey'):
            run('mkdir -p /home/genomekey/analysis')

        install_genomekey()

        # For ipython notebook.  Do this last user can get started.  Installing pandas is slow.
        run('pip install "ipython[notebook]" -I')


# @task
# def mount_genomekey_share(mount_path='/mnt/genomekey/share_yas3fs'):
# with aws_credentials(), settings(user='root'):
#         run('pip install yas3fs')
#         if mount_path not in run('cat /proc/mounts', quiet=True):
#             run('mkdir -p %s' % mount_path)
#             run('yas3fs --region us-west-2 --cache-path /mnt/genomekey/tmp/genomekey-data '
#                 's3://genomekey-data %s' % mount_path)
#
#             chmod_opt(os.path.join(mount_path, 'opt'))
#             # '--topic arn:aws:sns:us-west-2:502193849168:genomekey-data --new-queue --mkdir')

@task
def sync_genomekey_share(user='genomekey'):
    with settings(user=user):
        with hide('output'):
            setup_aws_cli()
            run('mkdir -p /mnt/genomekey/share')
            run('aws s3 sync s3://genomekey-data /mnt/genomekey/share')
            chmod_opt('/mnt/genomekey/share/opt')


def chmod_opt(opt_path):
    with cd(opt_path):
        # TODO use settings to decide what to chmod?
        bins = ['bwa/*/bwa',
                'samtools/*/samtools',
                'gof3r/*/gof3r',
                'fastqc/*/fastqc']

        for b in bins:
            # aws s3 cli doesn't preserve file perms :(
            run('chmod +x %s' % b)


@task
def setup_aws_cli(user='genomekey', overwrite=False):
    with settings(user=user):
        if overwrite or not files.exists('~/.aws/config'):
            run('mkdir -p ~/.aws')

            # push aws config files
            files.upload_template('config', '~/.aws/config', use_jinja=False, template_dir='~/.aws')

            files.upload_template('credentials', '~/.aws/credentials', use_jinja=False, template_dir='~/.aws')
