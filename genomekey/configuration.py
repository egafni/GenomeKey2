import os

library_path = os.path.dirname(os.path.realpath(__file__))

opj = os.path.join
user_home = os.path.expanduser(os.environ['HOME'])


### Path functions
data_path = '/mnt/data'
root = lambda x: opj(os.path.dirname(library_path), x)
bin = lambda x: opj(root('genomekey/bin'), x)
etc = lambda x: opj(root('etc'), x)
data = lambda x: opj(data_path, x)
opt = lambda x: opj(data_path, 'opt', x)
bundle = lambda x: opj(data('bundle/2.8/b37'), x)


### Read Config
from configparser import ConfigParser, ExtendedInterpolation

conf_path = opj(user_home, '.genomekey', 'genomekey.conf')
conf_path = os.environ.get('GENOMEKEY_CONF', conf_path)
if not os.path.exists(conf_path):
    raise IOError('%s does not exist and is required.  A template config file is available in %s' % (conf_path,
                                                                                                     etc(
                                                                                                         'genomekey.conf')))
settings = ConfigParser(interpolation=ExtendedInterpolation())
settings.read(conf_path)