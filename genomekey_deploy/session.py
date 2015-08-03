import os

from fabric.api import env, prefix, shell_env

# from genomekey.aws import get_aws_env


# Module globals
# AWS_ENV = get_aws_env()

env.user = 'root'
env.disable_known_hosts = True
env.abort_on_prompts = False

this_files_path = os.path.dirname(os.path.realpath(__file__))

# Helper functions
deploy_etc = lambda p: os.path.join(this_files_path, 'etc', p)
# aws_credentials = lambda: shell_env(**AWS_ENV)
VE = lambda: prefix('source ~/projects/GenomeKey/ve/bin/activate')
