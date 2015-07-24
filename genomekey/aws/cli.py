from configparser import ConfigParser

def get_config():
    cp = ConfigParser()
    cp.read('~/.aws/config')