import csv
import os
from cosmos.api import load_input, out_dir, forward
# from ..tools.misc import load_input_s3
import subprocess as sp
from genomekey.aws.s3 import cmd as s3cmd

__author__ = 'erik'


def get_bed_contigs(in_bed):
    # todo support s3?
    return sp.check_output("cat %s |cut -f1|uniq" % in_bed, shell=True).strip().split("\n")


def parse_inputs(input_path):
    columns = ['sample_name', 'rgid', 'chunk', 'read_pair', 'library', 'platform_unit', 'platform', 'path']
    with open(input_path) as fh:
        for d in csv.DictReader(fh, delimiter="\t"):
            # f = lambda p: p if p.startswith('s3://') else os.path.abspath(p)
            for c in columns:
                assert c in d, 'missing column %s in %s' % (c, input_path)
            yield d.pop('path'), d

def download_from_s3(in_file, out_file=out_dir('{in_file}')):
    assert in_file.startswith('s3://')
    return s3cmd.cp(in_file, out_file)

def gen_fastq_tasks(execution, input_path):
    for fastq_path, tags in parse_inputs(input_path):
        if fastq_path.startswith('s3://'):
            yield execution.add_task(download_from_s3,
                                     dict(in_file=fastq_path, out_file=out_dir('SM_{sample_name}/work/input/%s' % os.path.basename(fastq_path)), **tags),
                                     stage_name='Download_Fastqs_From_S3')
        else:
            yield execution.add_task(load_input, dict(in_file=fastq_path, **tags), stage_name='Load_Fastqs')