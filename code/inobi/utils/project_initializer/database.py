
import typing as T
import os, sys

import psycopg2

import inspect


from inobi import config


tag = "@{}:".format('db_project_initializer')


def initialize_module(execute: T.List[str] = None,
                      db_connection=None,
                      db_name: str = None,
                      sqls_dirname: str = 'sql',
                      sql_file_extension: str = 'sql'):
    """For project in Inobi initialization"""
    frame = inspect.currentframe().f_back
    return initialize_for_module(name=frame.f_globals['__name__'])


def initialize_for_module(name: str = None,
                          filename: str = None,
                          execute: T.List[str] = None,
                          db_connection=None,
                          db_name: str = None,
                          sqls_dirname: str = 'sql',
                          sql_file_extension: str = 'sql'
                          ):
    """For project in Inobi initialization"""

    if db_name is None:
        db_name = config.CONNECTION_PROPS['dbname']

    clean_connection = False
    if db_connection is None:

        clean_connection = True
        db_connection = psycopg2.connect(config.SQL_CONNECTION)


    md = None
    if name:
        try:
            md = os.path.dirname(sys.modules[name].__file__)
        except KeyError:
            raise Exception('No module named {}'.format(name))

    elif filename:
        md = os.path.dirname(filename)

    else:
        raise Exception('To initialize module need to pass its name or file')

    sqls_dir = os.path.join(md, sqls_dirname)

    c = db_connection.cursor()

    _f_ext = '.' + sql_file_extension
    _f_ext_u = _f_ext + '.unformatted'

    all_sqls = None
    if execute is None:
        all_sqls = [sql for sql in os.listdir(sqls_dir) if sql.endswith(_f_ext) or sql.endswith(_f_ext_u)]
    else:
        all_sqls = sorted((sql for sql in os.listdir(sqls_dir) if sql in execute), key=lambda x: execute.index(x))

    for sql_fn in all_sqls:

        sql_first_name = sql_fn.split('.')[0]

        full_sql_fn = os.path.join(sqls_dir, sql_fn)

        with open(full_sql_fn, 'rb') as f:
            script = f.read().decode()

        if sql_fn.endswith(_f_ext_u):
            script = script.format(table_name=sql_first_name)

        try:
            c.execute(script)
        except psycopg2.ProgrammingError as e:
            raise Exception("Executing {} (module: {}) failed with:\n\t{}: {}".format(sql_fn, name, type(e).__name__, e))

    db_connection.commit()

    if clean_connection:
        db_connection.close()

    print(tag, '({}) finished'.format(name))
