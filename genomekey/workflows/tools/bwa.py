from cosmos.api import find, out_dir
from ...api import settings as s
from genomekey.api import can_stream
from . import picard




@can_stream(['in_fastqs','in_fastq1', 'in_fastq2'])
def bwa_mem(rgid, sample_name, library, platform, platform_unit,
            reference=s['ref']['reference_fasta'],
            cpu_req=16,
            # in_fastq1=find('.fastq', tags=dict(read_pair='1')),
            # in_fastq2=find('.fastq', tags=dict(read_pair='2')),
            in_fastqs=find('.fastq', n=2),
            out_bam=out_dir('aligned.bam'),
            out_bai=out_dir('aligned.bam.bai')):

    in_fastq1, in_fastq2=in_fastqs
    return r"""

              {s[opt][bwa]} mem \
              -t {cpu_req} -L 0 -M \
              -R "@RG\tID:{rgid}\tLB:{library}\tSM:{sample_name}\tPL:{platform}\tPU:{platform_unit}" \
              {reference} \
              {in_fastq1} \
              {in_fastq2} \
            | {s[opt][samtools]} sort -@ 2 -m 2G - {samtools_out}

            {s[opt][samtools]} index {out_bam}
            """.format(s=s,
                       samtools_out=out_bam.replace('.bam', ''),
                       **locals())


# @can_stream(['in_fastq1', 'in_fastq2'])
# def bwa_mem_with_trimming(rgid, sample_name, library, platform, platform_unit,
#             reference=s['ref']['reference_fasta'],
#             cpu_req=16,
#             in_fastq1=find('.fastq', tags=dict(read_pair='1')),
#             in_fastq2=find('.fastq', tags=dict(read_pair='2')),
#             out_bam=out_dir('aligned.bam'),
#             out_bai=out_dir('aligned.bam.bai'),
#             out_adapter_metrics=out_dir('adapter.metrics')):
#     return r"""
#
#             {fastq_to_sam} \
#             | {mark_illumina_adapters} \
#             | {sam_to_fastq}
#             | {s[opt][bwa]} mem \
#               -t {cpu_req} -L 0 -M -p \
#               -R "@RG\tID:{rgid}\tLB:{library}\tSM:{sample_name}\tPL:{platform}\tPU:{platform_unit}" \
#               {reference} \
#               /dev/stdin \
#             | {s[opt][samtools]} sort -@ 2 -m 2G - {samtools_out}
#
#             {s[opt][samtools]} index {out_bam}
#             """.format(s=s,
#                        fastq_to_sam=picard.fastq_to_sam(rgid=rgid, sample_name=sample_name, library=library, platform=platform, platform_unit=platform_unit,
#                                                         in_fastq1=in_fastq1, in_fastq2=in_fastq2, out_bam='/dev/stdout').strip(),
#                        mark_illumina_adapters=picard.mark_illumina_adapters(in_bam='/dev/stdin', out_bam='/dev/stdout', metrics=out_adapter_metrics).strip(),
#                        sam_to_fastq=picard.sam_to_fastq_interleave('/dev/stdin', '/dev/stdout'),
#
#                        samtools_out=out_bam.replace('.bam', ''),
#                        **locals())