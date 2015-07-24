from genomekey import settings as s


def get_aws_env():
    return dict(AWS_ACCESS_KEY_ID=s['aws']['aws_access_key_id'],
                AWS_SECRET_ACCESS_KEY=s['aws']['aws_secret_access_key'],
                AWS_DEFAULT_REGION=s['aws']['default_region'])