import os

from configparser import ConfigParser


def get_config():
    cp = ConfigParser()
    cp.read([os.path.expanduser('~/.aws/config'),
             os.path.expanduser('~/.aws/credentials')])
    return cp


def set_env_aws_credentials():
    cp = get_config()
    os.environ['AWS_ACCESS_KEY_ID'] = cp['default']['aws_access_key_id']
    os.environ['AWS_SECRET_ACCESS_KEY'] = cp['default']['aws_secret_access_key']