


Build Docs
+++++++++++

.. todo:: Host this somewhere...

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    make html
    open _build/html/index.html



Testing
++++++++

.. code-block:: bash

    # test data is currently in s3 in genomekey-share

    source ~/projects/GenomeKey/ve/bin/activate
    ~/bin/genomekey -d dna-seq -n "Test" -t tiny_target.bed input_tiny.tsv