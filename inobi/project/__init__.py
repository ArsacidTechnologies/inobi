

from flask import request
from inobi.utils import getargs, http_ok
from inobi.security import secured, sign

from inobi.utils.converter import converted, Numeric
from typing import Dict, Iterable, Any


from flask import Blueprint

bp = Blueprint('Project', __name__)
route = bp.route


from inobi.utils.project_initializer import database


# Will execute all files in 'sql' directory of project in undefined order (todo: order if None)
# (uncomment to test)
# database.initialize_for_module(name=__name__)

# Creating view before tables will cause exception throwing
# (uncomment to test)
# database.initialize_for_module(name=__name__, execute=['cleanup.sql', 'test_view.sql', 'test.sql', 'test2.sql'])

# Will execute files listed in 'execute' parameter in given order


def on_app_will_run():
    database.initialize_for_module(name=__name__, execute=['cleanup.sql'])

on_app_will_run.is_migration = True


from inobi import add_prerun_hook


add_prerun_hook(on_app_will_run)


from collections import namedtuple


UserData = namedtuple('UserData', 'name last_name sex weight height')


def user_data_converter(d: Dict):
    return UserData(**d)

#
# @app.route('/project/some/api/<int:x>', methods=('GET', 'POST'))
# @secured('test test_admin')
# @converted
# def some_api_handler(x, user_data: user_data_converter, kek: int):
#     """Secured API example"""
#
#     Args = namedtuple('Args', 'x user_data kek')
#     args = Args(x, user_data, kek)
#
#     some_data = args._asdict()
#
#     return HTTP_OK(dict(data=some_data))


@route('/project/test/token', methods=('GET', 'POST'))
def app_test_token():
    """
    Generates token with given data parameters.

    For debug purposes only
    """

    (_data, exp) = getargs(request, 'data', 'exp')
    data = {
        'some': 'value',
        'id': 'test',
        'lel': 'kek'
    }
    data.update(_data or {'no': 'data'})
    return sign(data, ['transport_viewer', 'application_public'], expires_after=10*24*60*60), 200


@route('/access_test/transport_admin')
@secured('transport')
def a():
    return 'ok', 200


# @app.route('/access_test/transport_viewer')
# @secured('transport_viewer')
# def b():
#     return 'ok', 200
#
#
# @app.route('/access_test/transport')
# @secured('transport')
# def c():
#     return 'ok', 200