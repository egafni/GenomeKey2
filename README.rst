Create Data Dir
================

Download GATK Bundle and various bioinformatics tools

export DATA_DIR=/mnt/data

Bundle
+++++++++

.. code-block:: bash

    mkdir -p $DATA_DIR/bundle/2.8/b37
    cd $DATA_DIR/bundle/2.8/b37
    wget ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/2.8/b37/* -R "*CEU*,*NA12878*,*done*"


Testing
++++

.. code-block:: bash


    source ~/projects/GenomeKey/ve/bin/activate
    ~/bin/genomekey -d dna-seq -n "Test" -t tiny_target.bed input_tiny.tsv