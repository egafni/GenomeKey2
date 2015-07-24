from fabric.context_managers import settings, shell_env
from fabric.operations import run

__author__ = 'erik'


def install_ganglia():
    with settings(user='root'), shell_env(DEBIAN_FRONTEND='noninteractive'):
        # run('apt-get install ganglia-*') # need to auto answer yes for this with dbconf
        run('cp /etc/ganglia-webfrontend/apache.conf /etc/apache2/sites-enabled/ganglia.conf')
        run('/etc/init.d/gmetad start')
        run('/etc/init.d/ganglia-monitor start')
        run('/etc/init.d/apache2 restart')