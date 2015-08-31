from cosmos import find, out_dir
from ... import settings as s


def merge(in_bams=find('bam$', n='>0'),
        out_bam=out_dir('merged.bam')):
    if len(in_bams) == 1:
        # Can't merge 1 bam, just copy it
        return r"""
        cp {in_bams[0]} {out_bam}
        """.format(**locals())
    else:
        in_bams = ' '.join(map(str, in_bams))
        return r"""
            {s[opt][samtools]} merge {out_bam} {in_bams}
        """.format(s=s, **locals())

