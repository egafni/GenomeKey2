from fabric.contrib import files

from fabric.decorators import task
from fabric.operations import local
from fabric.state import env
from fabric.api import run, hide, cd, settings

from genomekey_deploy.util import tobool
from genomekey_deploy.session import VE


__author__ = 'erik'


@task
def install_genomekey(user='genomekey', reinstall=False, dev=True):
    reinstall = tobool(reinstall)
    dev = tobool(dev)
    with settings(user=user), hide('output'):
        files.append('~/.bashrc', ['export SGE_ROOT=/opt/sge6',
                                   'export PATH=$PATH:/opt/sge6/bin/linux-x64:$HOME/bin', ])

        if reinstall:
            run('rm -rf ~/projects/GenomeKey')

        if not files.exists('~/projects/GenomeKey'):
            run('mkdir -p ~/projects')

            # Sync Files
            with cd('~/projects'):
                if dev:
                    # Rsync from local projects
                    local('rsync -avP -e "ssh -o StrictHostKeyChecking=no -i {0}" ~/projects/GenomeKey {1}@{2}:~/projects'.format(
                        env.key_filename, env.user, env.host))
                    local('rsync -avP -e "ssh -o StrictHostKeyChecking=no -i {0}" ~/projects/Cosmos {1}@{2}:~/projects'.format(
                        env.key_filename, env.user, env.host))
                else:
                    # Install from github
                    run('wget https://github.com/LPM-HMS/GenomeKey_v2/archive/master.zip')
                    run('unzip -o master.zip')
                    run('mv GenomeKey_v2-master GenomeKey')
                    run('rm master.zip')

                # Upload our .genomekey.conf if one isnt already on server
                if not files.exists('~/.genomekey.conf'):
                    run('mkdir -p ~/.genomekey')
                    files.upload_template('genomekey.conf',
                                          '~/.genomekey/genomekey.conf', template_dir='~/.genomekey')

            # Create VirtualEnv, and install GenomeKey
            with cd('~/projects/GenomeKey'):
                if not files.exists('ve'):
                    run('pip install virtualenv --user')
                    run('virtualenv ve')
                    with VE():
                        run('pip install pip -I')
                        run('pip install .')
                        run('pip install pygraphviz')

                        run('genomekey initdb')
            if dev:
                # Set VE paths to point to dev code
                with VE():
                    with cd('~/projects/GenomeKey'):
                        run('pip uninstall genomekey -y')
                        run('pwd >> ve/lib/python2.7/site-packages/includes.pth')
                        if not files.exists('~/bin/genomekey'):
                            run('mkdir -p ~/bin')
                            run('ln -s ~/projects/GenomeKey/bin/genomekey ~/bin/genomekey')
                    with cd('~/projects/Cosmos'):
                        run('pip uninstall cosmos-wfm -y')
                        run('pwd >> ~/projects/GenomeKey/ve/lib/python2.7/site-packages/includes.pth')