from cosmos import abstract_input_taskfile as aif, abstract_output_taskfile as aof
from genomekey import settings as s

from ... import GK_Tool

bam_list_to_inputs = lambda l: " -I ".join(map(str, l))
vcf_list_to_input = lambda l: " -V ".join(map(str, l))


def arg(flag, value=None):
    return '%s %s' % (flag, value) if value else ''


class GATK(GK_Tool):
    time_req = None
    mem_req = 5 * 1024

    @property
    def bin(self):
        return 'java -Xmx{mem_req}m -Djava.io.tmpdir={s[gk][tmp_dir]} -jar {s[opt][gatk]}'.format(
            s=s, mem_req=int(self.mem_req * .9), **locals()
        )


class RealignerTargetCreator(GATK):
    mem_req = 8 * 1024
    cpu_req = 4

    def cmd(self,
            in_bams=aif(format='bam', n='>0', forward=True),
            in_bais=aif(format='bai', n='>0', forward=True),
            target_bed=aif('target', 'bed', forward=True),
            out_sites=aof('denovo_realign_targets.bed')):
        in_bams = bam_list_to_inputs(in_bams)
        intervals = arg('--intervals', target_bed.path)
        return r"""
            #could add more knowns from ESP and other seq projects...
            {self.bin} \
            -T RealignerTargetCreator \
            -R {s[ref][reference_fasta]} \
            -I {in_bams} \
            -o {out_sites} \
            --known {s[ref][1kg_indel_vcf]} \
            --known {s[ref][mills_vcf]} \
            -nt {self.cpu_req} \
            {intervals}
        """.format(s=s, **locals())


class IndelRealigner(GATK):
    mem_req = 8 * 1024
    cpu_req = 1

    def cmd(self,
            in_bams=aif(format='bam', n='>0'),
            in_bais=aif(format='bai', n='>0'),
            in_sites=aif('denovo_realign_targets', 'bed'),
            in_target_bed=aif('target', 'bed', forward=True),
            out_bam=aof('realigned.bam'),
            out_bai=aof('realigned.bai')):
        in_bams = bam_list_to_inputs(in_bams)
        intervals = arg('--intervals', in_target_bed.path)
        return r"""
            # IR does not support parallelization
            {self.bin} \
            -T IndelRealigner \
            -R {s[ref][reference_fasta]} \
            -I {in_bams} \
            -o {out_bam} \
            -targetIntervals {in_sites} \
            -known {s[ref][1kg_indel_vcf]} \
            -known {s[ref][mills_vcf]} \
            -model USE_READS \
            {intervals}

            {s[opt][samtools]} index {out_bam}
        """.format(s=s, **locals())


class HaplotypeCaller(GATK):
    cpu_req = 8
    mem_req = 16 * 1024

    def cmd(self,
            in_bams=aif(format='bam', n='>0'),
            in_bais=aif(format='bai', n='>0'),
            target_bed=aif('target', 'bed', forward=True),
            out_vcf=aof('raw_variants.g.vcf')):
        in_bams = bam_list_to_inputs(in_bams)
        intervals = arg('--intervals', target_bed.path)
        return r"""
            {self.bin} \
            -T HaplotypeCaller \
            -R {s[ref][reference_fasta]} \
            -D {s[ref][dbsnp_vcf]} \
            -nct {self.cpu_req} \
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

            """.format(s=s, **locals())


class GenotypeGVCFs(GATK):
    cpu_req = 8
    mem_req = 12 * 1024

    def cmd(self,
            in_vcfs=aif(format='vcf', n='>0'),
            out_vcf=aof('variants.vcf')):
        in_vcfs = vcf_list_to_input(in_vcfs)

        return r"""
            {self.bin} \
            -T GenotypeGVCFs \
            -R {s[ref][reference_fasta]} \
            -nt {self.cpu_req} \
            -V {in_vcfs} \
            -o {out_vcf}
            """.format(s=s, **locals())


class CombineGVCFs(GATK):
    mem_req = 12 * 1024

    def cmd(self,
            in_vcfs=aif(format='vcf', n='>0'),
            out_vcf=aof('variants.g.vcf')):
        in_vcfs = vcf_list_to_input(in_vcfs)

        return r"""
            {self.bin} \
            -T CombineGVCFs \
            -R {s[ref][reference_fasta]} \
            -V {in_vcfs} \
            -o {out_vcf}
            """.format(s=s, **locals())


