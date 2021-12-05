
import functools as FT

from inobi import add_prerun_hook
from .config import PREFIX, NAME


from inobi.utils.project_initializer import database


def on_app_run():
    database.initialize_for_module(name=__name__)


on_app_run.is_migration = True


add_prerun_hook(on_app_run)

from flask import Blueprint

bp = Blueprint(NAME, __name__)


# def route(rule, *args, **kwargs):
#     return app.route(PREFIX+rule, *args, **kwargs)


route = FT.partial(bp.route, methods=('GET', 'POST'))

from .views import *
