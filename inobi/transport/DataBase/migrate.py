from .DB import verify_sqlite
from inobi.config import SQL_CONNECTION
from . import tables
import psycopg2
import sqlite3

from . import line_queries as queries

SQLITE_SELECT = '''
SELECT * FROM {};
'''


def migrate(source_db_path, sql_connection=SQL_CONNECTION):
    with psycopg2.connect(sql_connection) as conn:

        valid = verify_sqlite(source_db_path)
        if valid['code'] != 200:
            return valid

        cursor = conn.cursor()
        cursor.execute(queries.refresh)

        res = {}

        lite_conn = sqlite3.connect(source_db_path)
        lite_cursor = lite_conn.cursor()

        getStations = SQLITE_SELECT.format(tables.STATIONS)
        getPlatforms = SQLITE_SELECT.format(tables.PLATFORMS)
        getRoutes = SQLITE_SELECT.format(tables.ROUTES)
        getDirections = SQLITE_SELECT.format(tables.DIRECTIONS)
        getStationPlatforms = SQLITE_SELECT.format(tables.STATION_PLATFORMS)
        getStationRoutes = SQLITE_SELECT.format(tables.STATION_ROUTES)
        getRouteDirections = SQLITE_SELECT.format(tables.ROUTE_DIRECTIONS)
        getDirectionPlatforms = SQLITE_SELECT.format((tables.DIRECTION_PLATFORMS))
        getExcludeRoutes = SQLITE_SELECT.format(tables.EXCLUDE_ROUTES)
        get_break_points = SQLITE_SELECT.format(tables.BREAK_POINTS)
        get_direction_links = SQLITE_SELECT.format(tables.DIRECTION_LINKS)

        lite_cursor.execute(getStations)
        stations = lite_cursor.fetchall()
        res['stations'] = len(stations)
        if len(stations) != 0:
            cursor.executemany(queries.insert_station, stations)

        lite_cursor.execute(getPlatforms)
        platforms = lite_cursor.fetchall()
        res['platforms'] = len(platforms)
        if len(platforms) != 0:
            cursor.executemany(queries.insert_platform, platforms)

        lite_cursor.execute(getRoutes)
        routes = lite_cursor.fetchall()
        res['routes'] = len(routes)
        if len(routes) != 0:
            cursor.executemany(queries.insert_route, routes)

        lite_cursor.execute(getDirections)
        directions = lite_cursor.fetchall()
        res['directions'] = len(directions)
        if len(directions) != 0:
            cursor.executemany(queries.insert_direction, directions)

        lite_cursor.execute(getStationPlatforms)
        station_platforms = lite_cursor.fetchall()
        res['station_platforms'] = len(station_platforms)
        if len(station_platforms) != 0:
            cursor.executemany(queries.insert_con_station_platform, station_platforms)

        lite_cursor.execute(getStationRoutes)
        station_routes = lite_cursor.fetchall()
        res['station_routes'] = len(station_routes)
        if len(station_routes) != 0:
            cursor.executemany(queries.insert_con_station_route, station_routes)

        lite_cursor.execute(getRouteDirections)
        route_directions = lite_cursor.fetchall()
        res['route_directions'] = len(route_directions)
        if len(route_directions) != 0:
            cursor.executemany(queries.insert_con_route_direction, route_directions)

        lite_cursor.execute(getExcludeRoutes)
        exclude_routes = lite_cursor.fetchall()
        res['exclude_routes'] = len(exclude_routes)
        if len(exclude_routes) != 0:
            cursor.executemany(queries.insert_exclude_routes, exclude_routes)

        lite_cursor.execute(getDirectionPlatforms)
        direction_platforms = lite_cursor.fetchall()
        res['direction_platforms'] = len(direction_platforms)
        if len(direction_platforms) != 0:
            cursor.executemany(queries.insert_con_direction_platform, direction_platforms)

        lite_cursor.execute(get_break_points)
        break_points = lite_cursor.fetchall()
        res['break_points'] = len(break_points)
        if len(break_points) != 0:
            cursor.executemany(queries.insert_break_points, break_points)

        lite_cursor.execute(get_direction_links)
        direction_links = lite_cursor.fetchall()
        res['direction_links'] = len(direction_links)
        if len(direction_links) != 0:
            cursor.executemany(queries.insert_direction_links, direction_links)

        lite_conn.close()
        conn.commit()
        return res




