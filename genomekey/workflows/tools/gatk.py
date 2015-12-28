from cosmos.api import find, out_dir, forward
from genomekey.api import settings as s

bam_list_to_inputs = lambda l: " -I ".join(map(str, l))
vcf_list_to_input = lambda l: " -V ".join(map(str, l))


def arg(flag, value=None):
    return '%s %s' % (flag, value) if value else ''


def gatk(mem_req=5 * 1024):
    return 'java -Xmx{mem_req2}m -Djava.io.tmpdir={s[gk][tmp_dir]} -jar {s[opt][gatk]}'.format(
        s=s, mem_req2=int(mem_req * .9), **locals()
    )


def realigner_target_creator(cpu_req=4,
                             mem_req=8 * 1024,
                             in_target_bed=find('target.bed'),
                             in_bams=find('bam$', n='>0'),
                             in_bais=find('bai$', n='>0'),
                             out_bams=forward('in_bams'),
                             out_bais=forward('in_bais'),
                             out_sites=out_dir('denovo_realign_targets.bed')):
    in_bams = bam_list_to_inputs(in_bams)
    intervals = arg('--intervals', in_target_bed)
    # TODO should we pad intervals?  might be indels on perimeter that need realigner.  Not too worried because we're using HaplotypeCaller, though.
    return r"""
        #could add more knowns from ESP and other seq projects...
        {gatk} \
        -T RealignerTargetCreator \
        -R {s[ref][reference_fasta]} \
        -I {in_bams} \
        -o {out_sites} \
        --known {s[ref][1kg_indel_vcf]} \
        --known {s[ref][mills_vcf]} \
        -nt {cpu_req} \
        {intervals}
    """.format(s=s, gatk=gatk(mem_req), **locals())


def indel_realigner(mem_req=8 * 1024,
                    contig=None,
                    in_bams=find('bam$', n='>0'),
                    in_bais=find('bai$', n='>0'),
                    in_sites=find('denovo_realign_targets.bed'),
                    out_bam=out_dir('realigned.bam'),
                    out_bai=out_dir('realigned.bai')):
    in_bams = bam_list_to_inputs(in_bams)
    return r"""
        # IR does not support parallelization
        {gatk} \
        -T IndelRealigner \
        -R {s[ref][reference_fasta]} \
        -I {in_bams} \
        -o {out_bam} \
        -targetIntervals {in_sites} \
        -known {s[ref][1kg_indel_vcf]} \
        -known {s[ref][mills_vcf]} \
        -model USE_READS \
        --filter_bases_not_stored \
        {intervals}

        {s[opt][samtools]} index {out_bam}
    """.format(s=s,
               intervals=arg('--intervals', contig),
               gatk=gatk(mem_req),
               **locals())


def haplotype_caller(cpu_req=8,
                     mem_req=16 * 1024,
                     in_bams=find('bam$', n='>0'),
                     in_bais=find('bai$', n='>0'),
                     in_target_bed=find('target.bed'),
                     out_vcf=out_dir('raw_variants.g.vcf')):
    in_bams = bam_list_to_inputs(in_bams)
    intervals = arg('--intervals', in_target_bed)
    return r"""
        {gatk} \
        -T HaplotypeCaller \
        -R {s[ref][reference_fasta]} \
        -D {s[ref][dbsnp_vcf]} \
        -nct {cpu_req} \
        --emitRefConfidence GVCF \
        -stand_call_conf 30 \
        -stand_emit_conf 10 \
        -I {in_bams} \
        -o {out_vcf} \
        {intervals} \
        -A Coverage \
        -A GCContent \
        -A AlleleBalanceBySample \
        -A AlleleBalance \
        -A HaplotypeScore \
        -A MappingQualityRankSumTest \
        -A InbreedingCoeff \
        -A FisherStrand \
        -A QualByDepth
    """.format(s=s, gatk=gatk(mem_req), **locals())


def genotype_gvcfs(cpu_req=8,
                   mem_req=12 * 1024,
                   in_vcfs=find('vcf|vcf.gz$', n='>0'),
                   out_vcf=out_dir('variants.vcf')):
    in_vcfs = vcf_list_to_input(in_vcfs)

    return r"""
        {gatk} \
        -T GenotypeGVCFs \
        -R {s[ref][reference_fasta]} \
        -nt {cpu_req} \
        -V {in_vcfs} \
        -o {out_vcf}
    """.format(s=s, gatk=gatk(mem_req), **locals())


def combine_gvcfs(mem_req=12 * 1024,
                  in_vcfs=find('vcf|vcf.gz$', n='>0'),
                  out_vcf=out_dir('variants.g.vcf')):
    in_vcfs = vcf_list_to_input(in_vcfs)

    return r"""
        {gatk} \
        -T CombineGVCFs \
        -R {s[ref][reference_fasta]} \
        -V {in_vcfs} \
        -o {out_vcf}
    """.format(s=s, gatk=gatk(mem_req), **locals())


