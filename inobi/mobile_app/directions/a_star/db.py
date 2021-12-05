import sqlite3

from geopy.distance import distance

from ...config import DIRECTIONS_DB_PATH


def _distance(lat1, lng1, lat2, lng2):
    return distance((lat1, lng1), (lat2, lng2)).kilometers


def _init_utils(conn):
    conn.create_function('distance', 4, _distance)
    return conn


def get_connection(path=DIRECTIONS_DB_PATH):
    return _init_utils(sqlite3.connect(path))
