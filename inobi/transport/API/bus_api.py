from inobi.transport.DataBase.bus_db import findBusByMac, getBuses
from inobi.redis import getRedis
from inobi.config import redis_segments as segment
import redis
import time
import pickle
from collections import deque
from inobi.config import SQL_CONNECTION

from math import radians, cos, sin, asin, sqrt, atan2, degrees
from .subscribe_v2 import socket_emit


def getBearing(point1, point2):

    lng1, lat1, lng2, lat2 = map(radians, [point1['lng'], point1['lat'], point2['lng'], point2['lat']])

    dlng = lng2 - lng1
    y = sin(dlng) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlng)
    bearing = degrees(atan2(y, x))
    return round((bearing + 360) % 360, 3)

def updatePing(bus, lat, lng, time, driver=None):
    path = bus.get('path', deque(maxlen=5))
    path.append(dict(lat=lat,
                     lng=lng,
                     time=time))
    bus['bearing'] = getBearing(bus.get('location', dict(lat=0, lng=0)), dict(lat=lat, lng=lng))
    bus['path'] = path
    bus['location'] = dict(lat=lat,
                           lng=lng)
    bus['driver'] = driver
    bus['time'] = time
    return bus

def bus(data):
    _redis = getRedis(db=segment['buses'])
    if _redis['code'] != 200:
        return _redis
    _redis = _redis['data']
    pipe = redis.Redis.pipeline(_redis)
    mac = data['id']
    lat = data['lat']
    lng = data['lng']
    driver = data.get('driver')
    now = time.time()
    line = _redis.hget('lines', mac)

    # not in redis lines
    if not line:
        unknown = _redis.hget('unknown', mac)
        # In redis (unknown)
        if unknown:
            unknown = pickle.loads(unknown)
            bus = updatePing(unknown, lat, lng, now, driver)
            _redis.hset('unknown', mac, pickle.dumps(bus))

            # send data to socket connected clients room = unknown
            bus['path'] = list(bus['path'])
            # subs.socket_emit(bus, sioEvents['subscribe'], room=sioRooms['unknown'])
            socket_emit(bus, unknown=True, only_base=True)
            return dict(message='append to existing unknown', code=200)

        # if not in redis unknown
        sqlBus = findBusByMac(mac)
        if sqlBus['code'] not in (200, 404):
            return sqlBus

        # if bus not found in db
        if sqlBus['code'] == 404:

            bus = updatePing({'mac': mac}, lat, lng, now, driver)
            _redis.hset('unknown', mac, pickle.dumps(bus))

            # send data to socket connected clients room = unknown
            bus['path'] = list(bus['path'])
            # subs.socket_emit(bus, sioEvents['subscribe'], room=sioRooms['unknown'])
            socket_emit(bus, unknown=True)
            return dict(message='created unknown', code=200)

        # if bus found in db
        sqlBus = sqlBus['data'][0]
        bus = updatePing(sqlBus, lat, lng, now, driver)
        pipe.hset('buses', '{}:{}'.format(bus['line_id'], bus['mac']), pickle.dumps(bus))
        pipe.hset('lines', bus['mac'], pickle.dumps(bus['line_id']))
        pipe.execute()

        # send data to socket connected clients
        bus['path'] = list(bus['path'])
        # subs.socket_emit(bus, sioEvents['subscribe'], room=bus['line_id'], type=bus['type'])
        socket_emit(bus, line_id=bus['line_id'], only_base=True)

        return dict(message='took from db', code=200)

    # if bus line in lines (redis)
    line = pickle.loads(line)
    redisBus = _redis.hget('buses', '{}:{}'.format(line, mac))

    # if bus not in redis buses
    if not redisBus:
        sqlBus = findBusByMac(mac)
        if sqlBus['code'] not in (200, 404):
            return sqlBus
        # bus not found in db -> redis unknown
        if sqlBus['code'] == 404:
            bus = updatePing({'mac': mac}, lat, lng, now, driver)
            pipe.hdel('lines', mac)
            pipe.hset('unknown', mac, pickle.dumps(bus))
            pipe.execute()

            # send data to unknown room
            bus['path'] = list(bus['path'])
            # subs.socket_emit(bus, sioEvents['subscribe'], room=sioRooms['unknown'])
            socket_emit(bus, unknown=True)
            return dict(message='from db to unknown', code=200)

        # bus found in db -> redis bus, line, socket
        sqlBus = sqlBus['data'][0]
        sqlBus = updatePing(sqlBus, lat, lng, now, driver)
        pipe.hset('buses', '{}:{}'.format(line, mac), pickle.dumps(sqlBus))
        pipe.hset('lines', sqlBus['mac'], pickle.dumps(sqlBus['line_id']))
        pipe.execute()

        # send data to socket connected clients
        sqlBus['path'] = list(sqlBus['path'])
        # subs.socket_emit(sqlBus, sioEvents['subscribe'], room=sqlBus['line_id'], type=sqlBus['type'])
        socket_emit(sqlBus, line_id=sqlBus['line_id'], only_base=True)
        return dict(message='from db to subscribe', code=200)
    # bus in redis buses
    jBus = pickle.loads(redisBus)

    jBus = updatePing(jBus, lat, lng, now, driver)
    _redis.hset('buses', '{}:{}'.format(line, mac), pickle.dumps(jBus))

    # send data to socket connected clients
    jBus['path'] = list(jBus['path'])
    # subs.socket_emit(jBus, sioEvents['subscribe'], room=jBus['line_id'], type=jBus['type'])
    socket_emit(jBus, line_id=jBus['line_id'], only_base=True)
    return dict(message='subscribe updated', code=200)


def clear_redis(line_id, mac):
    _redis = getRedis(segment['buses'])
    if _redis['code'] != 200:
        return _redis
    _redis = _redis['data']
    pipe = redis.Redis.pipeline(_redis)
    pipe.hdel('buses', '{}:{}'.format(line_id, mac))
    pipe.hdel('lines', mac)
    pipe.execute()


def deleteBus(data):
    _redis = getRedis(segment['buses'])
    if _redis['code'] != 200:
        return _redis
    _redis = _redis['data']
    pipe = redis.Redis.pipeline(_redis)
    busDB = bus_db.busDB_controller(SQL_CONNECTION)
    deletedBus = busDB.deleteBus(data['id'])
    if deletedBus['code'] != 200:
        return deletedBus
    deletedBus = deletedBus['data'][0]
    if 'line_id' in deletedBus:
        pipe.hdel('buses', '{}:{}'.format(deletedBus['line_id'], deletedBus['mac']))
        pipe.hdel('lines', deletedBus['mac'])
    else:
        pipe.hdel('unknown', deletedBus['mac'])
    pipe.execute()
    return dict(code=200, message='OK', data=deletedBus)

def listBuses():
    buses = getBuses()
    if buses['code'] != 200:
        return buses
    buses = buses['data']
    return dict(code=200, message='OK', data=buses)
#
def getUnknownBuses():
    _redis = getRedis(segment['buses'])
    if _redis['code'] != 200:
        return _redis
    _redis = _redis['data']
    buses = []
    keys = _redis.hgetall('unknown')
    for value in keys.values():
        bus = pickle.loads(value)
        bus['path'] = list(bus['path'])
        buses.append(bus)
    return dict(code=200, message='OK', data=buses)


