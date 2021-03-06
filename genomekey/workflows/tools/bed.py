from cosmos.api import find, out_dir
from genomekey.api import get_env
s = get_env().config

def filter_bed_by_contig(contig,
                       drm='local',
                       in_bed=find('bed$'),
                       out_bed=out_dir('target.bed')):
    return r"""
        grep -P "^{contig}\t" {in_bed} > {out_bed}
    """.format(s=s, **locals())