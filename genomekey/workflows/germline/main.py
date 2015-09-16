from .util import parse_inputs
from ...aws import s3
from ...api import settings

from ..tools import bwa, picard, gatk, samtools, fastqc, bed
from . import util

from cosmos.api import one2one, many2one, out_dir, group, load_input, Execution
import os


def run_germline(execution, target_bed, input_path=None, use_s3_bucket=None):
    """
    Executes the germline variant calling pipeline

    :type execution: Execution
    :param str target_bed: The target bed to call variants in
    :param str input_path: The path to the input_file tsv of fastq files
    """
    #: chrom -> target_bed_path
    # target_bed = os.path.abspath(target_bed)
    # input_path = os.path.abspath(input_path)

    # Copy the target.bed to the output_dir
    assert os.path.exists(target_bed), '%s does not exist' % target_bed
    cp_target_bed_task = execution.add_task(lambda drm='local', out_bed=out_dir('target.bed'): 'cp %s %s' % (target_bed, out_bed), tags=dict(skip_s3_pull=True),
                                            out_dir='output', stage_name='Copy_Target_Bed')

    # Split target.bed by contigs
    target_bed_tasks = [execution.add_task(bed.spit_bed_by_contig, dict(contig=contig), [cp_target_bed_task], 'work/contigs/{contig}')
                        for contig in util.get_contigs(target_bed)]

    # Load fastq inputs into NOOP tasks for easier downstream grouping
    fastq_tasks = [execution.add_task(load_input, dict(in_file=fastq_path, **tags), stage_name='Load_Fastqs')
                   for fastq_path, tags in parse_inputs(input_path)]

    # Run Fastqc
    fastqc_tasks = many2one(execution, fastqc.fastqc, fastq_tasks, ['sample_name'], out_dir='output/{sample_name}/qc')

    aligned_tasks = align(execution, fastq_tasks, target_bed_tasks)
    called_tasks = variant_call(execution, aligned_tasks, target_bed_tasks)

    execution.run(cmd_wrapper=s3.make_s3_cmd_fxn_wrapper(use_s3_bucket))

    if execution.successful:
        execution.log.info('Final vcf: %s' % os.path.join(use_s3_bucket if use_s3_bucket else execution.output_dir.output_dir,
                                                          called_tasks[0].output_files[0]))


    # Copy the sqlite db to s3
    dburl = settings['gk']['database_url']
    if use_s3_bucket and dburl.startswith('sqlite'):
        # TODO implement so there is a 1-to-1 relationship between a sqlite database and an Execution.  Currently this is pushing way too much information,
        # TODO but will soon be replaced.  Alternative: use amazon RDS!  Or perhaps both?  Could do a sqlalchemy merge and save to sqlite, or implement
        # TODO cosmos multiverse
        s3.cp(dburl.replace('sqlite:///', ''), os.path.join(use_s3_bucket, 'sqlite.db.backup'))


def align(execution, fastq_tasks, target_bed_tasks):
    """
    Reads -> Alignments

    :param Execution execution: The Execution instance to create Tasks in
    :param list[Task] | [(str, dict)] fastq_tasks: Fastq input (file_path, dict) tuples or Tasks
    :param list[Task] target_bed_tasks: target beds to parallelize/split on
    :return: Indel Realigned Tasks
    """
    aligns = many2one(execution, bwa.bwa_mem, fastq_tasks, ['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk'],
                      out_dir='output/{sample_name}/qc')

    dedupe = many2one(execution, picard.mark_duplicates, aligns, groupby=['sample_name', 'library'], out_dir='work/{sample_name}/library_{library}')

    # Skipping BQSR.  Will improve results only slightly, if at all.


    # Note, could get slightly improved results by indel realigning over multiple samples
    # for tags, parents in group(dedupe, ['sample_name']):
    # for target_bed_task in target_bed_tasks:
    # d = dict(contig=target_bed_task.tags['contig'],
    # in_target_bed=target_bed_task.output_files[0],
    # **tags)
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
                                      parents=parents, out_dir='', stage_name="Merge_Sample_Bams")
                   for tags, parents in group(realigned_by_sample_contig_tasks, ['sample_name'])],

    many2one(execution, samtools.merge, realigned_by_sample_contig_tasks, ['sample_name'], out_dir='output/{sample_name}', stage_name="Merge_Sample_Bams")

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