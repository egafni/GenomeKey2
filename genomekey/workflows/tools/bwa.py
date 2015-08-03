from cosmos import abstract_input_taskfile as itf, abstract_output_taskfile as otf
from ... import settings as s
from genomekey.aws import s3
from ... import GK_Tool


class BWA_MEM(GK_Tool):
    mem_req = None
    cpu_req = 16
    skip_s3_pull = True

    def cmd(self, rgid, sample_name, library, platform, platform_unit, reference=s['ref']['reference_fasta'],
            reads=itf(format='fastq.gz', n=2),
            out_bam=otf('aligned.bam'),
            out_bai=otf('aligned.bam.bai')):
        r1, r2 = sorted(reads, key=lambda tf: tf.task_output_for.tags['read_pair'])

        if r1.path.startswith('s3://'):
            r1, r2 = [s3.stream_in(tf.path, md5=False) for tf in [r1, r2]]

        # s3_append = s3.cmd_append(use_s3, self)


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
