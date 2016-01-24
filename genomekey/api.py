import os

from . import library_path
from configuration import settings
from genomekey.aws.s3 import run as s3run
from genomekey.aws.s3 import cmd as s3cmd
from .aws.config import set_env_aws_credentials
from aws.s3.cosmos_utils import make_s3_cmd_fxn_wrapper, can_stream, shared_fs_cmd_fxn_wrapper
from .util.parallel import Parallel

def get_submit_args(task, default_queue=None, parallel_env='orte'):
    """
    Default method for determining the extra arguments to pass to the DRM.
    For example, returning `"-n 3" if` `task.drm == "lsf"` would caused all jobs
    to be submitted with `bsub -n 3`.

    :param cosmos.Task task: The Task being submitted.
    :param default_queue: The default queue.
    :rtype: str
    """
    drm = task.drm or default_queue
    default_job_priority = None
    use_mem_req = False
    use_time_req = False

    cpu_req = task.cpu_req
    mem_req = task.mem_req if use_mem_req else None
    time_req = task.time_req if use_time_req else None

    jobname = '%s_task(%s)' % (task.stage.name, task.id)
    queue = ' -q %s' % default_queue if default_queue else ''
    priority = ' -p %s' % default_job_priority if default_job_priority else ''


    if drm in ['lsf', 'drmaa:lsf']:
        rusage = '-R "rusage[mem={mem}] ' if mem_req and use_mem_req else ''
        time = ' -W 0:{0}'.format(task.time_req) if task.time_req else ''
        return '-R "{rusage}span[hosts=1]" -n {task.cpu_req}{time}{queue} -J "{jobname}"'.format(**locals())

    elif drm in ['ge', 'drmaa:ge']:
        h_vmem = int(math.ceil(mem_req / float(cpu_req))) if mem_req else None

        def g():
            resource_reqs = dict(h_vmem=h_vmem, slots=cpu_req, time_req=time_req)
            for k, v in resource_reqs.items():
                if v is not None:
                    yield '%s=%s' % (k, v)

        resource_str = ','.join(g())

        return '-pe {parallel_env} {cpu_req} -l num_proc={cpu_req} {priority} -N "{jobname}"'.format(resource_str=resource_str, priority=priority,
                                                                               jobname=jobname, cpu_req=cpu_req, parallel_env=parallel_env)
    elif drm == 'local':
        return None
    else:
        raise Exception('DRM not supported: %s' % drm)


class GenomeKey():
    def __init__(self):
        set_env_aws_credentials()
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
        self.cosmos_app = Cosmos(settings['gk']['database_url'], default_drm=settings['gk']['default_drm'], flask_app=flask_app,
                                 get_submit_args=get_submit_args)
