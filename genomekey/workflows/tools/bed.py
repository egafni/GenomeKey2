from cosmos import abstract_input_taskfile as aif, abstract_output_taskfile as aof
from genomekey import settings as s

from ... import GK_Tool


class Split_Bed_By_Contig(GK_Tool):
    drm = 'local'
    skip_s3_pull = True

    def cmd(self,
            contig,
            in_bed=aif(format='bed'),
            out_bed=aof('target.bed')):
        return r"""
            grep -P "^{contig}\t" {in_bed} > {out_bed}
        """.format(s=s, **locals())