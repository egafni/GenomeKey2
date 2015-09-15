from ..api import settings as s
import os

def assert_references_exist():
    for k,v in s['ref'].items():
        assert os.path.exists(v),  'Reference file missing! %s = %s' % (k,v)