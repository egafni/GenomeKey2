import os

from . import library_path
from configuration import settings
from genomekey.aws.s3 import run as s3run
from genomekey.aws.s3 import cmd as s3cmd
from .aws.config import set_env_aws_credentials
from aws.s3.cosmos_utils import make_s3_cmd_fxn_wrapper, can_stream, shared_fs_cmd_fxn_wrapper
from .util.parallel import Parallel



class GenomeKey():
    def __init__(self):
        set_env_aws_credentials()
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
        # export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        from cosmos.web.gemon.views import bprint as gemon_bprint
        from cosmos.api import Cosmos
        from flask import Flask
        flask_app = Flask('genomekey', template_folder=os.path.join(library_path, 'web/templates'))

        flask_app.secret_key = '\x16\x89\xf5-\tK`\xf5FY.\xb9\x9c\xb4qX\xfdm\x19\xbd\xdd\xef\xa9\xe2'
        flask_app.register_blueprint(gemon_bprint, url_prefix='/gemon')
        self.flask_app = flask_app
        self.cosmos_app = Cosmos(settings['gk']['database_url'], default_drm=settings['gk']['default_drm'], flask_app=flask_app)
