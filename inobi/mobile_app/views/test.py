
from flask import request

from inobi.security import secured
from .. import route

from inobi.utils import logged, http_ok, http_err
from inobi.utils.converter import converted, Modifier

from ..utils import send_email


@route('/v1/test/crack')
@logged()
# @secured('application_inobi')
def app_test_crack():

    import os

    # import pdb
    # pdb.set_trace()

    crack

    return os.path.abspath('.') + " kek", 200


@route('/v1/test/email')
@converted()
def app_test_email(to: Modifier.EMAIL, subject: Modifier.MINIMUM_SIZED_STRING(4),
                msg: str, from_addr: Modifier.EMAIL = None):

    send_email(to, subject, msg, from_address=from_addr)

    return http_ok()


@route('/v1/test/sleep')
@converted
def app_test_sleep_v1():

    import time

    time.sleep(10)

    return http_ok(ip=request.remote_addr)


@route('/v1/test')
# @logged()
@converted
def app_test_v1():

    return http_ok(ip=request.remote_addr)


@route('/v1/test/request')
@converted
def app_test_request_v1():

    d = {
        attr: str(getattr(request, attr, None))
        for attr in 'url base_url scheme url_charset url_root url_rule host_url host script_root path full_path'.split()
    }
    return http_ok(request=d)


@route('/v1/test/delete_user')
@converted
def app_test_delete_user_v1(user_id: int):

    from inobi.config import SQL_CONNECTION
    import psycopg2

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            cursor.execute('select delete_user(%s)', (user_id, ))

            (deleted, ) = cursor.fetchone()

            if deleted:
                return http_ok()
            else:
                return http_err('No user with id', 404)
