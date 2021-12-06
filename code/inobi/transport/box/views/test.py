
from flask import request

from ... import route

from inobi.utils import http_ok
from inobi.security import secured

from .. import db


@route('/v1/box/test')
@secured('application_admin')
def box_test_v1():

    args = {k: v for k, v in request.args.items() if k not in ('jwt', 'token')}

    if request.method == 'GET':

        results = {key: db.get_box_setting(key) for key in args}

        return http_ok(results=results)

    updates = {key: db.set_box_setting(key, value) for key, value in args.items()}

    return http_ok(updates=updates)
