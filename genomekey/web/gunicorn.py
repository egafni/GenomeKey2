"""
Used to launch gunicorn
"""
from genomekey.api import GenomeKey

genomekey = GenomeKey()
flask = genomekey.flask_app