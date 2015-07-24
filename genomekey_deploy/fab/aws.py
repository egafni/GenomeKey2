import os

from fabric.context_managers import settings, hide
from fabric.contrib import files
from fabric.operations import run
from fabric.api import cd, task

from .genomekey import install_genomekey
from ..util import apt_update
from ..session import deploy_etc, AWS_ENV, aws_credentials


__author__ = 'erik'


@task
def init_node():
    # note can make an AMI to avoid doing this
    # TODO get rid of this pastebin
    run('wget "http://pastebin.com/raw.php?i=uzhrtg5M" -O /etc/apt/sources.list')

    run('sudo add-apt-repository ppa:webupd8team/java -y')
    apt_update(force=True)

    # debconf so java install doesn't prompt for license confirmation
    run('echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
    run('sudo apt-get install oracle-java7-installer oracle-java7-set-default -y')

    run('mkdir -p /mnt/genomekey/analysis')
    run('mkdir -p /mnt/genomekey/tmp')
    run('chown genomekey:genomekey /mnt/genomekey/tmp')
    run('chown genomekey:genomekey /mnt/genomekey/analysis')


@task
def init_master():
    with hide('output'):
        init_node()

        # update apt-list, starcluster AMI is out-of-date
        run('apt-get install graphviz graphviz-dev mbuffer -y')
        run('pip install awscli')
        run('mkdir -p /mnt/genomekey')
        run('mkdir -p /mnt/genomekey/tmp')

        with settings(user='genomekey'):
            setup_aws_cli()
            install_genomekey()
            mount_genomekey_share()
            sync_genomekey_share()

            # For ipython notebook.  Do this last user can get started.  Installing pandas is slow.
            run('pip install "ipython>3" "tornado>4" pyzmq jsonschema pandas -U')


def mount_genomekey_share(user='root', mount_path='/mnt/genomekey/share_yas3fs'):
    with aws_credentials(), settings(user=user):
        if not files.exists(mount_path):
            run('mkdir -p %s' % mount_path)
            run('pip install yas3fs --user')
            run('yas3fs --region us-west-2 --cache-path /mnt/genomekey/tmp/genomekey-data '
                's3://genomekey-data %s' % mount_path)
            chmod_opt(os.path.join(mount_path, '/opt'))
            # '--topic arn:aws:sns:us-west-2:502193849168:genomekey-data --new-queue --mkdir')


def sync_genomekey_share(user='genomekey'):
    with settings(user=user):
        with hide('output'):
            setup_aws_cli()
            run('mkdir -p /mnt/genomekey/share')
            run('aws s3 sync s3://genomekey-data/* /mnt/genomekey/share/')
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


def setup_aws_cli(user='genomekey', overwrite=False):
    with settings(user=user):
        if overwrite or not files.exists('~/.aws/config'):
            run('mkdir -p ~/.aws')
            d = deploy_etc('aws')
            files.upload_template('config', '~/.aws/config',
                                  AWS_ENV,
                                  use_jinja=True, template_dir=d)
            files.upload_template('credentials', '~/.aws/credentials',
                                  AWS_ENV,
                                  use_jinja=True, template_dir=d)
