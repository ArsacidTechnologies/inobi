from inobi.transport import route
from inobi.security import secured
from inobi.transport.configs import __url_subscribe, scope
from ..API.subscribe_api import subscribe, driver, adminSubscribe
from ..API.subscribe_v2 import subscribe as subscribe_v2
from inobi.utils import http_err, http_ok
from flask import request


def _old_t_to_new_mapper(t):
    t['number'] = str(t['number'])
    return t


@route(__url_subscribe['subscribe'], methods=['POST'])
@secured()
def subscribee():
    data = request.get_json(force=True, silent=True)
    if not data:
        return http_err('json required', 400)

    if 'inactive' not in data:
        return http_err('inactive argument is missing', 400)
    if 'line_id' not in data:
        return http_err('line_id argument is missing', 400)


    if data['inactive'].lower() == 'false':
        data['inactive'] = False
    elif data['inactive'].lower() == 'true':
        data['inactive'] = True
    else:
        return http_err('inactive argument not valid', 400)

    subscribes = list(map(_old_t_to_new_mapper, subscribe_v2(data['line_id'])))
    return http_ok(dict(data=subscribes), count=len(subscribes))
    # response = subscribe(data)
    # if response['code'] != 200:
    #     return http_err(response['message'], response['code'])
    # return http_ok(message=response['message'], data=dict(data=response['data']))


@route(__url_subscribe['driver'], methods=['POST', 'GET'])
@secured((scope['admin'], 'transport_driver'))
def driverSubscribe():
    token_data = driverSubscribe._token_data
    transport = token_data.get('transport')
    if not transport:
        return http_err('UNAUTHORIZED', 401)
    line_id = transport.get('line_id')
    if not line_id:
        return http_err('UNAUTHORIZED', 401)
    response = driver(line_id)
    if response['code'] != 200:
        return http_err(response['message'], response['code'])
    return http_ok(message=response['message'], data=dict(data=response['data']))


@route(__url_subscribe['adminSubscribe'], methods=['POST', 'GET'])
@secured(scope['viewer'])
def adminSubscribee():
    try:
        data = request.get_json(force=True)
    except:
        return http_err('json is not valid', 400)

    if 'inactive' not in data:
        return http_err('inactive argument is missing')
    if 'line_id' not in data:
        return http_err('line_id argument is missing')

    if data['inactive'].lower() == 'false':
        data['inactive'] = False
    elif data['inactive'].lower() == 'true':
        data['inactive'] = True
    else:
        return http_err('inactive argument not valid', 400)

    response = adminSubscribe(data)
    if response['code'] != 200:
        return http_err(response['message'], response['code'])
    return http_ok(message=response['message'], data=dict(data=response['data']))


# _kek = 0

# from inobi.redis import getredis
# from inobi.config import redis_segments

# import logging
# from datetime import datetime
# logging.basicConfig(filename='socketio.log', level=logging.DEBUG)


# @socketio.on('connect')
# @secured(else_answer=False)
# def socket_connection():
#     r = getredis(redis_segments['socket'])
#     r.hset('connections', request.sid, request.namespace)
#     global _kek
#     _kek += 1
#     logging.debug(' {} connected {} {}'.format(_kek, datetime.now(), request.sid))
#     print('connect', _kek)
#     return True


# @route('/socketio/check')
# def httpStatus():
#     arr = []
#     rooms = socketio.server.manager.rooms
#     for namespace, rsio in rooms.items():
#         for room, sio in rsio.items():
#             arr.append(
#                 dict(sios=sio,
#                      room=room,
#                      namespace=namespace)
#             )
#     return jsonify(arr)
#
#
# @route('/socketio/delete')
# def toDelete():
#     r = getredis(redis_segments['socket'])
#     toDelete = r.hgetall('toDelete')
#     if toDelete:
#         for sid, namespace in toDelete.items():
#             socketio.server.disconnect(sid.decode(), namespace.decode())
#             r.hdel('connections', sid.decode())
#         r.delete('toDelete')
#     return str(toDelete)




# @socketio.on('status')
# def status(*args):
#     r = getredis(redis_segments['socket'])
#     sid = request.sid
#     r.hdel('toDelete', sid)
#
#
# @socketio.on('disconnect')
# def socket_disconnection():
#     r = getredis(redis_segments['socket'])
#     r.hdel('connections', request.sid)
#     global _kek
#     _kek -= 1
#
#     print('disconnect', _kek)
#     logging.debug(' {} disconnected {} {}'.format(_kek, datetime.now(), request.sid))
#
#     return None
#
#
# @socketio.on(sioEvents['join'])
# def join_rooms(*args, **kwargs):
#     for room in args:
#         if isinstance(room, (list, tuple)):
#             for subroom in room:
#                 # print(request.sid, 'joined to', )
#                 join_room(subroom, request.sid)
#         else:
#             join_room(room, request.sid)
#     emit(sioEvents['join'], {'status': 200, 'message': 'successfully joined', 'room': args}, room=request.sid)
#     return {'status': 200, 'message': 'successfully joined', 'room': args}
#
#
#
# @socketio.on(sioEvents['leave'])
# def leave_rooms(*args, **kwargs):
#
#     for room in args:
#         if isinstance(room, (list, tuple)):
#             for subroom in room:
#                 leave_room(subroom, request.sid)
#         else:
#             leave_room(room, request.sid)
#     emit(sioEvents['leave'], {'status': 200, 'message': 'successfully leaved', 'room': args}, room=request.sid)
#     return {'status': 200, 'message': 'successfully leaved', 'room': args}
#
#
# from flask_socketio import Namespace
#
#
# class adminNamespace(Namespace):
#     @secured('transport_viewer', else_answer=False)
#     def on_connect(self):
#         print("ADMIN CONNECTED")
#         return True
#
#     def on_join(self, *args):
#         for room in args:
#             if isinstance(room, (list, tuple)):
#                 for subroom in room:
#                     join_room(subroom, request.sid)
#             else:
#                 join_room(room, request.sid)
#         emit('join', {'status': 200, 'message': 'successfully joined', 'room': args}, room=request.sid)
#         return {'status': 200, 'message': 'successfully joined', 'room': args}
#
#     def leave_rooms(*args):
#         for room in args:
#             if isinstance(room, (list, tuple)):
#                 for subroom in room:
#                     leave_room(subroom, request.sid)
#             else:
#                 leave_room(room, request.sid)
#         emit('leave', {'status': 200, 'message': 'successfully leaved', 'room': args}, room=request.sid)
#         return {'status': 200, 'message': 'successfully leaved', 'room': args}
#
#
# socketio.on_namespace(adminNamespace('/admin'))
