import os

from cosmos.api import find, out_dir
from ... import settings as s
from genomekey.aws import s3
from cosmos.util.helpers import random_str

#skip_s3_pull
def fastqc(cpu_req=2,
           in_r1s=find('fastq', n='>=1', tags=dict(read_pair='1')),
           in_r2s=find('fastq', n='>=1', tags=dict(read_pair='2')),
           out_dir=out_dir('fastqc/')):

    assert len(in_r1s) == len(in_r2s)

    if len(in_r1s) > 1:
        # If there are more than 1 fastqs per read_pair, merge them into one file per read_pair
        # Note, catting compressed files together seems fine
        # Have to cat because fastqc does not support streaming
        # Todo make sure we are concating to local temp disc if available.  For the usual S3 option this is fine.
        r1, r2 = os.path.join('cat_r1.fastq.gz'), os.path.join('cat_r2.fastq.gz')
        cat = r"""
            cat {r1s_join} > {r1}
            cat {r2s_join} > {r2}
            """.format(s=s,
                       r1s_join=' '.join(map(str, in_r1s)),
                       r2s_join=' '.join(map(str, in_r2s)),
                       **locals())
        cleanup = 'rm %s %s' % (r1, r2)
    else:
        r1, r2 = in_r1s[0], in_r2s[0]
        cat = ""
        cleanup = ""

    return r"""
            {cat}

            mkdir -p {out_dir}
            {s[opt][fastqc]} \
            --threads {cpu_req} \
            --dir {s[gk][tmp_dir]} \
            -o {out_dir} \
            {r1} {r2}

            {cleanup}
            """.format(s=s, **locals())