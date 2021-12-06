
import time

import typing as T
import collections as C
import functools as FT

import json

import psycopg2
from psycopg2 import errorcodes

from passlib.hash import pbkdf2_sha256

from validate_email import validate_email

from inobi.config import SQL_CONNECTION

from .exceptions import InobiException

from inobi.transport.DataBase.classes import Transport, TransportOrganization

from .. import error_codes

from flask import url_for, current_app as app

from ..config import APP_USER_PICTURES_DIRECTORY, join

import os

from ..utils import valid_iranian_national_id
from ..views.picture import app_user_picture_v1

from inobi.transport.organization.db.update_transport_drivers import update_driver_transport


class _noupdate:
    pass


class User(C.namedtuple('User', 'id register_time email name phone scopes birthday gender national_code payload device_id')):

    noupdate = _noupdate

    @classmethod
    def make(cls, row, start_index=0) -> 'User':
        data = row[start_index:start_index + len(cls._fields)]
        u = cls._make(data)
        return u._replace(
            scopes=json.loads(u.scopes),
            payload=json.loads(u.payload) if u.payload else None
        )

    @classmethod
    def make_from_dict(cls, d: dict):
        return cls(**{k: d.get(k, None) for k in cls._fields})

    @classmethod
    def make_to_update(cls, id, d: dict) -> 'User':
        email = d.get('email', _noupdate)
        if email is not _noupdate and not isinstance(email, str) and not validate_email(email):
            raise InobiException('Email is not Valid', error_codes.EMAIL_IS_NOT_VALID)
        name = d.get('name', _noupdate)
        if name is not _noupdate and not isinstance(name, str) and not len(name) > 2:
            raise InobiException('Name Must be String With Minimum 3 Characters',
                                 error_codes.NAME_IS_NOT_VALID)
        phone = d.get('phone', _noupdate)
        birthday = d.get('birthday', _noupdate)
        if birthday is not _noupdate and not isinstance(birthday, (int, float)):
            raise InobiException('Birthday Must be Numeric Type (int, float)',
                                 error_codes.BIRTHDAY_IS_NOT_VALID)
        gender = d.get('gender', _noupdate)
        if gender is not _noupdate and not isinstance(gender, int) and (not (0 < gender < 3)):
            raise InobiException('Gender Must Be in a valid gender',
                                 error_codes.GENDER_IS_NOT_VALID)
        national_code = d.get('national_code', _noupdate)
        if national_code is not _noupdate and not isinstance(national_code, str) and not valid_iranian_national_id(national_code):
            raise InobiException('National code Must Be a valid iranian national ID (aka str)',
                                 error_codes.NATIONAL_CODE_IS_NOT_VALID)
        payload = d.get('payload', _noupdate)
        if payload is not _noupdate and not isinstance(payload, dict):
            raise InobiException('Payload Must Be Object Type (aka dict)',
                                 error_codes.PAYLOAD_IS_NOT_VALID)
        device_id = d.get('device_id') or d.get('mac', _noupdate)
        return cls(id=id, register_time=_noupdate,
                   email=email, name=name, phone=phone,
                   scopes=_noupdate, birthday=birthday, gender=gender,
                   national_code=national_code, payload=payload,
                   device_id=device_id)

    def update_values(self) -> C.OrderedDict:
        d = C.OrderedDict((k, v) for k, v in super(User, self)._asdict().items() if v is not _noupdate)
        if 'payload' in d and isinstance(d, dict):
            d['payload'] = json.dumps(d['payload'])
        return d

    def _asdict(self, login: 'Login' = None, social_user: 'SocialUser' = None):
        d = super(User, self)._asdict()
        del d['device_id']
        if self.payload and 'picture' in self.payload:
            d['payload']['picture'] = url_for(app_user_picture_v1.__name__,
                                              picture=self.payload['picture'],
                                              _external=True)
        d['login'] = login._asdict() if login else None
        d['social_user'] = social_user._asdict() if social_user else None
        return d

    def remove_picture(self):
        if self.payload and 'picture' in self.payload:
            try:
                os.remove(join(APP_USER_PICTURES_DIRECTORY, self.payload['picture']))
            except FileNotFoundError:
                pass
            return True
        return False


class Login(C.namedtuple('Login', 'id register_time username pwd')):

    LOGIN_KEY = 'login'

    noupdate = _noupdate

    @classmethod
    def make(cls, row, start_index=0) -> 'Login':
        data = row[start_index:start_index + len(cls._fields)]
        return cls._make(data)

    @classmethod
    def make_to_update(cls, d: dict) -> 'Login':
        username = d.get('username', _noupdate)
        if username is not _noupdate and not isinstance(username, str) and not len(username) > 2:
            raise InobiException('Username Must be String With At Least 3 Characters',
                                 error_codes.USERNAME_IS_NOT_VALID)
        pwd = d.get('pwd', _noupdate)
        if pwd is not _noupdate and not isinstance(pwd, str) and not len(pwd) > 5:
            raise InobiException('Password Must be String With At Least 6 Characters',
                                 error_codes.PASSWORD_IS_NOT_VALID)

        pwd = pwd if pwd is _noupdate else pbkdf2_sha256.hash(pwd)

        return cls(id=_noupdate, register_time=_noupdate,
                   username=username, pwd=pwd)

    def update_values(self) -> C.OrderedDict:
        return C.OrderedDict((k, v) for k, v in super(Login, self)._asdict().items() if v is not _noupdate)

    def verify(self, pwd) -> bool:
        return pbkdf2_sha256.verify(pwd, self.pwd)

    def _asdict(self):
        d = super(Login, self)._asdict()
        del d['pwd']
        return d


class SocialUser(C.namedtuple('SocialUser', 'id register_time type sid payload')):

    LOGIN_KEY = 'social_user'

    @classmethod
    def make(cls, row, start_index=0) -> 'SocialUser':
        data = row[start_index:start_index + len(cls._fields)]
        su = cls._make(data)
        return su._replace(
            payload=json.loads(su.payload)
        )


from inobi.city.db import City


class ReturnUser(T.NamedTuple('ReturnUser', [('user', User),
                                             ('login', T.Union[SocialUser, Login]),
                                             ('transport', Transport),
                                             ('transport_organization', TransportOrganization),
                                             ('city', City),
                                             ('is_to_admin', bool),
                                             ('is_driver', bool)
                                             ])):
    def verify(self, pwd) -> bool:
        if isinstance(self.login, Login):
            return self.login.verify(pwd)
        return True


_UL = T.TypeVar('_UL')


def _fetch_user_by_user_login(conn: psycopg2, user_login_type: str,
                              where_clause: str,  args: T.Iterable,
                              user_login_factory_class: T.Generic[_UL],
                              login_alias='l', user_logins_alias='ul'
                              ) -> ReturnUser:

    assert user_login_type in ('social_users', 'logins'), 'Kek'

    sql = '''
select u.*, {login_alias}.*, t.*, "to".*, c.*, toa.organization, tod.organization from users u
    inner join user_logins {user_logins_alias}
        on {user_logins_alias}.user = u.id
    inner join {user_login_type} {login_alias}
        on {user_logins_alias}.login = l.id
    left join transports t
        on u.id = t.driver
    left join transport_organization_admins toa
        on u.id = toa.user
    left join transport_organizations "to"
        on toa.organization = "to".id
    left join cities c
        on "to".city = c.id
    
    left join transport_organization_drivers tod
        on u.id = tod."user"

    where {where_clause}
    '''.format(user_logins_alias=user_logins_alias,
               login_alias=login_alias,
               user_login_type=user_login_type,
               where_clause=where_clause)

    with conn.cursor() as cursor:
        cursor.execute(sql, args)

        row = cursor.fetchone()
        if row is None:
            raise InobiException('No Users Registered With Given Credentials',
                                 error_codes.NO_USER_REGISTERED_WITH_GIVEN_CREDENTIALS)

        user = User.make(row, 0)
        fc = len(User._fields)

        user_login = user_login_factory_class.make(row, fc)
        fc += len(user_login_factory_class._fields)

        transport = Transport.make_from_db_row(row, fc)
        fc += len(Transport._fields)

        transport_organization = TransportOrganization.make_from_db_row(row, fc)
        fc += len(TransportOrganization._fields)

        city = City.make(row, fc)
        fc += len(City._fields)

        is_to_admin = row[fc]
        fc += 1

        is_driver = row[fc]
        # fc += 1

        return ReturnUser(user, user_login, transport, transport_organization, city, is_to_admin, is_driver)


def fetch_user_by_social(type: str, id: str) -> ReturnUser:

    with psycopg2.connect(SQL_CONNECTION) as conn:

        return _fetch_user_by_user_login(
            conn,
            'social_users',
            'l.type = %s and l.sid = %s and ul.type = %s',
            (type, id, 'social_user'),
            SocialUser
        )


def fetch_user_by_login(username, email, phone, device_id=None) -> ReturnUser:
    with psycopg2.connect(SQL_CONNECTION) as conn:

        return_user = _fetch_user_by_user_login(
            conn,
            'logins',
            '(l.username ilike %s or u.email ilike %s or u.phone ilike %s) and ul.type = %s',
            (username, email, phone, 'login'),
            Login
        )

        if device_id is not None and return_user.user.device_id != device_id:
            updated_user = _update_device_id_of_user(conn, device_id, return_user.user)
            return_user = return_user._replace(user=updated_user)

        return return_user


def fetch_user_by_national_code(national_code) -> User:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = 'select * from users where national_code = %s'
            cursor.execute(sql, (national_code,))
            return User.make(cursor.fetchone())


def fetch_user_by_phone(phone) -> User:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = 'select * from users where phone = %s'
            cursor.execute(sql, (phone,))
            return User.make(cursor.fetchone())


def _update_device_id_of_user(conn, device_id, user: User) -> User:
    with conn.cursor() as cursor:

        # free previous device_id if binded to another user
        sql = 'update users set device_id = null where device_id = %s'
        cursor.execute(sql, (device_id, ))

        # bind device_id to given user
        sql = 'update users set device_id = %s where id = %s returning *'
        cursor.execute(sql, (device_id, user.id))
        return User.make(cursor.fetchone())


def fetch_user_by_device_id(device_id) -> ReturnUser:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        return _fetch_user_by_user_login(
            conn,
            'logins',
            'u.device_id = lower(%s) and ul.type = %s',
            (device_id, 'login'),
            Login
        )


def is_registered(phone=None, email=None) -> bool:
    if phone is not None and email is not None:
        raise InobiException('Provide Only Phone or Email Parameters', error_codes.ONLY_EMAIL_OR_PHONE_MUST_PRESENT)
    if phone is None and email is None:
        raise InobiException('Phone Or Email Must Present', error_codes.EMAIL_OR_PHONE_MUST_PRESENT)

    value = phone or email

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = '''
select 1 from users where {} ilike %s
'''.format('phone' if phone else 'email')
            cursor.execute(sql, (value, ))
            return cursor.fetchone() is not None


PreviousLogin = Login


def update_password(password, email=None, phone=None) -> T.Tuple[Login, PreviousLogin]:
    if email is None and phone is None:
        raise InobiException('Email Or Phone Must Present', error_codes.EMAIL_OR_PHONE_MUST_PRESENT)
    contact = email or phone

    pwd = pbkdf2_sha256.hash(password)

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            sql = '''
update logins l
    set pwd = %s
    from logins l_prev
        inner join user_logins ul on ul.login = l_prev.id and ul.type = 'login'
        inner join users u on ul."user" = u.id
    where l.id = l_prev.id and u.{} = %s
    returning l.*, l_prev.*
'''.format('email' if email else 'phone')

            cursor.execute(sql, (pwd, contact))

            row = cursor.fetchone()

            login = Login.make(row)
            prev_login = Login.make(row, start_index=len(Login._fields))

            return login, prev_login


def update_national_code(national_code, email=None, phone=None) -> T.Tuple[Login, PreviousLogin]:
    if email is None and phone is None:
        raise InobiException('Email Or Phone Must Present', error_codes.EMAIL_OR_PHONE_MUST_PRESENT)
    contact = email or phone

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = '''
update users u
    set national_code = %s
    where u.{} = %s
    returning u.natioanl_code
'''.format('email' if email else 'phone')
            cursor.execute(sql, (national_code, contact))
            row = cursor.fetchone()
            return row is not None


def register_user(name, email, phone, birthday, payload,
                  username, pwd, national_code, gender,
                  social_type=None, social_id=None, social_payload=None,
                  soft: bool = False, require_crendentials: bool = True,
                  transport_id: int = None, transport_organization_id: int = None,
                  verify_contact: bool = True,
                  device_id: str = None,
                  available_transport: list = None,
                  issuer: int = None) -> T.Tuple[User, T.Optional[SocialUser], T.Optional[Login]]:

    if require_crendentials and not ((username and pwd) or (social_type and social_id and social_payload)):
        raise InobiException('Credentials Required',
                             error_codes.CREDENTIALS_NOT_PROVIDED)

    with psycopg2.connect(SQL_CONNECTION) as conn:

        login = _register_login(conn,
                                username=username,
                                pwd=pbkdf2_sha256.hash(pwd),
                                soft=soft) \
            if username and pwd \
            else None

        social_user = _register_social_user(conn,
                                            type=social_type,
                                            id=social_id,
                                            payload=social_payload,
                                            soft=soft) \
            if social_type and social_id and social_payload \
            else None

        user = _register_user(conn, name=name, email=email,
                              phone=phone, birthday=birthday, gender=gender,
                              payload=payload, national_code=national_code,
                              soft=soft, verify_contact=verify_contact,
                              device_id=device_id)

        try:
            _link_user_to_login_social_user(conn, user, login, social_user)
        except InobiException:
            if hasattr(app, 'sentry') and app.sentry:
                app.sentry.captureException()

        if transport_organization_id:
            # THIS IS ONLY USED WHEN DRIVER IS SIGNING UP
            # A NORMAL USER CAN'T PASS ORGANIZATION ID AND BIND TO IT
            _bind_to_transport_organization(conn, transport_organization_id, user.id)
        if transport_id:
            if not transport_organization_id:
                raise InobiException('Can Not Bind Transport Without Transport Organization ID',
                                     error_codes.TRANSPORT_ORGANIZATION_REQUIRED_TO_SET_USER_AS_TRANSPORT_DRIVER)
            tr_stuff = dict(transport=transport_id,
                            available_transport=available_transport)
            update_driver_transport(conn=conn, tr_stuff=tr_stuff, driver=user.id, organization=transport_organization_id)

        return user, social_user, login


def _bind_transport(conn, user_id, transport_id, transport_organization_id):
    with conn.cursor() as cursor:
        sql = '''
update transports as t
    set driver = %s 
    from transports as t2
        inner join transport_organization_transports tot
            on tot.transport = t2.id
    where t.id = %s and tot.organization = %s 
    returning t.*
'''
        cursor.execute(sql, (user_id, transport_id, transport_organization_id))
        if not cursor.fetchone():
            raise InobiException('Transport Not Found', error_codes.TRANSPORT_NOT_FOUND)


def _bind_to_transport_organization(conn, to_id, uid):
    with conn.cursor() as cursor:
        sql = '''
insert into transport_organization_drivers (organization, "user") 
    select "to".id, %s as user_id from transport_organizations "to"
        where "to".id = %s
    returning *
'''
        cursor.execute(sql, (uid, to_id))
        if not cursor.fetchone():
            raise InobiException('No Transport Organization With Such ID ({})'.format(to_id),
                                 error_codes.TRANSPORT_ORGANIZATION_NOT_FOUND)


def _unique_violation_handled(msg, error_code):
    def wow(f):
        @FT.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                r = f(*args, **kwargs)
            except psycopg2.IntegrityError as e:
                if errorcodes.lookup(e.pgcode) == 'UNIQUE_VIOLATION':
                    raise InobiException(msg, error_code)
                else:
                    raise e
            else:
                return r
        return wrapper
    return wow


@_unique_violation_handled('Logins already bound to user', error_codes.LOGIN_ALREADY_BOUND_TO_USER)
def _link_user_to_login_social_user(conn, user, login, social_user) -> int:
    links = []
    if login:
        links.append((user.id, login.id, 'login'))
    if social_user:
        links.append((user.id, social_user.id, 'social_user'))

    print(links)
    with conn.cursor() as cursor:
        sql = '''
            insert into user_logins ("user", "login", "type")
            values (%s, %s, %s)
        '''
        cursor.executemany(sql, links)

    return len(links)


@_unique_violation_handled('User Already Exists', error_codes.USER_ALREADY_EXISTS)
def _register_user(conn, name, email, phone, birthday, gender, payload,
                   national_code, soft: bool = False, verify_contact: bool = True,
                   device_id: str = None) -> User:
    with conn.cursor() as cursor:

        if verify_contact:
            # USER MUST BE ADDED INTO verified_contacts BEFORE IT GOES TO BE ADD users
            # USING `check_phone` or `check_email` METHODS IN `v2/verify/phone` or `v2/verify/email`
            sql = 'select 1 from verified_contacts where contact in (%s, %s)'
            cursor.execute(sql, (email, phone))
            if cursor.fetchone() is None:
                raise InobiException('No Verified Contact (email/phone) Provided',
                                     error_codes.NO_VERIFIED_CONTACT_PROVIDED)

        if device_id:
            sql = '''update users set device_id = null where device_id = %s'''
            cursor.execute(sql, (device_id, ))

        sql = '''
insert into users (name, email, phone, birthday, gender ,payload, national_code, device_id) 
    values (%s, %s, %s, %s, %s, %s, %s, %s)
{}      on conflict (email) do update set email = excluded.email
    returning *
'''.format('--' if not soft else '')
        cursor.execute(
            sql,
            (name, email, phone, birthday, gender, json.dumps(payload, ensure_ascii=False), national_code, device_id)
        )

        row = cursor.fetchone()
        user = User.make(row)

        return user


@_unique_violation_handled('Login Already Exists', error_codes.USERNAME_ALREADY_EXISTS)
def _register_login(conn, username, pwd, soft: bool = False) -> Login:
    with conn.cursor() as cursor:

        sql = '''
insert into logins (username, pwd)
    values (%s, %s)
{}    on conflict(username) do update set username = excluded.username
    returning *
'''.format('--' if not soft else '')
        cursor.execute(sql, (username, pwd))

        row = cursor.fetchone()
        login = Login.make(row)

        return login


@_unique_violation_handled('Social User Already Exists', error_codes.SOCIAL_USER_ALREADY_REGISTERED)
def _register_social_user(conn, type, id, payload, soft: bool = False) -> SocialUser:
    with conn.cursor() as cursor:

        sql = '''
insert into social_users (type, sid, payload)
    values (%s, %s, %s)
{}    on conflict(type, sid) do update set payload = excluded.payload
    returning *
'''.format('--' if not soft else '')
        cursor.execute(sql, (type, id, json.dumps(payload, ensure_ascii=False)))

        row = cursor.fetchone()
        social_user = SocialUser.make(row)

        return social_user
