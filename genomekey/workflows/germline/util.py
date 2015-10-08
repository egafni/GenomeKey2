import csv
import os
from cosmos.api import load_input, out_dir
from ..tools.misc import load_input_s3
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


def gen_fastq_tasks(execution, input_path):
    for fastq_path, tags in parse_inputs(input_path):
        if fastq_path.startswith('s3://'):
            yield execution.add_task(load_input_s3, dict(in_file=fastq_path, out_file=out_dir('SM_{sample_name}/work/input/%s' % fastq_path), **tags), stage_name='Load_Fastqs')
        else:
            yield execution.add_task(load_input_s3 if input_path.statswith('s3://') else load_input, dict(in_file=fastq_path, **tags), stage_name='Load_Fastqs')