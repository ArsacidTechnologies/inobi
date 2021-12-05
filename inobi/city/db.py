
import json, sqlite3

import psycopg2

from inobi import config, utils

import typing as T, collections as C


from .models import *

_get_conn = lambda: psycopg2.connect(config.SQL_CONNECTION)


def get_cities() -> utils.listofnamedtuples:

    with _get_conn() as conn:
        with conn.cursor() as cursor:
            sql = 'select * from cities'
            cursor.execute(sql)
            return utils.listofnamedtuples(map(City.make, cursor))


def get_city_by_id(city_id: int) -> T.Optional['City']:

    with _get_conn() as conn:
        with conn.cursor() as cursor:
            sql = 'select * from cities where id = %s'
            cursor.execute(sql, (city_id, ))
            row = cursor.fetchone()
            if row:
                return City.make(row)
            return None


class City(C.namedtuple('City', 'id name lat lng zoom lang country db_version payload')):

    @classmethod
    def make(cls, row: T.Iterable, start_index=0):
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        city = cls._make(row)
        return city._replace(
            country=json.loads(city.country) if city.country is not None else None,
            payload=json.loads(city.payload) if city.payload is not None else None
        )

    def _asdict(self):
        d = super(City, self)._asdict()
        d['location'] = dict(
            lat=d.pop('lat'),
            lng=d.pop('lng'),
            zoom=d.pop('zoom')
        )
        return d

    getall = staticmethod(get_cities)
    get_by_id = staticmethod(get_city_by_id)


def dump_city(db_path: str, city_id: int):
    with _get_conn() as pg_conn:
        with sqlite3.connect(db_path) as conn:
            _init_dump(conn)
            _dump_rows(pg_conn, conn, city_id)


def _dump_city(dst_conn: sqlite3.Connection, city_id: int):
    _init_dump(dst_conn)
    with _get_conn() as pg_conn:
        _dump_rows(pg_conn, dst_conn, city_id)


def _init_dump(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.executescript(SQL.INIT_DUMP_SCRIPT)


def _dump_rows(src_conn, conn: sqlite3.Connection, city_id):
    with src_conn.cursor() as src_cursor:

        cursor = conn.cursor()

        migrations = [
            (SQL.Select.ROUTES_OF_CITY, (city_id, ), SQL.Insert.ROUTE),
            (SQL.Select.ROUTE_DIRECTIONS_OF_CITY, (city_id, ), SQL.Insert.ROUTE_DIRECTION),
            (SQL.Select.DIRECTIONS_OF_CITY, (city_id, ), SQL.Insert.DIRECTION),
            (SQL.Select.DIRECTION_PLATFORMS_OF_CITY, (city_id, ), SQL.Insert.DIRECTION_PLATFORM),
            (SQL.Select.PLATFORMS_OF_CITY, (city_id, ), SQL.Insert.PLATFORM),
            (SQL.Select.EXCLUDE_ROUTES, None, SQL.Insert.EXCLUDE_ROUTE),
            (SQL.Select.STATIONS_PLATFORMS_OF_CITY, (city_id, ), SQL.Insert.STATION_PLATFORM),
            (SQL.Select.STATIONS_OF_CITY, (city_id, ), SQL.Insert.STATION),
            (SQL.Select.STATIONS_ROUTES_OF_CITY, (city_id, ), SQL.Insert.STATION_ROUTE),
            (SQL.Select.BREAKPOINTS, None, SQL.Insert.BREAKPOINT),
            (SQL.Select.DIRECTION_LINKS_OF_CITY, (city_id, ), SQL.Insert.DIRECTION_LINK)
        ]

        for select_stmt, args_in_select, insert_stmt in migrations:
            src_cursor.execute(select_stmt, args_in_select)
            for row in src_cursor:
                cursor.execute(insert_stmt, row)


def apply_direction_links(db_path: str, city_id: int):
    with sqlite3.connect(db_path) as conn:
        with _get_conn() as pgconn:
            pgcursor = pgconn.cursor()

            pgcursor.execute(SQL.Delete.DIRECTION_LINK_OF_CITY, (city_id, ))

            rows = conn.execute(SQL.Select.DIRECTION_LINKS)
            pgcursor.executemany(SQL.Insert.DIRECTION_LINK_PG, rows)

            pgcursor.execute(SQL.Update.INCR_DB_VERSION_OF_CITY, (city_id, ))

            (new_version, ) = pgcursor.fetchone()
            import os
            from . import config
            try:
                os.remove(config.CITY_DB_TEMPLATE.format(city_id=city_id, data_version=new_version))
            except FileNotFoundError:
                pass


class SQL:

    class Update:

        INCR_DB_VERSION_OF_CITY = '''
update cities 
    set db_version = db_version + 1
    where id = %s
    returning db_version
'''

    class Select:

        ROUTES_OF_CITY = '''
select distinct r.* from routes r
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''

        ROUTE_DIRECTIONS_OF_CITY = '''
select distinct rd.* from route_directions rd
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''

        DIRECTIONS_OF_CITY = '''
select distinct d.* from directions d
    inner join route_directions rd on rd.entry_id = d.id
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        DIRECTION_PLATFORMS_OF_CITY = '''
select distinct dp.* from direction_platforms dp
    inner join directions d on dp.id = d.id
    inner join route_directions rd on rd.entry_id = d.id
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        PLATFORMS_OF_CITY = '''
select distinct p.* from platforms p
    inner join direction_platforms dp on dp.entry_id = p.id
    inner join directions d on dp.id = d.id
    inner join route_directions rd on rd.entry_id = d.id
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        EXCLUDE_ROUTES_OF_CITY = '''
select distinct er.* from exclude_routes as er
    inner join routes as r on r.id = er.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        EXCLUDE_ROUTES = 'select * from exclude_routes'

        STATIONS_PLATFORMS_OF_CITY = '''
select distinct sp.* from station_platforms sp
    inner join platforms p on sp.entry_id = p.id
    inner join direction_platforms dp on dp.entry_id = p.id
    inner join directions d on dp.id = d.id
    inner join route_directions rd on rd.entry_id = d.id
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        STATIONS_OF_CITY = '''
select distinct s.* from stations s
    inner join station_platforms sp on sp.id = s.id
    inner join platforms p on sp.entry_id = p.id
    inner join direction_platforms dp on dp.entry_id = p.id
    inner join directions d on dp.id = d.id
    inner join route_directions rd on rd.entry_id = d.id
    inner join routes r on rd.id = r.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        STATIONS_ROUTES_OF_CITY = '''
select distinct s.id, 0::int, r.id from stations s 
    inner join station_platforms sp on sp.id = s.id 
    inner join platforms p on p.id = sp.entry_id 
    inner join direction_platforms dp on dp.entry_id = p.id 
    inner join directions d on d.id = dp.id 
    inner join route_directions rd on rd.entry_id = d.id 
    inner join routes r on r.id = rd.id
    inner join transport_organization_lines tol on tol.line = r.id
    inner join transport_organizations "to" on tol.organization = "to".id
    inner join cities c on "to".city = c.id
    where c.id = %s
'''
        DIRECTION_LINKS_OF_CITY = '''
with res as (
    select rd.entry_id from route_directions rd
        inner join routes r on r.id = rd.id
        inner join transport_organization_lines tol on tol.line = r.id
        inner join transport_organizations "to" on tol.organization = "to".id
        inner join cities c on "to".city = c.id
        where c.id = %s
    )
    select distinct * from direction_links 
        where dfrom in (select * from res) 
            and dto in (select * from res)
'''
        DIRECTION_LINKS = 'select * from direction_links'

        BREAKPOINTS = 'select * from breakpoints'

    class Insert:

        _insert = lambda tbl, values, placeholder='?': 'insert into {} values ({})'.format(tbl, ', '.join(placeholder for _ in range(values)))
        LINK_ROW_TEMPLATE = _insert('{}', 3)
        _insert_link_row = lambda rel, _tpl=LINK_ROW_TEMPLATE: _tpl.format(rel)

        ROUTE = _insert('routes', 5)
        ROUTE_DIRECTION = _insert_link_row('route_directions')
        DIRECTION = _insert('directions', 3)
        DIRECTION_PLATFORM = _insert_link_row('direction_platforms')
        PLATFORM = _insert('platforms', 3)
        STATION_PLATFORM = _insert_link_row('station_platforms')
        STATION = _insert('stations', 3)
        EXCLUDE_ROUTE = _insert('exclude_routes', 1)
        STATION_ROUTE = _insert_link_row('station_routes')

        DIRECTION_LINK = _insert('direction_links', 7)
        BREAKPOINT = _insert('breakpoints', 2)

        DIRECTION_LINK_PG = _insert('direction_links', 7, '%s')

    class Delete:

        DIRECTION_LINK_OF_CITY = '''
delete from direction_links dl
    using directions d
        inner join route_directions rd on rd.entry_id = d.id 
        inner join routes r on r.id = rd.id
        inner join transport_organization_lines tol on tol.line = r.id
        inner join transport_organizations "to" on tol.organization = "to".id
        inner join cities c on "to".city = c.id and c.id = %s 
    where d.id = dl.dfrom or d.id = dl.dto
'''


    INIT_DUMP_SCRIPT = '''
CREATE TABLE stations(
    id INTEGER PRIMARY KEY,
    name nvarchar,
    full_name nvarchar
);
        
CREATE TABLE routes(
    id INTEGER PRIMARY KEY,
    type nvarchar,
    name nvarchar,
    from_name nvarchar,
    to_name nvarchar
);

CREATE TABLE directions(
    id INTEGER PRIMARY KEY,
    type nvarchar,
    line nvarchar
);

CREATE TABLE direction_platforms(
    id INT,
    pos INT,
    entry_id INT,
    FOREIGN KEY (id) REFERENCES directions(id),
    FOREIGN KEY (entry_id) REFERENCES platforms(id)
);

CREATE TABLE platforms(
    id INTEGER PRIMARY KEY,
    lat REAL,
    lng REAL
);

CREATE TABLE station_platforms(
    id INT,
    pos INT,
    entry_id INT,
    FOREIGN KEY(id) REFERENCES stations(id),
    FOREIGN KEY(entry_id) REFERENCES platforms(id)
);

CREATE TABLE station_routes(
    id INT,
    pos INT,
    entry_id INT,
    FOREIGN KEY(id) REFERENCES stations(id),
    FOREIGN KEY(entry_id) REFERENCES routes(id)
);

CREATE TABLE route_directions(
    id INT,
    pos INT,
    entry_id INT,
    FOREIGN KEY (id) REFERENCES routes(id),
    FOREIGN KEY (entry_id) REFERENCES directions(id)
);

CREATE TABLE exclude_routes(
    id integer primary key
);

CREATE TABLE direction_links (
    dfrom int, 
    dto int, 
    type int, 
    pfrom int, 
    pfromi int, 
    pto int, 
    ptoi int, 
    primary key(dfrom, dto, type)
);

CREATE VIEW user_routes_v2 AS 
    SELECT r.* FROM routes r
        LEFT JOIN exclude_routes er
            ON er.id = r.id
        WHERE er.id IS null;
        
CREATE VIEW user_routes AS
    SELECT * FROM user_routes_v2
        WHERE name = cast(name as integer);
        
create table if not exists breakpoints( 
    id int, 
    entry_id int 
); 
'''