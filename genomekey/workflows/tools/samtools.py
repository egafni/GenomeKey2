from cosmos.api import find, out_dir
from genomekey.api import get_env
s = get_env().config


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
            {s[opt][samtools]} merge -f {out_bam} {in_bams}
        """.format(s=s, **locals())

def view(f, in_bam=find('bam$'), out_bam=out_dir('reads.bam')):
    return '{s[opt][samtools]} view -f {f} -h {in_bam} > {out_bam}'.format(s=s,
                                                                           **locals())