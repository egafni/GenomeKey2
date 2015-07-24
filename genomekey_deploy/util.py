from datetime import datetime

from fabric.api import run


def tobool(x):
    if isinstance(x, bool):
        return x
    elif x == 'True':
        return True
    elif x == 'False':
        return False
    else:
        raise ValueError('Bad bool value: %s' % x)


def apt_update(force=False):
    """
    apt update if stale
    :param checkfirst: if False, always update
    """
    if force:
        run('apt-get update -y')
    else:
        r = run('stat -c %y /var/lib/apt/periodic/update-success-stamp')
        datetime_instance = datetime.now() - datetime.strptime(r[:10], "%Y-%m-%d")
        if datetime_instance.days > 7:
            run('apt-get update -y')