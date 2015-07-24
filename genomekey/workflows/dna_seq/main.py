import csv
import os
import itertools as it
import subprocess as sp

from ..tools import bwa, picard, gatk, samtools, bed, fastqc
from genomekey import aws
from cosmos import Input, one2one, many2one
from cosmos.util.tool import reduce_, make_dict


def get_contigs(bed):
    return sp.check_output("cat %s |cut -f1|uniq" % bed, shell=True).strip().split("\n")


def parse_inputs(input_path):
    # columns = sample_name, rgid, chunk, read_pair, library, platform_unit, platform, path
    with open(input_path) as fh:
        for d in csv.DictReader(fh, delimiter="\t"):
            f = lambda p: p if p.startswith('s3://') else os.path.abspath(p)
            yield Input(f(d.pop('path')), 'r2', 'fastq.gz', d)
            # yield Inputs(inputs, tags=d)


def run_dna_seq(execution, target_bed, input_path=None):
    os.environ.update(aws.get_aws_env())

    target_beds_dict = split_target_beds_by_contig(execution, target_bed)

    fastqs = execution.add(parse_inputs(input_path), name="Load_Fastqs")
    fqc = execution.add(fastqc.FastQC(tags,
                                      parents,
                                      'output/{sample_name}/qc')
                        for tags, parents in reduce_(fastqs, ['sample_name']))

    aligned = align(execution, fastqs, target_beds_dict)
    called = variant_call(execution, aligned, target_beds_dict)

    execution.run()
    execution.log.info('Final vcf: %s' % called[0].output_files[0].path)


def split_target_beds_by_contig(ex, target_bed):
    """Load and split up target bed by chromosome"""
    target_bed_inp = ex.add(Input(os.path.abspath(target_bed), 'target', 'bed'), name='Load_Target_Bed')
    target_beds = ex.add(bed.Split_Bed_By_Contig(tags=dict(contig=contig, target_bed=target_bed),
                                             parents=target_bed_inp,
                                             out='work/contigs/{contig}')
                         for contig in get_contigs(target_bed))
    return {tb.tags['contig']: tb for tb in target_beds}


def align(ex, fastqs, target_beds_dict):
    """Reads to Alignments"""
    aligns = ex.add(bwa.BWA_MEM(tags,
                                parents=parents,
                                out='work/{sample_name}/readgroup_{rgid}/chunk_{chunk}')
                    for tags, parents in
                    reduce_(fastqs, ['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk']))

    dedupe = ex.add(many2one(picard.MarkDuplicates, aligns,
                             groupby=['sample_name', 'library'],
                             out='work/{sample_name}/library_{library}'))

    # Skipping BQSR.  Will improve results only slightly, if at all.


    # Note, could get slightly improved results by indel realigning over multiple samples

    rtc = ex.add(gatk.RealignerTargetCreator(tags=make_dict(tags, contig=contig),
                                             parents=it.chain(parents, [target_bed_task]),
                                             out='work/{sample_name}/contigs/{contig}')
                 for tags, parents in reduce_(dedupe, ['sample_name'])  # Many2one
                 for contig, target_bed_task in target_beds_dict.items())  # One2many

    realign = ex.add(one2one(gatk.IndelRealigner, rtc))

    merged = ex.add((samtools.Merge(tags=make_dict(tags, bam_name='align'),
                                    parents=parents,
                                    out='output/{sample_name}')
                     for tags, parents in reduce_(realign, ['sample_name'])),
                    name="Merge_Sample_Bams")

    return realign


def variant_call(ex, aligned, target_beds_dict):
    """Alignments to Variants"""
    hap_call = ex.add(gatk.HaplotypeCaller(tags=tags,
                                           parents=it.chain(group, [target_beds_dict[tags['contig']]]),
                                           out='work/{sample_name}/contigs/{contig}')
                      for tags, group in reduce_(aligned, ['sample_name', 'contig']))

    merged = ex.add(many2one(gatk.CombineGVCFs, hap_call,
                             groupby=['sample_name'],
                             out='output/{sample_name}'),
                    name='Create_Multisample_GVCF')

    genotypes = ex.add(many2one(gatk.GenotypeGVCFs, hap_call,
                                groupby=[],
                                out='output'))

    # Run VQSR or some basic filtering?

    return genotypes