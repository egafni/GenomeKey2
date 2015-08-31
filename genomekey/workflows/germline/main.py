from .util import split_target_beds_by_contig, parse_inputs

from ..tools import bwa, picard, gatk, samtools, fastqc

from cosmos.api import one2one, many2one, out_dir
from cosmos.util.tool import group


def run_germline(execution, target_bed, input_path=None):
    # chrom -> target_bed_path
    target_beds_dict = split_target_beds_by_contig(execution, target_bed)

    fastqs_w_tags = parse_inputs(input_path)
    fqc = [execution.add_task_task(fastqc.fastqc, tags, parents,
                                   'output/{sample_name}/qc')
           for tags, parents in group(fastqs_w_tags, ['sample_name'])]

    aligned = align(execution, fastqs_w_tags, target_beds_dict)
    called = variant_call(execution, aligned, target_beds_dict)

    execution.run()
    execution.log.info('Final vcf: %s' % called[0].output_files[0].path)


def align(execution, fastqs, target_beds_dict):
    """Reads -> Alignments"""
    aligns = [execution.add_task(bwa.bwa_mem, tags, parents,
                                 out_dir='work/{sample_name}/readgroup_{rgid}/chunk_{chunk}')
              for tags, parents in
              group(fastqs, ['sample_name', 'library', 'platform', 'platform_unit', 'rgid', 'chunk'])]

    dedupe = many2one(execution, picard.mark_duplicates, aligns,
                      groupby=['sample_name', 'library'],
                      out_dir='work/{sample_name}/library_{library}')

    # Skipping BQSR.  Will improve results only slightly, if at all.


    # Note, could get slightly improved results by indel realigning over multiple samples

    rtc = [execution.add_task(gatk.realigner_target_creator, dict(contig=contig, **tags), parents + [target_bed_task],
                              out_dir='work/{sample_name}/contigs/{contig}')
           for tags, parents in group(dedupe, ['sample_name'])  # Many2one
           for contig, target_bed_task in target_beds_dict.items()]  # One2many

    realign = one2one(execution, gatk.indel_realigner, rtc)

    # Merge bams so we have a sample bam.  Returning realign, so bams remained split by contig for downstream
    # parallelization
    merged_bams = [execution.add_task(samtools.merge,
                                      tags=dict(bam_name='aligned', out_bam=out_dir('{sample_name}.bam'), **tags),
                                      parents=parents,
                                      out='output/{sample_name}',
                                      stage_name="Merge_Sample_Bams")
                   for tags, parents in group(realign, ['sample_name'])],

    return realign


def variant_call(execution, aligned, target_beds_dict):
    """Alignments -> Variants"""
    hap_call = [execution.add_task(gatk.haplotype_caller, tags=tags,
                                   parents=parents + [target_beds_dict[tags['contig']]],
                                   out_dir='work/{sample_name}/contigs/{contig}')
                for tags, parents in group(aligned, ['sample_name', 'contig'])]

    combine_gvcfs = many2one(execution, gatk.combine_gvcfs, hap_call,
                             groupby=['sample_name'],
                             out_dir='output/{sample_name}')

    genotypes = many2one(execution, gatk.genotype_gvcfs, hap_call,
                         groupby=[],
                         out_dir='output')

    # Run VQSR or some basic filtering?

    return genotypes