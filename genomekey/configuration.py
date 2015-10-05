import os
library_path = os.path.dirname(os.path.realpath(__file__))
opj = os.path.join
root = lambda x: opj(os.path.dirname(library_path), x)
etc = lambda x: opj(root('etc'), x)
# bin = lambda x: opj(root('genomekey/bin'), x)

settings = dict()

def load_settings(conf_path=etc( 'genomekey.conf')):
    global settings
    user_home = os.path.expanduser(os.environ['HOME'])


    ### Path functions


    ### Read Config
    from configparser import ConfigParser, ExtendedInterpolation
    assert os.path.exists(conf_path), '%s does not exist' % conf_path

    settings = ConfigParser(interpolation=ExtendedInterpolation())
    settings.read(conf_path)
    return settings

load_settings()

