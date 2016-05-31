import os
from genomekey.api import get_env

def assert_references_exist():
    s = get_env().config
    for k,v in s['ref'].items():
        assert os.path.exists(v),  'Reference file missing! %s = %s' % (k,v)