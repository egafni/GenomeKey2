from distutils.core import setup
from setuptools import find_packages
import os
import re

setup_py_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(setup_py_path, 'genomekey/VERSION'), 'r') as fh:
    __version__ = fh.read().strip()


def find_all(path, reg_expr, inverse=False, remove_prefix=False):
    if not path.endswith('/'):
        path = path + '/'
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            match = re.search(reg_expr, filename) is not None
            if inverse:
                match = not match
            if match:
                out = os.path.join(root, filename)
                if remove_prefix:
                    out = out.replace(path, '')
                yield out


# with open('requirements.in') as fp:
#     install_requires = [line.strip() for line in fp]

install_requires = ['cosmos-wfm']

setup(
    # Metadata
    name="genomekey",
    version=__version__,
    description="NGS pipeline",
    url="",
    author="Erik Gafni",
    author_email="erik_gafni@hms.harvard.edu",
    maintainer="Erik Gafni",
    maintainer_email="erik_gafni@hms.harvard.edu",
    license="MIT",
    install_requires=[
        'recordtype',
	    'cosmos-wfm',
        'configparser',
        'futures',
        'ipdb',
        'twilio',
        'gntp',
        'fabric',
        'awscli'
    ],
    scripts=["bin/genomekey"],
    # Packaging Instructions
    packages=find_packages(),
    include_package_data=True,
    package_data={'genomekey': list(find_all('genomekey/', '.py|.pyc$', True, True))}
)
