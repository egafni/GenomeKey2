from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
from fabric.api import execute, env

from ..fab.aws import init_node, init_master
from ..fab.gk import copy_genomekey_dev_environ
from genomekey_deploy.util import tobool


def run_fab(func, hosts, *args, **kwargs):
    """
    :param hosts: starcluster Nodes
    """
    if not isinstance(hosts, list):
        hosts = [hosts]

    env.key_filename = [hosts[0].key_location]  # Assume all hosts use the same key...
    env.abort_on_promts=True
    kwargs['hosts'] = [h.ip_address for h in hosts]
    log.info('Run fab task: %s, key_filename=%s, args: %s, kwargs: %s' % (func.__name__, env.key_filename, args, kwargs))
    execute(func, *args, **kwargs)


class GenomeKeySetup(ClusterSetup):
    """
    Interface for StarCluster to use the genomekey_deploy fab files.  There should be very minimal logic here.
    """

    def __init__(self, install_dev_environ=True,  **kwargs):
        self.install_dev_environ = tobool(install_dev_environ)
        super(ClusterSetup, self).__init__(**kwargs)


    def run(self, nodes, master, user, user_shell, volumes):
        for node in nodes:
            # fab -f init_node -H $hosts
            run_fab(init_node, hosts=node)

        run_fab(init_master, hosts=master)

        if self.install_dev_environ:
            run_fab(copy_genomekey_dev_environ, hosts=master)

        # Print out_dir IP address for the user
        cluster_name = master.parent_cluster.name[4:]
        etc_hosts_line = "{0}\t{1}".format(master.ip_address, cluster_name)
        log.info('Consider adding to /etc/hosts: %s' % etc_hosts_line)


    def on_add_node(self, node, nodes, master, user, user_shell, volumes):
        run_fab(init_node, hosts=node)

    def on_shutdown(self, nodes, master, user, user_shell, volumes):
        pass

    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        pass

    def on_restart(self, nodes, master, user, user_shell, volumes):
        pass