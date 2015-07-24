
Amazon Web Services
=======================


Install StarCluster
+++++++++++++++++++

.. code-block:: bash
    export GK_HOME=/home/egafni/projects/GenomeKey_LPM

    pip install starcluster

    alias sc="starcluster -r us-west-1" # optionally place in your bashrc

    starcluster help # select option to create default config in ~/.starcluster

    cp $GK_HOME/genomekey/aws/starcluster/config ~/.starcluster/config

1) edit aws file with AWS credentials
2) Make/place aws private key in ~/.starcluster/key_name.rsa
3) make sure KEYNAME in ~/.starcluster/config is set to your keyname


Launch Cluster
+++++++++++++++++++

.. code-block:: bash

    sc mycluster

Configure Master
++++++++++++++++++

.. todo::

    Automate this as a starcluster extension

.. code-block:: bash

    # sc listclusters to get the list of clusters

    fab -f deploy_aws.py init_master -H $CLUSTER_HOST -i $CLUSTER_KEY
    fab -f deploy_aws.py init_genomekey -H $CLUSTER_HOST -i $CLUSTER_KEY



