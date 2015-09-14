from cosmos.api import find, out_dir
from ... import settings as s
from genomekey.aws import s3

# @s3.can_stream(['in_fastq1', 'in_fastq2'])
def bwa_mem(rgid, sample_name, library, platform, platform_unit,
            reference=s['ref']['reference_fasta'],
            cpu_req=16,
            # reads=find('fastq|fastq.gz', n=2),
            in_fastq1=find('.fastq', tags=dict(read_pair='1')),
            in_fastq2=find('.fastq', tags=dict(read_pair='2')),
            out_bam=out_dir('aligned.bam'),
            out_bai=out_dir('aligned.bam.bai')):

    # if in_fastq1.startswith('s3://'):
    #     in_fastq1, in_fastq2 = [s3.stream_in(fastq, md5=False) for fastq in [in_fastq1, in_fastq2]]


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
bwa_mem.can_stream=['in_fastq1', 'in_fastq2']