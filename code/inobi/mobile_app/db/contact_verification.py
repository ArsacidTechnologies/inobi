
import time

import typing as T
import collections as C
import functools as FT


import psycopg2
from psycopg2 import errorcodes

from inobi.config import SQL_CONNECTION

from .exceptions import InobiException

from .classes import VerifiedContact


def insert_verified_contact(contact: str, type: str) -> VerifiedContact:

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            sql = '''
insert into verified_contacts (contact, type) values (%s, %s)
    on conflict (contact) do update set type = excluded.type
    returning *
'''
            cursor.execute(sql, (contact, type))

            contact = VerifiedContact.row(cursor.fetchone())

            return contact


def fetch_contact(contact: str, type: str) -> T.Optional[VerifiedContact]:

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            sql = '''select * from verified_contacts where contact = %s and type = %s'''

            cursor.execute(sql, (contact, type))

            row = cursor.fetchone()

            if row is None:
                return None
            return VerifiedContact.row(row)
