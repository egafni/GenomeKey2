Amazon Web Services
=======================


Install StarCluster
+++++++++++++++++++

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    export GK_HOME=/home/egafni/projects/GenomeKey

    pip install starcluster StarClusterExtensions

    starcluster help # select option to create default config in ~/.starcluster

    # This is the default genomekey starcluster configuration
    # Changing anything besides private key locations and AWS credentials is not recommended (unless you're an advanced user)
    cp $GK_HOME/genomekey/aws/starcluster/config ~/.starcluster/config
    cp $GK_HOME/genomekey/aws/starcluster/aws_credentials ~/.starcluster/aws_credentials
    # Be sure to edit ~/.starcluster/aws_credentials


1) edit aws file with AWS credentials
2) Make/place aws private key (using starcluster or aws console) in ~/.starcluster/your_key.rsa
3) make sure KEYNAME in ~/.starcluster/config is set to your keyname


Launch Cluster
+++++++++++++++++++

This will launch a single master node.

.. code-block:: bash

    starcluster start gk

Adding nodes (StarCluster has been configured to request spot instances by default)

.. code-block:: bash

    starcluster addnode gk

Alternatively, use the elastic load balancer (not well tested)

.. code-block:: bash

    starcluster loadbalance -min_nodes 1 -max_nodes 4 -d -p gk


See the `StarCluster Docs <http://star.mit.edu/cluster/docs/latest/manual/>`_ for more information




(Advanced) Manually using Fabric Deploy Script
++++++++++++++++++++++++++++++++++++++++++++++++

Normally these deployment scripts are executed by the StarCluster GenomeKey plugin automatically, and this isn't necessary.
Advanced users will want to look through the genomekey_deploy/fab scripts to see the code behind the deployment
steps.

.. code-block:: bash

    # starcluster listclusters to get the list of clusters
    cd genomekey_deploy/fab
    fab -f aws.py command -H $CLUSTER_HOST -i $CLUSTER_KEY



