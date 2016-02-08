from cosmos.api import find, out_dir
from genomekey.api import settings as s, can_stream


def list_to_input(l):
    return " ".join('INPUT=%s' % x for x in l)


def picard(time_req=8 * 60, mem_req=3 * 1024, extra_java_args=''):
    return 'java{extra_java_args} ' \
           '-Xmx{mem_req2}m -Djava.io.tmpdir={s[gk][tmp_dir]} ' \
           '-Dsnappy.loader.verbosity=true ' \
           '-jar {s[opt][picard]}'.format(s=s,
                                          mem_req2=int(mem_req * .8),
                                          **locals())


# @can_stream([''])
def mark_duplicates(core_req=8,  # for scratch space
                    mem_req=12 * 1024,
                    in_bams=find('bam$', n='>=1'),
                    in_bais=find('bai$', n='>=1'),
                    out_bam=out_dir('deduped.bam'),
                    out_bai=out_dir('deduped.bam.bai'),
                    out_metrics=out_dir('deduped.metrics')):
    return r"""
        {picard} MarkDuplicates \
        {inputs} \
        O={out_bam} \
        METRICS_FILE={out_metrics} \
        ASSUME_SORTED=True \
        MAX_RECORDS_IN_RAM=1000000 \
        VALIDATION_STRINGENCY=SILENT \
        VERBOSITY=INFO

        {s[opt][samtools]} index {out_bam}
    """.format(inputs=list_to_input(in_bams), s=s,
               picard=picard(),
               **locals())


def fastq_to_sam(rgid, sample_name, library, platform, platform_unit,
                 in_fastq1=find('.fastq', tags=dict(read_pair='1')),
                 in_fastq2=find('.fastq', tags=dict(read_pair='2')),
                 out_bam=out_dir('unaligned.bam')):
    return r"""
        {picard} FastqToSam \
        FASTQ={in_fastq1} \
        FASTQ2={in_fastq2} \
        O={out_bam} \
        SAMPLE_NAME={sample_name} \
        LIBRARY_NAME={library} \
        PLATFORM_UNIT={platform_unit} \
        PLATFORM={platform} \
        READ_GROUP_NAME={rgid}

    """.format(s=s,
               picard=picard(),
               **locals())


def sam_to_fastq_interleave(in_bam=find('bam$'),
                            out_fastq=out_dir('reads.fastq')):
    return r"""
        {picard} SamToFastq \
        I={in_bam} \
        FASTQ={out_fastq}
    """.format(s=s,
               picard=picard(),
               **locals())


def mark_illumina_adapters(mem_req=8 * 1024,
                           in_bam=find('bam'),
                           out_bam=out_dir('unaligned_trimmed.bam'),
                           out_metrics=out_dir('adapter.metrics')):
    return r"""
        {picard} MarkIlluminaAdapters\
        I={in_bam} \
        O={out_bam} \
        METRICS={out_metrics}
    """.format(s=s,
               picard=picard(),
               **locals())

def collect_multiple_metrics(in_bam=find('bam'),
                             out_path=out_dir('metrics/picard'),
                             reference_fasta=s['ref']['reference_fasta']):
    return r"""
      {picard} CollectMultipleMetrics \
      I={in_bam} \
      O={out_dir} \
      R={reference_fasta}
    """.format(picard=picard(),
               **locals())
