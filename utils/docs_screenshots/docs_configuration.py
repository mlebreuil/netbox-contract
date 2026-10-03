"""
NetBox configuration for the documentation screenshots: the development configuration with its own database and
Redis databases, so the screenshots never touch the development data, and only this plugin enabled.
"""
import copy
import os

from netbox import configuration as _base
from netbox.configuration import *  # noqa: F401,F403

DATABASES = copy.deepcopy(_base.DATABASES)
DATABASES['default']['NAME'] = os.environ.get('DOCS_DB_NAME', 'netbox_docs')

REDIS = copy.deepcopy(_base.REDIS)
REDIS['tasks']['DATABASE'] = int(os.environ.get('DOCS_REDIS_TASKS_DB', 4))
REDIS['caching']['DATABASE'] = int(os.environ.get('DOCS_REDIS_CACHING_DB', 5))

# No debug toolbar in the screenshots; static files are served by `runserver --insecure`
DEBUG = False
PLUGINS = ['netbox_contract']
PLUGINS_CONFIG = {'netbox_contract': {'top_level_menu': True}}
