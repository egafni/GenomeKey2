.. _install:

Install GenomeKey
======================

.. code-block:: bash

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

    genomekey initdb

