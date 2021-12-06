
from datetime import datetime

import typing as T
import json

from inobi.utils import ntrow, listofnamedtuples, connected

from inobi.exceptions import BaseInobiException

import collections as C


class TONotificationsException(BaseInobiException):
    pass


@ntrow(make_optional=True)
class Notification(C.namedtuple('Notification', 'id organization resolved type domain title content attributes payload register_time')):
    _json_fields = ('attributes', 'payload')

    _noupdate = object()

    @classmethod
    def make_to_update(cls, id: int, to_id: int, values: dict):
        return cls.make([id, to_id, *(values.get(f, Notification._noupdate) for f in cls._fields[2:])])

    @classmethod
    @connected
    def get_all(cls, to_id: int, resolved=False, conn=None) -> listofnamedtuples:
        with conn.cursor() as cursor:
            sql = 'select * from transport_organization_notifications where organization = %s and resolved = %s'
            cursor.execute(sql, (to_id, resolved))
            return listofnamedtuples(map(cls.make, cursor))

    @classmethod
    @connected
    def get_by_id(cls, to_id: int, id: int, conn=None) -> T.Optional['Notification']:
        with conn.cursor() as cursor:
            sql = 'select * from transport_organization_notifications where organization = %s and id = %s'
            cursor.execute(sql, (to_id, id))
            row = cursor.fetchone()
            if row is None:
                return None
            return cls.make(row)

    @classmethod
    @connected
    def add(cls, to_id: int, type: str, domain: str, title: str, content: str, attributes: dict = None, payload: dict = None, resolved=False, conn=None) -> 'Alert':
        attrs = json.dumps(attributes) if attributes is not None else None
        p = json.dumps(payload) if payload is not None else None
        with conn.cursor() as cursor:
            sql = '''
insert into transport_organization_notifications 
(organization, resolved, type, domain, title, content, attributes, payload) 
values (%s, %s, %s, %s, %s, %s, %s, %s)
returning *
'''
            cursor.execute(sql, (to_id, resolved, type, domain, title, content, attrs, p))
            return cls.make(cursor.fetchone())

    @connected
    def resolve(self, conn=None) -> T.Optional['Notification']:
        with conn.cursor() as cursor:
            sql = '''
update transport_organization_notifications
set resolved = true
where organization = %s and id = %s
returning *
'''
            cursor.execute(sql, (self.organization, self.id))
            row = cursor.fetchone()
            if row is None:
                return None
            return self.make(row)

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.register_time)
