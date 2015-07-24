__author__ = 'erik'
import os
import itertools as it

from ..tools import gatk


# def split_target_bed_by_chrom(target_bed, output_dir):
#     """
#     Creates a target_bed for each chromosome.  If no targets in a chromosome exist, a bed file will not be
#     created for that chromosome.
#     :param str target_bed: target_bed file
#     :param str output_dir: output_directory
#     :return: a dictionary of chrom -> chrom_target_bed_path (
#     """
#     chrom_to_fh = dict()
#
#     with open(target_bed) as fh:
#         for line in fh:
#             line = line.strip()
#             chrom = line.split("\t")[0]
#             if chrom not in chrom_to_fh:
#                 chrom_to_fh[chrom] = open(os.path.join(output_dir, 'chr%s_targets.bed' % chrom), 'w')
#             print >> chrom_to_fh[chrom], line
#
#     for fh in chrom_to_fh.values():
#         fh.close()
#
#     return {chrom: fh.name for chrom, fh in chrom_to_fh.items()}


# def set_target_bed(tools, chrom_to_targets):
# """
#     Sets each tool's tags to the target_bed that corresponds to its chromosome
#     """
#     for t in tools:
#         t.tags['target_bed'] = chrom_to_targets[str(t.tags['chrom'])]
#         yield t
