

from inobi import db

import time
from inobi.utils import AsDictMixin
from passlib.hash import pbkdf2_sha256


class User(db.Model, AsDictMixin):
    _asdict_fields = ('birthday', 'gender', 'national_code', 'email', 'id', 'name', 'payload', 'phone', 'register_time')

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    register_time = db.Column(db.Float, nullable=False, default=time.time,
                              server_default=db.func.extract('epoch', db.func.now()))
    email = db.Column(db.String, unique=True, nullable=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=True, unique=True)
    scopes = db.Column(db.String, nullable=False, default='[]', server_default='[]')
    birthday = db.Column(db.Float, nullable=True)
    gender = db.Column(db.SmallInteger, nullable=True)
    national_code = db.Column(db.String, unique=True, nullable=True)
    payload = db.Column(db.String, nullable=False, default='{}', server_default='{}')
    device_id = db.Column(db.String, nullable=True)

    email_or_phone_presents_constraint = db.CheckConstraint('email is not null or phone is not null')
    device_id_lowered_index = db.Index('users_device_id_idx', db.func.lower(device_id))

    __table_args__ = (email_or_phone_presents_constraint, device_id_lowered_index)


class SocialUser(db.Model):

    __tablename__ = 'social_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    register_time = db.Column(db.Float, nullable=False, default=time.time,
                              server_default=db.func.extract('epoch', db.func.now()))
    type = db.Column(db.String, nullable=False)
    sid = db.Column(db.String, nullable=False)
    payload = db.Column(db.String, nullable=False)

    type_sid_unique_constraint = db.UniqueConstraint(type, sid)

    __table_args__ = (type_sid_unique_constraint, )


class Login(db.Model, AsDictMixin):
    _asdict_fields = ('id', 'register_time', 'username')

    __tablename__ = 'logins'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    register_time = db.Column(db.Float, nullable=False, default=time.time,
                              server_default=db.func.extract('epoch', db.func.now()))
    username = db.Column(db.String, nullable=False)
    pwd = db.Column(db.String, nullable=False)

    case_insensitive_username_unique_constraint = db.Index('logins_username_key', db.func.lower(username), unique=True)

    __table_args__ = (case_insensitive_username_unique_constraint, )

    def verify(self, pwd) -> bool:
        return pbkdf2_sha256.verify(pwd, self.pwd)


class UserLogin(db.Model):

    __tablename__ = 'user_logins'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    login = db.Column(db.Integer, nullable=False)
    user = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String, nullable=False)

    login_type_unique_constraint = db.UniqueConstraint(login, type, name='user_logins_type_login_index')

    __table_args__ = (login_type_unique_constraint, )

