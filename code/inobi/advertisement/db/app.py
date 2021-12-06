import psycopg2 as pypyodbc
import psycopg2 as pyodbc

from time import time as now

from . import SQL_CONNECTION, DbKey
from . import debug_exception

from collections import namedtuple
from json import loads, dumps


tag = '@db.app:'


class LoginLog(namedtuple('LoginLog', 'id type time payload')):
    def __new__(cls, *args, **kwargs):
        *_args, payload = args
        return super(cls, LoginLog).__new__(cls, *_args, loads(payload))


def log_login(_id, _type, payload):
    connection = pyodbc.connect(SQL_CONNECTION)
    try:
        cursor = connection.cursor()
        try:
            sql = 'INSERT INTO [app_logins] VALUES (?, ?, ?, ?)'

            cursor.execute(sql, (_id, _type, now(), dumps(payload)))

            cursor.commit()
        except Exception as e:
            debug_exception(tag, e)
            raise e
        finally:
            if cursor is not None:
                cursor.close()
    except Exception as e:
        debug_exception(tag, e)
        raise e
    finally:
        if connection is not None:
            connection.close()


# TODO: get logins list

def logins_list():
    return []
