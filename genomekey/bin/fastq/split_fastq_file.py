"""
INCOMPLETE
"""
import gzip
import os
from concurrent import futures
from logging import log
import itertools as it
import sys
import logging as log
from cosmos.util.iterstuff import take
import io

log.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=log.INFO)


def iter_by4(fp):
    for line in fp:
        yield tuple(next(fp) for i in range(4))


def get_split_paths(prefix, num_chunks, gz=True):
    return ['%s%s.fastq%s' % (prefix, chunk, '.gz' if gz else '')
            for chunk in range(1, num_chunks + 1)]


def split_fastq_file(in_fastq, prefix, num_threads, num_chunks):
    out_fps = [open(p, 'w') for p in get_split_paths(prefix, num_chunks, gz=False)]

    log.info('Splitting %s into %s chunks' % (in_fastq, num_chunks))

    with io.open(in_fastq, 'r') as in_fp:
        for i, four_lines in enumerate(iter_by4(in_fp)):
            q, r = divmod(i, num_chunks)
            map(out_fps[r].write, four_lines)

            # if i+1 % 1000 == 0:
            # log.info('Processed %s reads...' % (i + 1))
            #     break

    for out_fp in out_fps:
        out_fp.close()


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('in_fastq')
    p.add_argument('prefix')
    p.add_argument('num_chunks', type=int)
    p.add_argument('--num_threads', default=1)
    split_fastq_file(**vars(p.parse_args()))