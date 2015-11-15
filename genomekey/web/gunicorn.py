"""
Used to launch gunicorn
"""
from genomekey.api import GenomeKey

genomekey = GenomeKey()
genomekey.cosmos_app.configure_flask()
flask = genomekey.flask_app