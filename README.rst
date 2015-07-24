GenomeKey
+++++++++++

`GenomeKey Documentation <http://enterprisegenomics.github.io/GenomeKey/>`_


Build Docs
+++++++++++

.. todo:: Host this somewhere...

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    # pip install ghp-imports
    cd ~/projects/GenomeKey/docs
    make html
    ghp-import -n -m 'ghp' -p docs/_build/html



Testing
++++++++

.. code-block:: bash

    # test data is currently in s3 in genomekey-share

    source ~/projects/GenomeKey/ve/bin/activate
    ~/bin/genomekey -d dna-seq -n "Test" -t tiny_target.bed input_tiny.tsv