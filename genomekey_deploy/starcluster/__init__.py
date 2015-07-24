def read_config():
    from starcluster.config import StarClusterConfig

    sc_config = StarClusterConfig()
    sc_config.reload()
    return sc_config


def get_aws_env():
    sc_config = read_config()
    from .... import settings as s

    return dict(
        AWS_ACCESS_KEY_ID=sc_config.aws.aws_access_key_id,
        AWS_SECRET_ACCESS_KEY=sc_config.aws.aws_secret_access_key,
        AWS_DEFAULT_REGION=s['aws']['default_region'])