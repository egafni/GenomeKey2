from cosmos.api import find, out_dir
from genomekey.api import can_stream, settings as s, library_path
import os

bin = lambda p: os.path.join(library_path, 'bin', p)


@can_stream(['in_fastq'])
def split_fastq_file(num_chunks, prefix, out_fastqs, in_fastq=find('fastq|fastq.gz')):
    return r"""

        python {b} {in_fastq} {prefix} {num_chunks}

    """.format(s=s,
               b=bin('fastq/split_fastq_file.py'),
               **locals())


def ngsutils_fastq_split(num_chunks, prefix, in_fastq=find('fastq|fastq.gz')):
    """
    Doesn't work with streams :(
    """
    return r"""
        {s[opt][ngsutils]}/fastqutils split {in_fastq} {prefix} {num_chunks} -gz

    """.format(s=s,
               **locals())


# @can_stream(['out_fastq1', 'out_fastq2'])
# cpu_req is so that scratch space doesn't run out.  Need to get streaming to work.  It seems like streaming in is not supported, but streaming out
# could work with named pipes or gzipping inside the anonymous pipe?  Spent a few hours, and nothing is working :(
def cut_adapt(core_req=8,
              in_fastq1=find('.fastq', tags=dict(read_pair='1')),
              in_fastq2=find('.fastq', tags=dict(read_pair='2')),
              out_fastq1=out_dir('trimmed_r1.fastq.gz'),
              out_fastq2=out_dir('trimmed_r2.fastq.gz')):
    # out_fastq1='>( gzip > %s)' % out_fastq1
    # out_fastq2='>( gzip > %s)' % out_fastq2
    return r"""

        {s[opt][cutadapt]} \
        -a AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC \
        -A AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT \
        -o {out_fastq1} -p {out_fastq2} \
        {in_fastq1} {in_fastq2}
    """.format(s=s,
               **locals())