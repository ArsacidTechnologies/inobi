from inobi.transport import route
from flask import request, jsonify
from inobi.utils import http_ok, http_err, getargs, converter
from inobi.security import secured
from inobi.transport.API.subscribe_v2 import subscribe, admin_subscribe
from inobi import socketio

from inobi.transport import admin_namespace, transport_namespace, base_namespace, driver_namespace
from inobi.transport.configs import WS_TRANSPORT_NAMESPACE, WS_ADMIN_NAMESPACE, WS_BASE_NAMESPACE, WS_DRIVER_NAMESPACE

from copy import deepcopy
from inobi.transport import error_codes as ec


@route('/v2/subscribe', methods=['POST', 'GET'])
@secured()
def sub_view():
    (line_id,) = getargs(request, 'line_id')
    subscribes = subscribe(line_id)
    return http_ok(dict(data=subscribes), count=len(subscribes))


@route('/v3/subscribe', methods=['POST', 'GET'])
@secured()
def sub_v3_view():
    (line_id,) = getargs(request, 'line_id')
    subscribes = subscribe(line_id, exclude=())
    return http_ok(dict(data=subscribes), count=len(subscribes))


@route('/v2/driver/subscribe', methods=['POST', 'GET'])
@secured('transport_admin transport_driver')
def v2_driver_view(token_data):
    transport = token_data.get('transport')
    if not transport:
        return http_err('Transport Data Is Missing', 400, error_code=ec.ACCESS_DENIED)
    line_id = transport.get('line_id')
    if not line_id:
        return http_err('line_id Is Missing', 400, error_code=ec.LINE_NOT_FOUND)
    subscribes = admin_subscribe(line_id)
    return http_ok(dict(data=subscribes), count=len(subscribes))


@route('/v1/subscribe/routes')
@secured()
@converter.converted()
def subscribe_routes(city_id: int):
    transports = subscribe(type='admin', city_id=city_id, exclude=())
    active_routes = {}
    for transport in transports:
        if transport['line_id'] not in active_routes:
            active_routes[transport['line_id']] = 1
        else:
            active_routes[transport['line_id']] += 1
    routes = []
    for route_id, quantity in active_routes.items():
        routes.append({
            "route_id": route_id,
            "active": quantity
        })
    return http_ok(data={"data": routes})


@route('/socketio/check')
def httpStatus():
    return http_ok()
    arr = []
    count = {
        WS_TRANSPORT_NAMESPACE: 0,
        WS_ADMIN_NAMESPACE: 0,
        WS_BASE_NAMESPACE: 0,
        WS_DRIVER_NAMESPACE: 0
    }
    rooms = deepcopy(socketio.server.manager.rooms)
    conns = set()
    for namespace, rsids in rooms.items():
        for room, sids in rsids.items():
            for sid, active in sids.items():
                if room == sid:
                    arr.append(
                        dict(sid=sid,
                             namespace=namespace)
                    )
                    if namespace == WS_ADMIN_NAMESPACE:
                        count[WS_ADMIN_NAMESPACE] += 1
                        admin_namespace.set_conn(sid, namespace)
                    elif namespace == WS_TRANSPORT_NAMESPACE:
                        count[WS_TRANSPORT_NAMESPACE] += 1
                        transport_namespace.set_conn(sid, namespace)
                    elif namespace == WS_BASE_NAMESPACE:
                        count[WS_BASE_NAMESPACE] += 1
                        base_namespace.set_conn(sid, namespace)
                    elif namespace == WS_DRIVER_NAMESPACE:
                        count[WS_DRIVER_NAMESPACE] += 1
                        driver_namespace.set_conn(sid, namespace)

                    conns.add((sid, namespace))
    for sid, namespace in conns:
        socketio.emit('status', room=sid, namespace=namespace, data='hello')
    from ..views import logger
    logger.info(' '.join('{}={}'.format(k, v) for k, v in count.items()))
    return http_ok(conns=arr)


@route('/socketio/delete')
def toDelete():
    return http_ok()
    deleted = []
    deleted += base_namespace.del_crack_conns()
    deleted += transport_namespace.del_crack_conns()
    deleted += admin_namespace.del_crack_conns()
    deleted += driver_namespace.del_crack_conns()
    return http_ok(dict(data=deleted), count=len(deleted))


