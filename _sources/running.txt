.. _running:

Running GenomeKey
==================

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    genomekey germline -i input_files.tsv -t target.bed -n 'Workflow_Name'


input_files.tsv should have the following format.  If the path points to a file on s3, it will be automatically
pulled down by the alignment tasks.

.. code-block:: bash

    sample_name     read_pair       chunk   library platform_unit   platform        rgid    path
    John_Smith      1       1       LB      PU      ILLUMINA        RG1     s3://genomekey-data/test/brca/brca.example.illumina.0.1.fastq.gz
    John_Smith      2       1       LB      PU      ILLUMINA        RG1     s3://genomekey-data/test/brca/brca.example.illumina.0.2.fastq.gz


Test Workflows
+++++++++++++++

Here are some example datasets to test.

.. code-block:: bash

    # A single gene
    genomekey -d germline -n 'Test_BRCAo' /genomekey/share/test/brca/input_s3.tsv --target_bed /genomekey/share/test/brca/targets.bed

    # A gene panel
    cd /mnt/genomekey/share/test/1000g
    genomekey germline -n 'Test_Exon' /genomekey/share/test/1000g/exons.tsv  -t /genomekey/share/test/1000g/P3_consensus_exonic_targets.bed

    # Two Exomes



Web Dashboard
+++++++++++++++

.. code-block:: bash

    # Development flask server (not secure)
    genomekey runweb -H 0.0.0.0

    # More robust gunicorn web server
    gunicorn genomekey.web.gunicorn:flask -b 0.0.0.0:5000