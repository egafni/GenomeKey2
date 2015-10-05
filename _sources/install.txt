.. _install:

Install GenomeKey
======================

**You can skip this if you are using AWS and StarClusterExtensions, as GenomeKey will already be installed on the AMI.**

.. code-block:: bash

    apt-get install awscli # or brew install awscli

    pip install virtualenv --user
    mkdir -p ~/projects
    cd ~/projects
    git clone git@github.com:EnterpriseGenomics/GenomeKey.git GenomeKey
    cd GenomeKey

    virtualenv ve
    source ve/bin/activate

    pip install .

    aws configure # probably want to set default region is us-west-2

    genomekey -h
    # Copy and edit config file as instructed




