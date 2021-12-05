
from flask import Blueprint

from inobi import add_prerun_hook
from inobi.utils.project_initializer import database


bp = Blueprint('Debug', __name__)


def on_app_run():
    database.initialize_module()
on_app_run.is_migration = True


add_prerun_hook(on_app_run)


from . import views

