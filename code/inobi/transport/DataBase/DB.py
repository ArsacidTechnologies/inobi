import psycopg2
import sqlite3


# def __init__(self, sql_path=None, db_path=None):
#     self.sql_path = sql_path
#     self.db_path = db_path
#
# def create_conn():
#     if self.sql_connection != None:
#         return
#     if self.db_path:
#         try:
#             conn = sqlite3.connect(self.db_path)
#             self.sql_connection = conn
#         except Exception as e:
#             self.sql_connection = None
#             raise ConnectionError('Cannot connect to database', e)
#     else:
#         try:
#             conn = psycopg2.connect(self.sql_path)
#             self.sql_connection = conn
#         except Exception as e:
#             self.sql_connection = None
#             raise ConnectionError('Cannot connect to database', e)
#
# def close_conn(self):
#     if self.sql_connection != None:
#         self.sql_connection.close()
#         self.sql_connection = None
#
# def do(self, query, executemany=False,  params=None, out=False, commit=False):
#     conn = self.sql_connection
#     if not conn:
#         return dict(code=500, message='open connection first')
#     try:
#         cursor = self.sql_connection.cursor()
#         if params:
#             if executemany:
#                 cursor.executemany(query, params)
#             else:
#                 cursor.execute(query, params)
#         else:
#             cursor.execute(query)
#         if out:
#             fetched = cursor.fetchall()
#             if len(fetched) == 0:
#                 data = dict(code=404, message='data not found')
#             else:
#                 data = dict(code=200, data=fetched)
#         else:
#             data = dict(code=200)
#         if commit:
#             conn.commit()
#         cursor.close()
#     except Exception as e:
#         self.close_conn()
#         raise e
#     return data


from .tables import TABLES, CONNECTIONS



# verifying sqlite database to line requirements
def verify_sqlite(db_path):
    all_tables = TABLES + CONNECTIONS
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("select name from sqlite_master where type='table'")
        uploaded_tables = cursor.fetchall()
    except:
        return dict(code=400, message='not sqlite database file')
    conn.close()
    if not uploaded_tables:
        return dict(code=400, message=dict(message='uploaded database error'))
    for table in all_tables:
        if table not in [i[0] for i in uploaded_tables]:
            return dict(code=400, message='{} table is missing'.format(table))
    return dict(code=200)

