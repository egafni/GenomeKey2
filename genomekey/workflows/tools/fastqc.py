import os

from cosmos.api import find, out_dir
from genomekey.api import can_stream
from cosmos.util.helpers import random_str
from genomekey.api import get_env
s = get_env().config


# cpu_req is high so nodes don't run out of scratch
@can_stream(['in_r1s', 'in_r2s'])
def fastqc(core_req=8,
           in_r1s=find('fq.gz|\.fastq|fastq.gz', n='>=1', tags=dict(read_pair='1')),
           in_r2s=find('fq.gz|\.fastq|fastq.gz', n='>=1', tags=dict(read_pair='2')),
           out_dir=out_dir('fastqc/')):
    assert len(in_r1s) == len(in_r2s)

    # if len(in_r1s) > 1 or in_r1s[0].startswith('<('):
    #     # If there are more than 1 fastqs per read_pair, merge them into one file per read_pair
    #     # Note, catting compressed files together seems fine
    #     # Have to cat because fastqc does not support streaming
    #     # TODO make sure we are concating to local temp disc if available.  For the usual S3 option this is fine, since we're already in a tmp dir
    #     # TODO stream from s3 into a cat command when input files start with s3://
    #
    #     r1, r2 = 'cat_r1.fastq.gz', 'cat_r2.fastq.gz'
    #     cat = r"""
    #         cat {r1s_join} > {r1}
    #         cat {r2s_join} > {r2}
    #         """.format(s=s,
    #                    r1s_join=' '.join(map(str, in_r1s)),
    #                    r2s_join=' '.join(map(str, in_r2s)),
    #                    **locals())
    #     cleanup = 'rm %s %s' % (r1, r2)
    # else:
    #     r1, r2 = in_r1s[0], in_r2s[0]
    #     cat = ""
    #     cleanup = ""

    cat = 'cat {fqs} | {zcat_or_cat}'.format(fqs=' '.join(in_r1s + in_r2s),
                                             zcat_or_cat='zcat' if '.gz' in in_r1s[0] else 'cat')

    return r"""
            mkdir -p {out_dir}

            {cat} | \
            {s[opt][fastqc]} \
            --threads {core_req} \
            --dir {s[gk][tmp_dir]} \
            -o {out_dir} \
            /dev/stdin

            """.format(s=s, **locals())