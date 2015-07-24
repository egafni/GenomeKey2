# Setup logger
import logging

log = logging.getLogger('GenomeKey')
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('GenomeKey.%(levelname)s: %(asctime)s: %(message)s', "%Y-%m-%d %H:%M:%S"))
log.addHandler(ch)
log.propagate = False

from configuration import settings
import os

library_path = os.path.dirname(os.path.realpath(__file__))

user_home = os.path.expanduser(os.environ['HOME'])

with open(os.path.join(library_path, 'VERSION'), 'r') as fh:
    __version__ = fh.read().strip()

from .aws.s3 import S3Tool as GK_Tool