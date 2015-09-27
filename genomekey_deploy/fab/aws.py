from fabric.contrib import files
from fabric.api import cd, task, run, sudo, settings, hide, shell_env
import glob
from genomekey_deploy.util import apt_update

__author__ = 'erik'
GENOME_KEY_USER = 'genomekey'

def apt_get_install(packages):
    return run('apt-get -q -y install %s' % packages)

@task
def init_node():
    with hide('output'), settings(user='root'):
        # note can make an AMI to avoid doing this
        # TODO get rid of this pastebin.  The StarCluster AMI has whack apt sources.
        run('wget "http://pastebin.com/raw.php?i=uzhrtg5M" -O /etc/apt/sources.list')
        apt_update(force=True)

        if not ('Java(TM) SE Runtime Environment' in run('java -version')):
            run('add-apt-repository ppa:webupd8team/java -y')
            # apt_update(force=True)

            # debconf so java install doesn't prompt for license confirmation
            run('echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections')
            apt_get_install('oracle-java7-installer oracle-java7-set-default')

        apt_get_install('libcurl4-openssl-dev')

        run('chown -R genomekey:genomekey /genomekey')  # TODO fix the perms in the ami

        setup_scratch_space()

        with settings(user=GENOME_KEY_USER):
            setup_aws_cli(True)
            sync_genomekey_share()


@task
def init_master():
    with hide('output'), settings(user='root'):
        # update apt-list, starcluster AMI is out_dir-of-date
        apt_get_install('graphviz graphviz-dev mbuffer')
        run('pip install awscli')

        # For ipython notebook.  Do this last user can get started.  Installing pandas is slow.
        run('pip install "ipython[notebook]" -U')

        with settings(user=GENOME_KEY_USER):
            run('mkdir -p /home/genomekey/analysis')

            files.append('~/.bashrc', ['export SGE_ROOT=/opt/sge6',
                                       'export PATH=$PATH:/opt/sge6/bin/linux-x64:$HOME/bin'])


def sync_genomekey_share():
    """
    Requires that setup_aws_cli() has already been called
    """
    # with settings(user='root'):
    # TODO change the AMI and delete this?  This runs instantly so not a big deal
    # run('chown -R genomekey:genomekey /genomekey')
    print 'sync genomekey share'
    with hide('output'):
        run('aws s3 sync s3://genomekey-data /genomekey/share')
        chmod_opt('/genomekey/share/opt')


def chmod_opt(opt_path):
    with cd(opt_path):
        # TODO use settings to decide what to chmod?
        bins = ['bwa/*/bwa',
                'samtools/*/samtools',
                'gof3r/*/gof3r',
                'fastqc/*/fastqc',
                'cutadapt/*/bin/cutadapt',
                'bin/run']

        for b in bins:
            # aws s3 cli doesn't preserve file perms :(
            run('chmod +x %s' % b)


def setup_aws_cli(overwrite=False):
    if overwrite or not files.exists('~/.aws/config'):
        run('mkdir -p ~/.aws')

        # push aws config files
        files.upload_template('config', '~/.aws/config', use_jinja=False, template_dir='~/.aws')
        files.upload_template('credentials', '~/.aws/credentials', use_jinja=False, template_dir='~/.aws')


        # @taska
        # def mount_genomekey_share(mount_path='/mnt/genomekey/share_yas3fs'):
        # with aws_credentials(), settings(user='root'):
        # run('pip install yas3fs')
        # if mount_path not in run('cat /proc/mounts', quiet=True):
        # run('mkdir -p %s' % mount_path)
        #             run('yas3fs --region us-west-2 --cache-path /mnt/genomekey/tmp/genomekey-data '
        #                 's3://genomekey-data %s' % mount_path)
        #
        #             chmod_opt(os.path.join(mount_path, 'opt'))
        #             # '--topic arn:aws:sns:us-west-2:502193849168:genomekey-data --new-queue --mkdir')

@task
def setup_scratch_space():
    """
    Setup RAID0 with all available ephemeral discs
    """
    with settings(user='root'):
        def is_mounted(path):
            return run('df |grep %s' % path, quiet=True).return_code == 0

        print 'Setting up raid 0 for scratch space'

        if not is_mounted('df |grep /scratch'):
            apt_get_install("mdadm --no-install-recommends")
            ephemeral_devices = run('ls /dev/xvd*').split() # TODO i'm not sure this logic to find ephemeral_devices applies to non c3.4xlarge...
            print 'ephemeral devices: %s' % ephemeral_devices
            if is_mounted('/mnt'):
                run('umount /mnt')

            run('mkdir -p /scratch')
            run('mdadm --create -R --verbose /dev/md0 --level=0 --name=SCRATCH --raid-devices=%s %s' % (len(ephemeral_devices), ' '.join(ephemeral_devices)))
            run('sudo mkfs.ext4 -L SCRATCH /dev/md0')
            run('mount LABEL=SCRATCH /scratch')
            run('chown -R genomekey:genomekey /scratch')
        else:
            print '/scratch already mounted, not doing anything'



