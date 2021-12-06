
from flask import Blueprint
from functools import partial


from inobi import add_prerun_hook

# mobile_app configs
from .config import PREFIX


bp = Blueprint('App', __name__)


def route(rule, *args, **kwargs):
    return bp.route(rule, *args, **kwargs)


route = partial(route, methods=('GET', 'POST'))


from inobi.utils.project_initializer import database


def on_app_run():
    database.initialize_module()


on_app_run.is_migration = True
add_prerun_hook(on_app_run)

from .views import *

