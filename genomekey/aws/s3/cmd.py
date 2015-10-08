import re
import os
from genomekey.configuration import settings

opj = os.path.join


def cp(from_, to, chrom=None, recursive=False, quiet=False, only_show_errors=True):
    # todo try switching to gof3r, may be much faster
    if chrom and from_.startswith('s3://') and from_.endswith('.bam'):
        # slice the chrom!
        dirname = os.path.dirname(to)
        return 'mkdir -p {dirname} && ' \
               '{s[opt][samtools]} view -hb {from_} {chrom}: > {to} && ' \
               '{s[opt][samtools]} index {to}'.format(s=settings, **locals())
    else:
        if to.endswith('/') or from_.endswith('/'):
            recursive = True
        return 'aws s3 cp{quiet}{only_show_errors}{recursive} {from_} {to}'.format(
            from_=from_,
            to=to,
            quiet=' --quiet' if quiet else '',
            only_show_errors=' --only-show-errors' if only_show_errors else '',
            recursive=' --recursive' if recursive else ''
        )
        # else:
        # return 'aws s3 cp --quiet %s %s' % (from_, to)


def split_bucket_key(s3_path):
    bucket, key = re.search('s3://(.+?)/(.+)', s3_path).groups()
    return bucket, key


def stream_in(path, md5=False):
    # bucket, key = split_bucket_key(path)
    return '<(aws s3 cp %s -)' % path
    # md5 = '' if md5 else ' --no-md5'
    # return '<({s[opt][gof3r]} get{md5} -b {bucket} -k {key})'.format(s=s, **locals())


def stream_out(path):
    return '>(aws s3 cp - %s)' % path


# def get_inputs(s3_root, input_file_paths):
# """
# Downloads inputs from s3_root into their relative path on the filesystem
#
# ex get_inputs("s3://bucket/folder", "a/b") would download file "b" into "a/b"
# """
#
# def g():
# for path in input_file_paths:
#             yield cp(opj(s3_root, path), path)
#
#     return "\n".join(g())
#
#
# def push_outputs(s3_root, output_file_paths):
#     return "\n".join(cp(path, opj(s3_root, path)) for path in output_file_paths)


# def pull_if_s3(file_paths, local_dir='./'):

#     """
#     Pull from s3 if the path has s3:// in it
#     """
#
#     def check_for_s3(file_path):
#         if file_path.startswith('s3://'):
#             local_path = opj(local_dir, os.path.basename(file_path))
#             return local_path, cp(file_path, local_path) + "\n"
#         else:
#             return file_path, ''
#
#     local_path, s3_pull_cmds = zip(*[check_for_s3(tf) for tf in file_paths])
#     return local_path, ''.join(s3_pull_cmds).strip()
