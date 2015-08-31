from cosmos.api import find, out_dir
from ... import settings as s
from genomekey.aws import s3


def bwa_mem(rgid, sample_name, library, platform, platform_unit,
            reference=s['ref']['reference_fasta'],
            cpu_req=16,
            reads=find('fastq|fastq.gz', n=2),
            out_bam=out_dir('aligned.bam'),
            out_bai=out_dir('aligned.bam.bai')):
    r1, r2 = sorted(reads, key=lambda tf: tf.task_output_for.tags['read_pair'])

    if r1.path.startswith('s3://'):
        r1, r2 = [s3.stream_in(tf.path, md5=False) for tf in [r1, r2]]


    return r"""
            {s[opt][bwa]} mem \
            -t {self.cpu_req} -L 0 -M \
            -R "@RG\tID:{rgid}\tLB:{library}\tSM:{sample_name}\tPL:{platform}\tPU:{platform_unit}" \
            {reference} \
            {r1} \
            {r2} \
            | {s[opt][samtools]} sort -@ 2 -m 2G - {samtools_out}

            {s[opt][samtools]} index {out_bam}
            """.format(s=s,
                       samtools_out=out_bam.path.replace('.bam', ''),
                       **locals())
