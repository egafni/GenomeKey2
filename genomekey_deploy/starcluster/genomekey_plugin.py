from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
from fabric.api import execute, env

from ..fab.aws import init_node, init_master


def run_fab(func, hosts, *args, **kwargs):
    """
    :param hosts: starcluster Nodes
    """
    if not isinstance(hosts, list):
        hosts = [hosts]

    env.key_filename = hosts[0].key_location  # Assume all hosts use the same key...
    log.info('Run fab task: %s, args: %s, kwargs: %s' % (func.__name__, args, kwargs))
    execute(func, hosts=[h.ip_address for h in hosts], *args, **kwargs)


class GenomeKeySetup(ClusterSetup):
    """
    Interface for StarCluster to use the genomekey_deploy fab files.  There should be very minimal logic here.
    """
    def run(self, nodes, master, user, user_shell, volumes):
        for node in nodes:
            run_fab(init_node, hosts=node)

        run_fab(init_master, hosts=master)

        # Print out IP address for the user
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