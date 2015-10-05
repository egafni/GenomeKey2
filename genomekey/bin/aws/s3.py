"""
Light wrapper to aws s3 cp.  Provides a way to cp multiple files in parallel, print output messages, and return a proper error code.
"""
from concurrent import futures
import time
import itertools as it




if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    sps = p.add_subparsers()
    sp = sps.add_parser('cp')
    sp.add_argument('froms')
    sp.add_argument('tos')
    args = p.parse_args()
    cp(**vars(args))