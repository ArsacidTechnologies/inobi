
__production_connprops = dict(
    uid='Avisa',
    pwd='Js100#@!10102301',
    # uid='Inobi',
    # pwd='JS57&%10010102301',
    dsn='sqldatasource'  # configure odbc.ini and odbcinst.ini files in /etc
)

__test_connprops = dict(
    uid='superadmin',
    pwd='SuperHero05',
    server='localhost',
    port=1433,
    driver='ODBC Driver 13 for SQL Server',
    database='inobi'
)

__test_connprops_prod = dict(
    uid='Avisa',
    pwd='Js100#@!10102301',
    server='localhost',
    port=1433,
    driver='ODBC Driver 13 for SQL Server',
    database='test_inobi'
)

__remote_production_connprops = dict(
    uid='Avisa',
    pwd='Js100#@!10102301',
    # uid='Inobi',
    # pwd='JS57&%10010102301',
    dsn='dbserverdsn'
)

__test_connprops2 = dict(
    uid='dev',
    pwd='Qwer1234',
    driver='ODBC Driver 13 for SQL Server',
    server='localhost',
    database='inobi_v2'
)

__the_real_production_props = dict(
    uid='inobi',
    pwd='qO%v8kn8R',
    database='test_inobi',
    server='mssql',
    port=1433,
    driver='ODBC Driver 13 for SQL Server'
)