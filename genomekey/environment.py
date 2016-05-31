import os
from configparser import ConfigParser, ExtendedInterpolation
from cosmos.api import default_get_submit_args
from functools import partial
library_path = os.path.dirname(os.path.realpath(__file__))
opj = os.path.join

_environment = None


class GlobalEnvironment():
    def __init__(self, config_path, reference_version):
        assert os.path.exists(config_path), '%s does not exist' % config_path
        assert reference_version in ['hg38', 'b37'], 'bad reference_version: %s' % reference_version
        self.config_path = config_path
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        self.config.read(config_path)
        self.config.add_section('ref')
        for k, v in self.config['ref_%s' % reference_version].iteritems():
            self.config.set('ref', k, v)

        assert len(self.config['ref'].items()) > 1
        # set_env_aws_credentials()


        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
        # export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        from cosmos.web.gemon.views import bprint as gemon_bprint
        from cosmos.api import Cosmos, default_get_submit_args
        from functools import partial
        from flask import Flask

        flask_app = Flask('genomekey', template_folder=os.path.join(library_path, 'web/templates'))

        flask_app.secret_key = '\x16\x89\xf5-\tK`\xf5FY.\xb9\x9c\xb4qX\xfdm\x19\xbd\xdd\xef\xa9\xe2'
        flask_app.register_blueprint(gemon_bprint, url_prefix='/gemon')
        self.flask_app = flask_app
        self.cosmos_app = Cosmos(self.config['gk']['database_url'], default_drm=self.config['gk']['default_drm'], flask_app=flask_app,
                                 get_submit_args=partial(default_get_submit_args, parallel_env='orte'))




def initialize(config_path,
               reference_version='hg38'):
    global _environment
    assert _environment is None, 'Already initialized!'

    _environment = GlobalEnvironment(config_path, reference_version)
    return _environment


def get_env():
    global _environment
    if _environment is None:
        raise Exception, 'Environment has not been configured'

    return _environment