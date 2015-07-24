GenomeKey
+++++++++++

`GenomeKey Documentation <http://enterprisegenomics.github.io/GenomeKey/>`_


Testing
++++++++

.. code-block:: bash

    # test data is currently in s3 in genomekey-share

    source ~/projects/GenomeKey/ve/bin/activate
    ~/bin/genomekey -d dna-seq -n "Test" -t tiny_target.bed input_tiny.tsv




Deploying Docs
+++++++++++++++

This will build GenomeKey docs, commit the files to the gh-pages branch, and repository push the changes.

.. code-block:: bash

    source ~/projects/GenomeKey/ve/bin/activate
    # pip install ghp-imports
    cd ~/projects/GenomeKey/docs
    make html
    ghp-import -n -m 'deploy docs' -p _build/html
