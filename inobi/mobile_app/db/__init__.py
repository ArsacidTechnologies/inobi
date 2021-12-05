
import typing as T
import json

import psycopg2

from time import time as now

from inobi.config import SQL_CONNECTION

from .classes import LoginLog, AppUser

from validate_email import validate_email


tag = "@{}:".format(__name__)


from .exceptions import InobiException


_UserId = str
# def log_login(social_id, social_type, payload) -> T.Tuple[_UserId, T.Optional[T.Dict]]:
#
#     with psycopg2.connect(SQL_CONNECTION) as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             '''
#             INSERT INTO app_logins (
#                 social_id,
#                 social_type,
#                 time,
#                 payload
#             )
#             VALUES (%s, %s, %s, %s)
#             RETURNING id
#             ''',
#             (social_id, social_type, now(), json.dumps(payload))
#         )
#         (id_, ) = cursor.fetchone()
#         cursor.execute(
#             '''
#             select * from app_users where social_id = %s and social_type = %s
#             ''', (social_id, social_type)
#         )
#         registered_user = cursor.fetchone()
#         if registered_user is not None:
#             registered_user = AppUser._make(registered_user)._asdict()
#         return id_, registered_user
#
#
# def register_user(name, email, birthday, payload, social_id, social_type, social_payload) -> T.Tuple[str, dict]:
#
#     with psycopg2.connect(SQL_CONNECTION) as conn:
#
#         cursor = conn.cursor()
#         cursor.execute(
#             '''
#             INSERT INTO app_logins (
#                 social_id,
#                 social_type,
#                 time,
#                 payload
#             )
#             VALUES (%s, %s, %s, %s)
#             RETURNING id
#             ''',
#             (social_id, social_type, now(), json.dumps(payload))
#         )
#         (login_id,) = cursor.fetchone()
#
#         sql, values = '''
#             INSERT INTO app_users (
#                 last_login,
#                 register_time,
#
#                 name,
#                 email,
#                 birthday,
#                 payload,
#
#                 social_type,
#                 social_id,
#                 social_payload
#             )
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#             RETURNING * /*id, register_time, last_login, social_type, social_id, social_payload,
#                       name, contact, birthday, payload*/
#
#             ''', (login_id, now(), name, email, birthday, json.dumps(payload), social_type, social_id, json.dumps(social_payload))
#
#         try:
#             cursor = conn.cursor()
#             cursor.execute(sql, values)
#
#         except psycopg2.IntegrityError as e:
#             if e.args[0] == '23000':
#                 raise InobiException('User Already Registered')
#             else:
#                 raise
#
#         user = AppUser._make(cursor.fetchone())
#         conn.commit()
#         return login_id, user._asdict()





##############################
# BACKWARD COMPATIBLE v2 API #
##############################


import functools as FT

from datetime import datetime

from psycopg2 import errorcodes
from .user import User, SocialUser, fetch_user_by_social, register_user as _register_user_v2

from .user import Transport, TransportOrganization


LegacyUser = T.Tuple[_UserId, T.Dict]


def logged(f):
    @FT.wraps(f)
    def wrapper(*args, **kwargs):
        print(wrapper.__name__, 'called with args:', args, 'and kwargs:', kwargs)
        r = f(*args, **kwargs)
        print(wrapper.__name__, 'returned', r)
        return r
    return wrapper


# @logged
def _transform_to_legacy_user(user: User, social_user: SocialUser,
                              transport: T.Optional[Transport] = None,
                              transport_organization: T.Optional[TransportOrganization] = None
                              ) -> LegacyUser:
    lu = user._asdict()
    # lu['social_user'] = social_user._asdict()

    lu['social_payload'] = social_user.payload
    lu['contact'] = user.email
    lu['birthday'] = datetime.fromtimestamp(user.birthday).strftime('%d/%m/%Y') if user.birthday else None

    lu['transport'] = transport._asdict() if transport is not None else None
    lu['transport_organization'] = transport_organization._asdict() if transport_organization is not None else None

    return None, lu


def log_login(social_id, social_type, payload) -> LegacyUser:

    try:
        user, social_user, transport, transport_organization, city, *_ = fetch_user_by_social(social_type, social_id)
    except InobiException:
        return None, None

    return _transform_to_legacy_user(user, social_user)


from ..error_codes import USER_ALREADY_EXISTS


def register_user(name, email, phone, birthday, payload,
                  social_id, social_type, social_payload) -> LegacyUser:

    if not isinstance(birthday, (int, float)) and birthday is not None:
        birthday = datetime.strptime(birthday, '%d/%m/%Y').timestamp()

    try:
        u, su, l = _register_user_v2(
            name=name,
            email=email,
            phone=(phone or (payload or {}).get('phone') or None),
            birthday=birthday,
            payload=payload,
            username=None,
            pwd=None,
            social_id=social_id,
            social_type=social_type,
            social_payload=social_payload,
            soft=True,
            verify_contact=False
        )
    except InobiException:
        raise InobiException('User Already Registered', USER_ALREADY_EXISTS)
    else:
        return _transform_to_legacy_user(user=u, social_user=su)

#     with psycopg2.connect(SQL_CONNECTION) as conn:
#         with conn.cursor() as cursor:
#
#             sql = '''
# insert into t_social_users (type, sid, payload)
#     values (%s, %s, %s)
#     on conflict (type, sid) do update set payload = excluded.payload
#     returning *
# '''
#             try:
#                 cursor.execute(sql, (social_type, social_id, json.dumps(social_payload)))
#             except psycopg2.IntegrityError as e:
#                 if errorcodes.lookup(e.pgcode) == 'UNIQUE_VIOLATION':
#                     raise InobiException('User Already Registered')
#                 else:
#                     raise
#
#             row = cursor.fetchone()
#             social_user = SocialUser.make(row)
#
#             sql = '''
# insert into t_users (name, email, phone, birthday, payload)
#     values (%s, %s, %s, %s, %s)
#     on conflict (email) do update set phone = excluded.phone
#     returning *
# '''
#             if not isinstance(birthday, (int, float)):
#                 from datetime import datetime
#                 birthday = datetime.strptime(birthday, '%d/%m/%Y').timestamp()
#             cursor.execute(sql, (name, email, (payload or {}).get('phone'), birthday, json.dumps(payload)))
#
#             row = cursor.fetchone()
#             user = User.make(row)
#
#             sql = '''
# insert into t_user_logins ("login", "user")
#     values (%s, %s)
#     returning *
# '''
#             try:
#                 cursor.execute(sql, (social_user.id, user.id, 'social_user'))
#             except psycopg2.IntegrityError as e:
#                 if errorcodes.lookup(e.pgcode) == 'UNIQUE_VIOLATION':
#                     raise InobiException('User Already Registered')
#                 else:
#                     raise
#
#             return _transform_to_legacy_user(user, social_user)
