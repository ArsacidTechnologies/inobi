
import time, json

import typing as T
import collections as C

import attr

from validate_email import validate_email

from passlib.hash import pbkdf2_sha256

from .exceptions import InobiException


from ..security import LOGIN_HANDLERS, ID_KEYS


class LoginLog(C.namedtuple('LoginLog', 'id social_type social_id time payload')):
    @classmethod
    def fromrow(cls, row: tuple) -> 'LoginLog':
        return cls(*row[:-1], json.loads(row[-1]))


fields_AppUser = 'id last_login register_time social_type social_id ' \
                 'social_payload name contact birthday national_code payload scopes'
class AppUser(C.namedtuple('AppUser', fields_AppUser)):

    @classmethod
    def _make(cls, iterable) -> 'AppUser':
        *some, social_payload, name, contact, birthday, national_code, payload, scopes = iterable
        return cls(*some, json.loads(social_payload),
                   name, contact, birthday, national_code,
                   json.loads(payload), json.loads(scopes))


fields_User = 'id register_time username name email phone scopes birthday national_code pwd social_user payload'
class User(C.namedtuple('User', fields_User)):

    class SocialUser(C.namedtuple('SocialUser', 'id type sid payload')):

        @classmethod
        def make_from_db_row(cls, row) -> 'SocialUser':
            su = cls._make(row)
            return su._replace(payload=json.loads(su.payload))

        @classmethod
        def make_from_view(cls, type: str, token: str) -> 'SocialUser':

            token_data = LOGIN_HANDLERS[type](token, True)

            if not token_data:
                raise InobiException("Social User Not Valid")

            sid = token_data[ID_KEYS[type]]

            return cls(
                id=None,
                type=type,
                sid=sid,
                payload=token_data
            )

        @property
        def asdbrow(self):
            return self._replace(
                payload=json.dumps(self.payload, ensure_ascii=False)
            )

    @classmethod
    def make_from_db_row(cls, row) -> 'User':
        user = cls._make(row)
        return user._replace(
            scopes=json.loads(user.scopes),
            payload=json.loads(user.payload)
        )

    @classmethod
    def make_from_db_row_with_joined_social_user(cls, row) -> 'User':
        l = len(User._fields)
        user = cls.make_from_db_row(row[:l])
        if user.social_user is None:
            return user
        return user._replace(social_user=User.SocialUser.make_from_db_row(row[l:]))

    @classmethod
    def make_from_view(cls, username: str, name: str, email: str, pwd: str,
                       social_user: SocialUser = None, phone: str = None,
                       birthday: float = None, national_code: str = None, payload: dict = None) -> 'User':

        if len(username) < 3:
            raise InobiException("'username' Parameter Must Be At Least 3 Characters Length")

        if not validate_email(email):
            raise InobiException("'email' Parameter Must Be Valid email Address")

        user = User(
            id=None,
            register_time=time.time(),
            username=username,
            name=name,
            email=email,
            phone=phone,
            scopes=None,
            birthday=birthday,
            national_code=national_code,
            pwd=pbkdf2_sha256.hash(pwd),
            social_user=social_user,
            payload=payload or {}
        )

        return user

    @property
    def with_socials_inited(self) -> bool:
        return isinstance(self.social_user, User.SocialUser)

    @property
    def asdbrow(self):
        return self._replace(
            social_user=self.social_user.id if self.with_socials_inited else self.social_user,
            payload=json.dumps(self.payload, ensure_ascii=False)
        )

    @property
    def pwd_hash(self):
        return self.pwd

    def verify(self, pwd) -> bool:
        return pbkdf2_sha256.verify(pwd, self.pwd_hash)

    def _asdict(self) -> dict:
        d = super(User, self)._asdict()
        del d['scopes'], d['pwd']

        if self.with_socials_inited:
            d['social_user'] = d['social_user']._asdict()

        return d


@attr.s
class VerifiedContact:

    id = attr.ib()
    time = attr.ib()
    contact = attr.ib()
    type = attr.ib()

    @classmethod
    def row(cls, row: T.Iterable) -> T.Optional['VerifiedContact']:
        if row is not None:
            return cls(*row)
        return None

    def asdict(self):
        return attr.asdict(self)
