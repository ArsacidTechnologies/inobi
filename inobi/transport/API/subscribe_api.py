from inobi.redis import getRedis
from inobi.config import redis_segments
import time
import pickle


def __outOfInterval(timestamp):
    interval = 10 * 60
    now = time.time()
    if now - interval >= timestamp:
        return True
    else:
        return False

def __parseBus(bus):
    bus = pickle.loads(bus)
    if bus.get('path'):
        bus['path'] = list(bus['path'])
    return bus

def __parsePublicBus(bus):
    bus = pickle.loads(bus)
    newBus = dict()
    for k, v in bus.items():
        if k not in ['driver', 'mac', 'plate', 'device_phone']:
            newBus[k] = v
    if bus.get('path'):
        newBus['path'] = list(bus['path'])

    lat = int(bus.get('location', {}).get('lat', 0))
    lng = int(bus.get('location', {}).get('lng', 0))
    if lat == 0 or lng == 0:
        return None
    return newBus

def driver(line_id):
    busesInInterval = []
    busesOutOfInterval = []

    _redis = getRedis(redis_segments['buses'])
    _redis = _redis['data']
    keys = _redis.hscan_iter('buses', match='{}:*'.format(line_id))
    for key in keys:
        k, bus = key
        if bus:
            bus = __parseBus(bus)

            if __outOfInterval(bus['time']):
                busesOutOfInterval.append(bus)
            else:
                busesInInterval.append(bus)
    return dict(code=200, data=busesInInterval, message='OK')

def adminSubscribe(data):
    busesInInterval = []
    busesOutOfInterval = []

    _redis = getRedis(redis_segments['buses'])
    _redis = _redis['data']
    line_id = data['line_id']

    if type(line_id) != list:
        if line_id.lower() == 'all':
            redisData = _redis.hgetall('buses')
            for bus in redisData.values():
                bus = __parseBus(bus)

                if __outOfInterval(bus['time']):
                    busesOutOfInterval.append(bus)
                else:
                    busesInInterval.append(bus)
        else:
            keys = _redis.hscan_iter('buses', match='{}:*'.format(line_id))
            for key in keys:
                k, bus = key
                if bus:
                    bus = __parseBus(bus)

                    if __outOfInterval(bus['time']):
                        busesOutOfInterval.append(bus)
                    else:
                        busesInInterval.append(bus)

    else:
        for line in line_id:
            keys = _redis.hscan_iter('buses', match='{}:*'.format(line))
            for item in keys:
                key, bus = item
                if bus:
                    bus = __parseBus(bus)

                    if __outOfInterval(bus['time']):
                        busesOutOfInterval.append(bus)
                    else:
                        busesInInterval.append(bus)

    if data['inactive']:
        return dict(code=200, message='OK', data=busesOutOfInterval)
    elif not data['inactive']:
        return dict(code=200, message='OK', data=busesInInterval)


def subscribe(data):
    busesInInterval = []
    busesOutOfInterval = []

    _redis = getRedis(redis_segments['buses'])
    _redis = _redis['data']
    line_id = data['line_id']

    if type(line_id) != list:
        if line_id.lower() == 'all':
            redisData = _redis.hgetall('buses')
            for bus in redisData.values():
                bus = __parsePublicBus(bus)
                if not bus:
                    continue
                if __outOfInterval(bus['time']):
                    busesOutOfInterval.append(bus)
                else:
                    busesInInterval.append(bus)
        else:
            keys = _redis.hscan_iter('buses', match='{}:*'.format(line_id))
            for key in keys:
                k, bus = key
                if bus:
                    bus = __parsePublicBus(bus)
                    if not bus:
                        continue
                    if __outOfInterval(bus['time']):
                        busesOutOfInterval.append(bus)
                    else:
                        busesInInterval.append(bus)

    else:
        for line in line_id:
            keys = _redis.hscan_iter('buses', match='{}:*'.format(line))
            for item in keys:
                key, bus = item
                if bus:
                    bus = __parsePublicBus(bus)
                    if not bus:
                        continue
                    if __outOfInterval(bus['time']):
                        busesOutOfInterval.append(bus)
                    else:
                        busesInInterval.append(bus)

    if data['inactive']:
        return dict(code=200, message='OK', data=busesOutOfInterval)
    elif not data['inactive']:
        return dict(code=200, message='OK', data=busesInInterval)


# @staticmethod
# def ssocket_emit(data, event, room, type=None,  *args, **kwargs):
#     import copy
#     publicData = copy.deepcopy(data)
#     skiped = True if int(publicData['location']['lng']) == 0 \
#         or int(publicData['location']['lat']) == 0 else False
#     for p in ['driver', 'mac', 'plate', 'device_phone']:
#         if p in publicData:
#             try:
#                 del publicData[p]
#             except:
#                 publicData.pop(p, None)
#
#     if room != sioRooms['unknown']:
#         if not skiped:
#             socketio.emit(event, data=publicData, room=room, json=True)
#             socketio.emit(event, data=publicData, json=True, room=sioRooms['all'])
#         socketio.emit(event, data=data, json=True, room=room, namespace='/admin')
#         socketio.emit(event, data=data, json=True, room=sioRooms['all'], namespace='/admin')
#
#         if type == 'trolleybus':
#             if not skiped:
#                 socketio.emit(event, data=publicData, json=True, room=sioRooms['t_bus'])
#             socketio.emit(event, data=data, json=True, room=sioRooms['t_bus'], namespace='/admin')
#         elif type == 'bus':
#             if not skiped:
#                 socketio.emit(event, data=publicData, json=True, room=sioRooms['bus'])
#             socketio.emit(event, data=data, json=True, room=sioRooms['bus'], namespace='/admin')
#         elif type == 'shuttle_bus':
#             if not skiped:
#                 socketio.emit(event, data=publicData, json=True, room=sioRooms['s_bus'])
#             socketio.emit(event, data=data, json=True, room=sioRooms['s_bus'], namespace='/admin')
#         else:
#             socketio.emit(event, data=data, json=True, room=room, namespace='/admin')
#     else:
#         socketio.emit(event, data=data, room=room, json=True, namespace='/admin')







