Amazon Web Services
=======================


Install StarCluster
+++++++++++++++++++

1) Create an aws private key (using starcluster or aws console) at save it somewhere like ~/.starcluster/your_key.rsa
2) Install starcluster into a local genomekey installation (so that it has access to the genomekey_deploy package)

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate

    pip install starcluster StarClusterExtensions

    starcluster help # select option to create default config in ~/.starcluster

    # This is the default genomekey starcluster configuration
    # Changing anything besides private key locations and AWS credentials is not recommended (unless you're an advanced user)
    cp $GK_HOME/genomekey/aws/starcluster/config ~/.starcluster/config
    # Edit ~/.starcluster/config and follow the instructions


    # install the aws cli, and configure it as well (you have to store your AWS credentials in two places)
    # this configuration file will be pushed to the starcluster clusters so that genomekey can use aws
    # TODO just infer awscli config from starcluster config
    brew install awscli # or sudo apt-get install awscli
    aws configure


Launch Cluster
+++++++++++++++++++

This will launch a single master node (reserved instance), and one execution node (spot instance)

.. code-block:: bash

    starcluster start gk -s 2

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



(Advanced) Creating a custom AMI
++++++++++++++++++++++++++++++++++

A custom StarCluster AMI was created to speed up deployment.

  * apt-update
  * Install oracle Java
  * Increase EBS root volume size (Must be done by first using "starcluster ebsimage", then in console, create a second image and specify root ebs size).
  * Download GATK bundle to root ebs drive
  * Create the final ebs image ("starcluster ebsimage")
