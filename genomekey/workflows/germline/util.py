import csv
import os

from cosmos import Input
from genomekey.workflows.tools import bed
import subprocess as sp

__author__ = 'erik'


def get_contigs(bed):
    return sp.check_output("cat %s |cut -f1|uniq" % bed, shell=True).strip().split("\n")


def split_target_beds_by_contig(ex, target_bed):
    """Load and split up target bed by chromosome"""
    target_bed_inp = ex.add(Input(os.path.abspath(target_bed), 'target', 'bed'), name='Load_Target_Bed')
    target_beds = ex.add(bed.Split_Bed_By_Contig(tags=dict(contig=contig, target_bed=target_bed),
                                                 parents=target_bed_inp,
                                                 out='work/contigs/{contig}')
                         for contig in get_contigs(target_bed))
    return {tb.tags['contig']: tb for tb in target_beds}


def parse_inputs(input_path):
    columns = ['sample_name', 'rgid', 'chunk', 'read_pair', 'library', 'platform_unit', 'platform', 'path']
    with open(input_path) as fh:
        for d in csv.DictReader(fh, delimiter="\t"):
            f = lambda p: p if p.startswith('s3://') else os.path.abspath(p)
            yield d.pop('path'), d