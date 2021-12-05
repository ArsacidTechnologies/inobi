
import psycopg2
from psycopg2.extensions import quote_ident
import typing as T

from inobi.config import SQL_CONNECTION


from .classes import Message


def add_message(msg: Message) -> Message:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            sql = '''
insert into messages (issuer, type, content, service, "to")
    values (%s, %s, %s, %s, %s)
    returning *
'''
            cursor.execute(sql, (msg.issuer, msg.type, msg.content, msg.service, msg.to))

            return Message._make(cursor.fetchone())


def get_messages(order_by: str = 'register_time',
                 desc: bool = True,
                 limit: int = 20, offset: int = 0,
                 **filter_kwargs) -> T.List[Message]:

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:

            where_clause = ''
            args = ()
            valid_filters = [(k, v) for k, v in filter_kwargs.items() if v is not None]
            if valid_filters:
                where_clause = 'where ' + ' and '.join('{} = %s'.format(quote_ident(k, cursor)) for k, _ in valid_filters)
                args = [v for _, v in valid_filters]

            sql = '''
select * from messages {}
    order by {} {}
    limit {} offset {}
'''.format(where_clause, order_by, 'desc' if desc else 'asc', limit, offset)

            cursor.execute(sql, args)

            return list(map(Message._make, cursor))
