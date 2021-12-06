

from flask import Blueprint

from inobi.utils.project_initializer import database
from inobi import add_prerun_hook

from . import config

migration = lambda: database.initialize_module()
migration.is_migration = True

add_prerun_hook(migration)


bp = Blueprint(config.NAME, __name__)

from .views import *
