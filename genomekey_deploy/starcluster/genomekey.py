from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
from fabric.api import execute, env

from ..fab.aws import init_node, init_master
from ..fab.genomekey import install_genomekey


def run_fab(func, hosts, *args, **kwargs):
    """
    :param hosts: list of starcluster nodes
    """
    if not isinstance(hosts, list):
        hosts = [hosts]

    env.key_filename = hosts[0].key_location  # Assume all hosts use the same key...
    log.info('Run fab task: %s, args: %s, kwargs: %s' % (func, args, kwargs))
    execute(func, hosts=[h.ip_address for h in hosts], *args, **kwargs)


class GenomeKeySetup(ClusterSetup):
    def run(self, nodes, master, user, user_shell, volumes):
        run_fab(init_master, hosts=master)
        run_fab(install_genomekey, hosts=master)

        cluster_name = master.parent_cluster.name[4:]
        etc_hosts_line = "{0}\t{1}".format(master, cluster_name)
        log.info('Consider adding to /etc/hosts: %s' % etc_hosts_line)

    def on_add_node(self, node, nodes, master, user, user_shell, volumes):
        run_fab(init_node, hosts=node)

    def on_shutdown(self, nodes, master, user, user_shell, volumes):
        pass

    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        pass

    def on_restart(self, nodes, master, user, user_shell, volumes):
        pass