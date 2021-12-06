
from flask import Blueprint

bp = Blueprint('Transport Box', __name__)

from .views import *


from inobi import add_prerun_hook
from inobi.utils.project_initializer import database


migration = lambda: database.initialize_module()
migration.is_migration = True

add_prerun_hook(migration)
