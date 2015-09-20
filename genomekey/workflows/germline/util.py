import csv
import os

from cosmos import Input
from genomekey.workflows.tools import bed
import subprocess as sp

__author__ = 'erik'


def get_bed_contigs(in_bed):
    # todo support s3?
    return sp.check_output("cat %s |cut -f1|uniq" % in_bed, shell=True).strip().split("\n")


def parse_inputs(input_path):
    columns = ['sample_name', 'rgid', 'chunk', 'read_pair', 'library', 'platform_unit', 'platform', 'path']
    with open(input_path) as fh:
        for d in csv.DictReader(fh, delimiter="\t"):
            f = lambda p: p if p.startswith('s3://') else os.path.abspath(p)
            yield d.pop('path'), d