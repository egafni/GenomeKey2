from .util import parse_inputs
from ...aws import s3

from ..tools import bwa, picard, gatk, samtools, fastqc, bed
from . import util

from cosmos.api import one2one, many2one, out_dir, group, load_input
import os

def run_germline(execution, target_bed, input_path=None, use_s3_bucket=None):
    """
    Executes the germline variant calling pipeline

    :param Execution execution: Execution instance
    :param target_bed: The target bed to call variants in
    :param input_path: The path to the input_file tsv of fastq files
    """
    #: chrom -> target_bed_path
    # target_bed = os.path.abspath(target_bed)
    # input_path = os.path.abspath(input_path)


    target_bed_tasks = [execution.add_task(bed.spit_bed_by_contig, tags=dict(contig=contig, in_bed=target_bed, skip_s3_pull=True), out_dir='work/contigs/{contig}')
                        for contig in util.get_contigs(target_bed)]

    fastq_tasks = [execution.add_task(load_input, dict(in_file=fastq_path, **tags)) for fastq_path, tags in parse_inputs(input_path)]
    fastqc_tasks = [execution.add_task(fastqc.fastqc, tags, parents, 'output/{sample_name}/qc')
                    for tags, parents in group(fastq_tasks, ['sample_name'])]

    aligned_tasks = align(execution, fastq_tasks, target_bed_tasks)
    called_tasks = variant_call(execution, aligned_tasks, target_bed_tasks)

    execution.run(cmd_wrapper=s3.make_wrapper(use_s3_bucket))
    execution.log.info('Final vcf: %s' % called_tasks[0].output_files[0])


def align(execution, fastqs, target_bed_tasks):
    """
    Reads -> Alignments

    :param Execution execution: The Execution instance to create Tasks in
    :param list[Task] | [(str, dict)] fastqs: Fastq input (file_path, dict) tuples or Tasks
    :param list[Task] target_bed_tasks: target beds to parallelize/split on
    :return: Indel Realigned Tasks
    """
    aligns = [execution.add_task(bwa.bwa_mem, tags, parents, out_dir='work/{sample_name}/readgroup_{rgid}/chunk_{chunk}')
              for tags, parents in group(fastqs, by=['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk'])]

    dedupe = many2one(execution, picard.mark_duplicates, aligns, groupby=['sample_name', 'library'], out_dir='work/{sample_name}/library_{library}')

    # Skipping BQSR.  Will improve results only slightly, if at all.


    # Note, could get slightly improved results by indel realigning over multiple samples
    # for tags, parents in group(dedupe, ['sample_name']):
    #     for target_bed_task in target_bed_tasks:
    #         d = dict(contig=target_bed_task.tags['contig'],
    #                                      in_target_bed=target_bed_task.output_files[0],
    #                                      **tags)
    #

    rtc_tasks = [execution.add_task(gatk.realigner_target_creator,
                                    dict(contig=target_bed_task.tags['contig'],
                                         in_target_bed=target_bed_task.output_files[0],
                                         **tags),
                                    parents + [target_bed_task],
                                    out_dir='work/{sample_name}/contigs/{contig}')
                 for tags, parents in group(dedupe, ['sample_name'])  # Many2one
                 for target_bed_task in target_bed_tasks]  # One2many

    realigned_by_sample_contig_tasks = one2one(execution, gatk.indel_realigner, rtc_tasks)

    # Merge bams so we have a sample bam.  Returning realign, so bams remained split by contig for downstream
    # parallelization
    merged_bams = [execution.add_task(samtools.merge, tags=dict(bam_name='aligned', **tags),
                                      parents=parents, out_dir='output/{sample_name}', stage_name="Merge_Sample_Bams")
                   for tags, parents in group(realigned_by_sample_contig_tasks, ['sample_name'])],

    return realigned_by_sample_contig_tasks


def variant_call(execution, aligned_tasks, target_bed_tasks):
    """
    Alignments -> Variants

    :param Execution execution:
    :param list[Task] aligned_tasks:
    :param list[Task] target_bed_tasks:
    :return:
    """
    contig_to_targets = {t.tags['contig']: t for t in target_bed_tasks}

    hapcall_tasks = [execution.add_task(gatk.haplotype_caller, tags=tags, parents=parents + [contig_to_targets[tags['contig']]],
                                        out_dir='work/{sample_name}/contigs/{contig}')
                     for tags, parents in group(aligned_tasks, ['sample_name', 'contig'])]

    combine_gvcf_tasks = many2one(execution, gatk.combine_gvcfs, hapcall_tasks, groupby=['sample_name'], out_dir='output/{sample_name}')

    genotype_tasks = many2one(execution, gatk.genotype_gvcfs, hapcall_tasks, groupby=[], out_dir='output')

    # Run VQSR or some basic filtering?

    return genotype_tasks