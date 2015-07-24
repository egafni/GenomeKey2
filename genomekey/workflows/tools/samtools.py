from cosmos import abstract_input_taskfile as aif, abstract_output_taskfile as aof
from ... import settings as s, GK_Tool


class Merge(GK_Tool):
    def cmd(self, in_bams=aif(format='bam', n='>0'),
            out_bam=aof('{bam_name}.bam')):

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

