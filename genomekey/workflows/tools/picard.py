from cosmos import abstract_input_taskfile as aif, abstract_output_taskfile as aof
from ... import settings as s, GK_Tool


def list_to_input(l):
    return " ".join('INPUT=%s' % x for x in l)


class Picard(GK_Tool):
    time_req = 12 * 60
    mem_req = 3 * 1024
    cpu_req = 1
    extra_java_args = ''

    @property
    def bin(self):
        return 'java{self.extra_java_args} ' \
               '-Xmx{mem_req}m -Djava.io.tmpdir={s[gk][tmp_dir]} ' \
               '-Dsnappy.loader.verbosity=true ' \
               '-jar {s[opt][picard]}'.format(s=s,
                                              mem_req=int(self.mem_req * .8),
                                              **locals())


class MarkDuplicates(Picard):
    def cmd(self, use_s3=False,
            in_bams=aif(format='bam', n='>=1'),
            in_bais=aif(format='bai', n='>=1'),
            out_bam=aof('deduped.bam'),
            out_bai=aof('deduped.bam.bai'),
            metrics=aof('deduped.metrics')):
        return r"""
            {self.bin} MarkDuplicates \
            {inputs} \
            O={out_bam} \
            METRICS_FILE={metrics} \
            ASSUME_SORTED=True \
            MAX_RECORDS_IN_RAM=1000000 \
            VALIDATION_STRINGENCY=SILENT \
            VERBOSITY=INFO

            {s[opt][samtools]} index {out_bam}
        """.format(inputs=list_to_input(in_bams), s=s,
                   **locals())


