import os

library_path = os.path.dirname(os.path.realpath(__file__))
opj = os.path.join

settings = None


def initialize(config_path=opj(library_path, 'etc/genomekey.conf'),
               reference_version='hg38'):
    assert reference_version in ['hg38', 'b37']
    global settings

    assert settings is None, 'Already initialized!'

    user_home = os.path.expanduser(os.environ['HOME'])


    ### Path functions


    ### Read Config
    from configparser import ConfigParser, ExtendedInterpolation

    assert os.path.exists(config_path), '%s does not exist' % config_path

    settings = ConfigParser(interpolation=ExtendedInterpolation())
    settings.read(config_path)

    settings['ref'] = settings[reference_version]

    return settings
