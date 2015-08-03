from .util import split_target_beds_by_contig, parse_inputs

from ..tools import bwa, picard, gatk, samtools, fastqc

from cosmos import one2one, many2one
from cosmos.util.tool import reduce_


def run_dna_seq(execution, target_bed, input_path=None):
    # chrom -> target_bed_path
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


def align(ex, fastqs, target_beds_dict):
    """Reads -> Alignments"""
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

    rtc = ex.add(gatk.RealignerTargetCreator(tags=dict(contig=contig, **tags),
                                             parents=parents + [target_bed_task],
                                             out='work/{sample_name}/contigs/{contig}')
                 for tags, parents in reduce_(dedupe, ['sample_name'])  # Many2one
                 for contig, target_bed_task in target_beds_dict.items())  # One2many

    realign = ex.add(one2one(gatk.IndelRealigner, rtc))

    merged_bams = ex.add((samtools.Merge(tags=dict(bam_name='aligned', **tags),
                                         parents=parents,
                                         out='output/{sample_name}')
                          for tags, parents in reduce_(realign, ['sample_name'])),
                         name="Merge_Sample_Bams")

    return realign


def variant_call(ex, aligned, target_beds_dict):
    """Alignments -> Variants"""
    hap_call = ex.add(gatk.HaplotypeCaller(tags=tags,
                                           parents=group + [target_beds_dict[tags['contig']]],
                                           out='work/{sample_name}/contigs/{contig}')
                      for tags, group in reduce_(aligned, ['sample_name', 'contig']))

    combine_gvcfs = ex.add(many2one(gatk.CombineGVCFs, hap_call,
                                    groupby=['sample_name'],
                                    out='output/{sample_name}'),
                           name='Create_Multisample_GVCF')

    genotypes = ex.add(many2one(gatk.GenotypeGVCFs, hap_call,
                                groupby=[],
                                out='output'))

    # Run VQSR or some basic filtering?

    return genotypes