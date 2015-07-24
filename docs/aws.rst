Amazon Web Services
=======================


Install StarCluster
+++++++++++++++++++

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    export GK_HOME=/home/egafni/projects/GenomeKey

    pip install starcluster

    starcluster help # select option to create default config in ~/.starcluster

    cp $GK_HOME/genomekey/aws/starcluster/config ~/.starcluster/config

1) edit aws file with AWS credentials
2) Make/place aws private key (using starcluster or aws console) in ~/.starcluster/key_name.rsa
3) make sure KEYNAME in ~/.starcluster/config is set to your keyname


Launch Cluster
+++++++++++++++++++

.. code-block:: bash

    starcluster start mycluster


(Advanced) Manually using Fabric Deploy Script
++++++++++++++++++++++++++++++++++++++++++++++++

Normally these deployment scripts are executed by StarCluster automatically, and this isn't necessary.

.. code-block:: bash

    # sc listclusters to get the list of clusters
    cd genomekey_deploy/fab
    fab -f aws.py command -H $CLUSTER_HOST -i $CLUSTER_KEY



