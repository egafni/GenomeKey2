from cosmos.api import find, out_dir
from ...api import settings as s

def list_to_input(l):
    return " ".join('INPUT=%s' % x for x in l)


def picard(time_req=12 * 60, mem_req=3 * 1024, extra_java_args=''):
    return 'java{extra_java_args} ' \
           '-Xmx{mem_req2}m -Djava.io.tmpdir={s[gk][tmp_dir]} ' \
           '-Dsnappy.loader.verbosity=true ' \
           '-jar {s[opt][picard]}'.format(s=s,
                                          mem_req2=int(mem_req * .8),
                                          **locals())


def mark_duplicates(mem_req=3 * 1024,
                    in_bams=find('bam$', n='>=1'),
                    in_bais=find('bai$', n='>=1'),
                    out_bam=out_dir('deduped.bam'),
                    out_bai=out_dir('deduped.bam.bai'),
                    metrics=out_dir('deduped.metrics')):
    return r"""
        {picard} MarkDuplicates \
        {inputs} \
        O={out_bam} \
        METRICS_FILE={metrics} \
        ASSUME_SORTED=True \
        MAX_RECORDS_IN_RAM=1000000 \
        VALIDATION_STRINGENCY=SILENT \
        VERBOSITY=INFO

        {s[opt][samtools]} index {out_bam}
    """.format(inputs=list_to_input(in_bams), s=s,
               picard=picard(),
               **locals())


