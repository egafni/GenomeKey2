Amazon Web Services
=======================


Install StarCluster and StarClusterExtensions
++++++++++++++++++++++++++++++++++++++++++++++

1) Create an aws private key (using starcluster or aws console) at save it somewhere like ~/.starcluster/your_key.rsa
2) Install starcluster, starclusterextensions ande awscli
3) Configure starcluster and awscli
3) Launch the cluster!

.. code-block:: bash

    # Clone repos
    cd ~/GenomeKeyDeploy/$VERSION
    git clone -b master https://github.com/egafni/StarClusterExtensions.git
    git clone -b genomekey https://github.com/egafni/StarCluster.git
    git clone -b master https://github.com/LPM-HMS/COSMOS-2.0.git Cosmos
    git clone -b master https://github.com/LPM-HMS/GenomeKey2.git GenomeKey

    # Create a virtual environment for StarCluster and StarClusterExtensions
    virtualenv ve
    source ve/bin/activate

    pip install StarCluster/ StarClusterExtensions/

    mkdir etc/
    cp StarClusterExtensions/etc/config etc/starcluster.config
    # Edit etc/starcluster.config and fill out necessary fields



    # install the aws cli, and configure it as well (you have to store your AWS credentials in two places)
    # this configuration file will be pushed to the starcluster clusters so that genomekey can use aws
    # TODO just infer awscli config from starcluster config
    brew install awscli # or sudo apt-get install awscli
    aws configure


Launch Cluster
+++++++++++++++++++

This will launch a single master node (reserved instance), and one execution node (spot instance).  **you must be in the GenomeKeyDeploy/$VERSION directory**

.. code-block:: bash

    cd ~/GenomeKeyDeploy/$VERSION
    source ve/bin/activate
    starcluster -c etc/starcluster.config start gk

Adding nodes (StarCluster has been configured to request spot instances by default)

.. code-block:: bash

    starcluster addnode gk

Alternatively, use the elastic load balancer (not well tested)

.. code-block:: bash

    starcluster loadbalance -min_nodes 1 -max_nodes 4 -d -p gk


See the `StarCluster Docs <http://star.mit.edu/cluster/docs/latest/manual/>`_ for more information


Run GenomeKey
+++++++++++++++

.. code-block:: bash

    ssh -i /path/to/genomekey_key.rsa genomekey@$STARCLUSTER_HOST
    # tmux is highly recommended here

    cd projects/GenomeKey
    source ve/bin/activate
    genomekey -h



(Advanced) Manually using Fabric Deploy Script
++++++++++++++++++++++++++++++++++++++++++++++++

Normally these deployment scripts are executed by the StarCluster GenomeKey plugin automatically, and this isn't necessary.
Advanced users will want to look through the genomekey_deploy/fab scripts to see the code behind the deployment
steps.

.. code-block:: bash

    # starcluster listclusters to get the list of clusters
    cd StarClusterExtensions/sce/plugins/genomekey/fab
    fab -f aws.py command -H $CLUSTER_HOST -i $CLUSTER_KEY
    # example:
    cd ~/projects/StarClusterExtensions/sce/plugins/genomekey/fab
    fab -f gk.py copy_genomekey_dev_environ -H gk -i ~/.starcluster/ngx_keys/genomekey_key.rsa


(Advanced) Creating a custom AMI
++++++++++++++++++++++++++++++++++

A custom StarCluster AMI was created to speed up deployment.

  * apt-update
  * Install oracle Java
  * Increase EBS root volume size (Must be done by first using "starcluster ebsimage", then in console, create a second image and specify root ebs size).
  * Download GATK bundle to root ebs drive
  * Create the final ebs image ("starcluster ebsimage")
