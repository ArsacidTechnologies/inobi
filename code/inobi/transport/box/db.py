
import psycopg2
import time
import typing as T
import functools as F
import collections as C


from inobi.config import SQL_CONNECTION

from inobi.exceptions import BaseInobiException

from .. import error_codes


class InobiException(BaseInobiException):
    pass


class BoxUpdate(C.namedtuple('BoxUpdate', 'id, previous_version version time lat lng')):
    pass



_T = T.NewType('_T', T.Any)


def get_box_setting(key: str, mapper: T.Callable[[str], _T] = None, typed_to: _T = None) -> T.Optional[_T]:

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        sql = 'select * from box_settings where key = %s'

        cursor.execute(sql, (key,))

        row = cursor.fetchone()
        if row is None:
            return None

        (_, value) = row

        if mapper or typed_to:
            return (mapper or typed_to)(value)

        return value


def set_box_setting(key: str, value):

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        cursor.execute('select value from box_settings where key = %s', (key, ))

        row = cursor.fetchone()
        prev_value = row[0] if row is not None else None

        sql = '''
insert into box_settings 
    values (%s, %s) 
    on conflict (key) do 
        update set value = excluded.value 
    returning *
'''
        cursor.execute(sql, (key, value))

        row = cursor.fetchone()

        assert row == (key, str(value)), "wtf!"

        conn.commit()

        return dict(key=key, value=value, previous_value=prev_value)


get_box_update_version = F.partial(get_box_setting, key='version', mapper=int)


def set_box_update_version(version):
    upd = set_box_setting(key='version', value=version)
    return dict(previous=upd['previous_value'], current=upd['value'])


get_box_internet = F.partial(get_box_setting, key='allow_internet')
set_box_internet = F.partial(set_box_setting, key='allow_internet')


def log_box_update(_id, version, prev_version=None, lat=None, lng=None) -> BoxUpdate:

    if version is None:
        raise InobiException('Version is Null', error_codes.VERSION_IS_NULL)

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        sql = '''
insert into box_updates (id, time, version, previous_version, lat, lng)
    values (%s, %s, %s, %s, %s, %s)
    on conflict (id) do update set
        time = excluded.time,
        version = excluded.version,
        previous_version = excluded.previous_version,
        lat = excluded.lat,
        lng = excluded.lng
    returning *
'''
        cursor.execute(sql, (_id, time.time(), version, prev_version, lat, lng))

        conn.commit()

        box_update = BoxUpdate._make(cursor.fetchone())

        return box_update


def box_updates_list() -> T.List[BoxUpdate]:

    with psycopg2.connect(SQL_CONNECTION) as conn:

        cursor = conn.cursor()

        cursor.execute('select * from box_updates order by time desc')

        return [BoxUpdate._make(row) for row in cursor]
