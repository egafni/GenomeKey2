from .util import parse_inputs
from genomekey.api import settings, make_s3_cmd_fxn_wrapper, s3cmd, s3run, shared_fs_cmd_fxn_wrapper

from ..tools import bwa, picard, gatk, samtools, fastqc, bed, fastq
from . import util
from genomekey.bin.fastq.split_fastq_file import get_split_paths
from genomekey.aws.s3 import cmd as s3cmd


from cosmos.api import one2one, many2one, out_dir, group, load_input, Execution, make_dict, bash_call
import os
import math

opj = os.path.join
import subprocess as sp

FASTQ_MAX_CHUNK_SIZE = 2 ** 30 / 2
FASTQ_MAX_CHUNK_SIZE = 2 ** 20  # 1Mb for testing


def run_germline(execution, target_bed, input_path=None, s3fs=None):
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
    cp_target_bed_task = execution.add_task(lambda drm='local', out_bed=out_dir('target.bed'): 'cp %s %s' % (target_bed, out_bed),
                                            out_dir='', stage_name='Copy_Target_Bed')

    target_bed_tasks = [execution.add_task(bed.filter_bed_by_contig, dict(contig=contig), [cp_target_bed_task], 'work/contigs/{contig}')
                        for contig in util.get_bed_contigs(target_bed)]

    fastq_tasks = list(util.gen_fastq_tasks(execution, input_path))

    fastqc_tasks = many2one(fastqc.fastqc, fastq_tasks, ['sample_name', 'library'], out_dir='SM_{sample_name}/qc/LB_{library}')

    # fastq_tasks = split_large_fastq_files(execution, fastq_tasks) # not working yet
    aligned_tasks = align(execution, fastq_tasks, target_bed_tasks)
    called_tasks = variant_call(execution, aligned_tasks, target_bed_tasks)

    execution.run(cmd_wrapper=make_s3_cmd_fxn_wrapper(s3fs) if s3fs else shared_fs_cmd_fxn_wrapper)

    if execution.successful:
        execution.log.info('Final vcf: %s' % opj(s3fs if s3fs else execution.output_dir.output_dir,
                                                 called_tasks[0].output_files[0]))


    # Copy the sqlite db to s3
    dburl = settings['gk']['database_url']
    if s3fs and dburl.startswith('sqlite'):
        # TODO implement so there is a 1-to-1 relationship between a sqlite database and an Execution.  Currently this is pushing way too much information,
        # TODO but will soon be replaced.  Alternative: use amazon RDS!  Or perhaps both?  Could do a sqlalchemy merge and save to sqlite, or implement
        # TODO cosmos multiverse
        s3cmd.cp(dburl.replace('sqlite:///', ''), opj(s3fs, 'sqlite.db.backup'))


def split_large_fastq_files(execution, fastq_tasks):
    def gen():
        for tags, (fastq_task,) in group(fastq_tasks, ['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk', 'read_pair']):
            fastq_path = fastq_task.output_files[0]
            file_size = float(s3run.get_filesize(fastq_path) if fastq_path.startswith('s3://') else os.stat(file_size).st_size)

            if file_size > FASTQ_MAX_CHUNK_SIZE:
                # split into 500MB files
                num_chunks = int(math.ceil(float(file_size) / FASTQ_MAX_CHUNK_SIZE))
                assert num_chunks < 100, 'Doubt you want this many chunks'

                out_path = 'SM_{sample_name}/work/LB_{library}/RP_{read_pair}/chunk{chunk}'.format(**fastq_task.tags)
                prefix = opj(out_path, 'reads_')

                split_task = execution.add_task(fastq.split_fastq_file,
                                                dict(num_chunks=num_chunks,
                                                     prefix=prefix,
                                                     out_fastqs=get_split_paths(prefix, num_chunks),
                                                     **fastq_task.tags),
                                                fastq_task,
                                                out_dir=out_path)

                for out_fastq in split_task.output_files:
                    yield execution.add_task(load_input, make_dict(fastq_task.tags, in_file=out_fastq),
                                             split_task, stage_name='Load_Split_Fastq_Files'
                    )

            else:
                yield fastq_task

    return list(gen())


def align(execution, fastq_tasks, target_bed_tasks):
    """
    Reads -> Alignments

    :param Execution execution: The Execution instance to create Tasks in
    :param list[Task] | [(str, dict)] fastq_tasks: Fastq input (file_path, dict) tuples or Tasks
    :param list[Task] target_bed_tasks: target beds to parallelize/split on
    :return: Indel Realigned Tasks
    """

    # Do we need to split fastqs into smaller pieces?
    trimmed = many2one(fastq.cut_adapt, fastq_tasks, ['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk'],
                       out_dir='SM_{sample_name}/work/RG_{rgid}/CH_{chunk}')

    aligns = one2one(bwa.bwa_mem, trimmed, out_dir='SM_{sample_name}/work/RG_{rgid}/CH_{chunk}')

    dedupe = many2one(picard.mark_duplicates, aligns, groupby=['sample_name', 'library'], out_dir='SM_{sample_name}/work/LB_{library}')

    # Note, could get slightly improved results by indel realigning over multiple samples, especially if low coverage
    # for tags, parents in group(dedupe, ['sample_name']):
    # for target_bed_task in target_bed_tasks:
    # d = dict(contig=target_bed_task.tags['contig'],
    # in_target_bed=target_bed_task.output_files[0],
    # **tags)
    #

    rtc_tasks = [execution.add_task(gatk.realigner_target_creator,
                                    dict(contig=target_bed_task.tags['contig'],
                                         in_target_bed=target_bed_task.output_files[0], **tags),
                                    parents + [target_bed_task],
                                    out_dir='SM_{sample_name}/work/contigs/{contig}')
                 for tags, parents in group(dedupe, ['sample_name'])  # Many2one
                 for target_bed_task in target_bed_tasks]  # One2many

    realigned_by_sample_contig_tasks = one2one(gatk.indel_realigner, rtc_tasks)


    # Skipping BQSR.  Will improve results only slightly, if at all.


    # Merge bams so we have a sample bam.  Returning realign, so bams remained split by contig for downstream
    # parallelization
    many2one(samtools.merge, realigned_by_sample_contig_tasks, ['sample_name'], out_dir='SM_{sample_name}', stage_name="Merge_Sample_Bams")

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
                                        out_dir='SM_{sample_name}/work/contigs/{contig}')
                     for tags, parents in group(aligned_tasks, ['sample_name', 'contig'])]

    combine_gvcf_tasks = many2one(gatk.combine_gvcfs, hapcall_tasks, groupby=['sample_name'], out_dir='SM_{sample_name}')

    genotype_tasks = many2one(gatk.genotype_gvcfs, hapcall_tasks, groupby=[], out_dir='')

    # Run VQSR or some basic filtering?

    return genotype_tasks