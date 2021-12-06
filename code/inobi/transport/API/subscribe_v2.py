import psycopg2
from inobi.redis import getredis
from inobi.config import RedisSegments
import pickle
import time
from inobi.transport.configs import Room, Event, \
    WS_TRANSPORT_NAMESPACE, WS_ADMIN_NAMESPACE, WS_BASE_NAMESPACE, TKeys, WS_DRIVER_NAMESPACE, RouteTypes, \
    WS_TRANSPORT_V2_NAMESPACE
from inobi.transport.exceptions import TransportException
import json

from ..DataBase.line_v2 import get_transport_organization_lines
from inobi.transport.error_codes import LINE_NOT_FOUND, ACCESS_DENIED
from flask_socketio import emit
from inobi.transport.data_checker import TransportVariables
from .common import dump_ping
from ...config import SQL_CONNECTION


def _in_interval(timestamp):
    interval = 10 * 60
    now = time.time()
    if now - interval >= timestamp:
        return False
    else:
        return True


def _parse_transport(transport, type='public', exclude: tuple = (RouteTypes.SHUTTLE_BUS,), city_id=None):
    if city_id:
        if transport.get('organizations'):
            if city_id not in [organization.city for organization in transport['organizations']]:
                return None
        elif transport.get('city') and transport['city'] != city_id:
            return None

    new_transport = dict()

    transport['path'] = list(transport.get('path', []))
    if transport['path']:
        transport['path'] = [transport['path'][0]]
    if type == 'public':
        if transport.get('type') in (RouteTypes.TECHNICAL,) + tuple(exclude):
            return None
        if transport.get('type') == RouteTypes.SHUTTLE_BUS:
            transport['location']['lat'] = transport.get(TransportVariables.ADJUSTMENT_LAT, 0)
            transport['location']['lng'] = transport.get(TransportVariables.ADJUSTMENT_LNG, 0)
            transport['path'] = []
        lat = int(transport.get('location', {}).get('lat', 0))
        lng = int(transport.get('location', {}).get('lng', 0))
        if lat == 0 and lng == 0:
            return None
        for k, v in transport.items():
            if k in TransportVariables.PUBLIC:
                new_transport[k] = v
        new_transport['name'] = transport.get('number')

    elif type == 'admin':
        new_transport = dump_ping(transport)
    return new_transport, _in_interval(new_transport['time'])


def subscribe(line_id='all', type='public', inactive=False, organization_id=None,
              exclude: tuple = (RouteTypes.SHUTTLE_BUS,), all=False, city_id=None):
    in_time = []
    out_time = []
    redis = getredis(RedisSegments.BUSES_V2)

    if organization_id:
        organization_lines = redis.hget(TKeys.ORGANIZATION_LINES, organization_id)
        if not organization_lines:
            organization_lines = get_transport_organization_lines(organization_id)
            redis.hset(TKeys.ORGANIZATION_LINES, organization_id, json.dumps(organization_lines))
        else:
            organization_lines = organization_lines.decode()
            organization_lines = json.loads(organization_lines)

        organization_lines = set(organization_lines)
        if isinstance(line_id, list):
            line_id = set(line_id)
            line_id = line_id.intersection(organization_lines)
        elif isinstance(line_id, int):
            if line_id not in organization_lines:
                return []
        elif isinstance(line_id, str):
            if line_id.lower() == 'all':
                line_id = organization_lines
            else:
                raise TransportException(msg='line_id argument is unknown', code=LINE_NOT_FOUND)

    if isinstance(line_id, (list, tuple, set)):
        if not isinstance(line_id, set):
            line_id = set(line_id)

        # =====================================================
        with psycopg2.connect(SQL_CONNECTION) as conn:
            with conn.cursor() as cursor:
                cursor.execute('select id from routes')
                rows = cursor.fetchall()
                routes = [route[0] for route in rows]
                line_id = set(routes)
        # ====================================================
        raw = redis.hgetall(TKeys.TRANSPORTS)
        for k, v in raw.items():
            key = k.decode().split(':')
            if int(key[0]) in line_id:
                parsed = _parse_transport(pickle.loads(v), type, exclude=exclude, city_id=city_id)
                if not parsed:
                    continue
                transport, in_interval = parsed
                if in_interval:
                    in_time.append(transport)
                else:
                    out_time.append(transport)

    elif isinstance(line_id, int):
        cached = redis.get(TKeys.cached_subs_key(line_id))
        if cached:
            cached_data = json.loads(cached.decode())
            in_time = cached_data['in_time']
            out_time = cached_data['out_time']
        else:
            raw = redis.hgetall(TKeys.TRANSPORTS)
            for k, v in raw.items():
                key = k.decode().split(':')
                t_line = int(key[0])
                if t_line == line_id:
                    parsed = _parse_transport(pickle.loads(v), type, exclude=exclude, city_id=city_id)
                    if not parsed:
                        continue
                    transport, in_interval = parsed
                    if in_interval:
                        in_time.append(transport)
                    else:
                        out_time.append(transport)
            cached = {
                "in_time": in_time,
                "out_time": out_time
            }
            redis.set(TKeys.cached_subs_key(line_id), json.dumps(cached), ex=5)
    elif isinstance(line_id, str):
        if line_id.lower() == 'all':
            raw = redis.hgetall(TKeys.TRANSPORTS)
            for raw_transport in raw.values():
                parsed = _parse_transport(pickle.loads(raw_transport), type, exclude=exclude, city_id=city_id)
                if not parsed:
                    continue
                transport, in_interval = parsed
                if in_interval:
                    in_time.append(transport)
                else:
                    out_time.append(transport)
        else:
            raise TransportException('line_id argument is unknown', code=LINE_NOT_FOUND)
    else:
        raise TransportException('line_id argument is unknown', code=LINE_NOT_FOUND)

    if all:
        return in_time + out_time
    if not inactive:
        return in_time
    elif inactive and not type == 'public' or organization_id:
        return out_time
    else:
        raise TransportException('Forbidden', code=ACCESS_DENIED)


def admin_subscribe(route_id: int = None, inactive=False, organization_id=None, all=False):
    redis = getredis(RedisSegments.BUSES_V2)
    if route_id:
        cached = redis.get(TKeys.cached_subs_key(route_id))
        if cached:
            cached_data = json.loads(cached.decode())
            in_time = cached_data['in_time']
            out_time = cached_data['out_time']
            if all:
                data = in_time + out_time
            elif inactive:
                data = out_time
            else:
                data = in_time
            return data

    raw = redis.hgetall(TKeys.TRANSPORTS)
    in_time = []
    out_time = []
    for k, v in raw.items():
        ping = pickle.loads(v)
        parsed, is_active = _parse_transport(ping, 'admin', exclude=())

        if organization_id is not None:
            if ping.get('organizations'):
                if organization_id in [org.id for org in ping['organizations']]:
                    if route_id is not None:
                        if parsed['line_id'] == route_id:
                            if is_active:
                                in_time.append(parsed)
                            else:
                                out_time.append(parsed)
                    else:
                        if is_active:
                            in_time.append(parsed)
                        else:
                            out_time.append(parsed)
        elif route_id is not None:
            if parsed['line_id'] == route_id:
                if is_active:
                    in_time.append(parsed)
                else:
                    out_time.append(parsed)
    if route_id:
        cached = {
            "in_time": in_time,
            "out_time": out_time
        }
        redis.set(TKeys.cached_subs_key(route_id), json.dumps(cached), ex=5)

    if all:
        data = in_time + out_time
    elif inactive:
        data = out_time
    else:
        data = in_time
    return data


from copy import deepcopy


def socket_emit(transport, line_id=None, unknown=False, *args, **kwargs):
    admin_dump = dump_ping(transport)
    line_id = transport.get('line_id')
    skiped = False
    transport_copy = deepcopy(transport)
    parsed = _parse_transport(transport_copy, exclude=())
    V2 = False
    if not parsed:
        skiped = True
    if unknown:
        skiped = True
    if transport.get('type') == RouteTypes.TECHNICAL:
        skiped = True
    if transport.get('type') == RouteTypes.SHUTTLE_BUS:
        V2 = True
    if not skiped:
        pub_transport, in_interval = parsed
        if not V2:
            emit(Event.SUBSCRIBE,
                 pub_transport,
                 room=line_id,
                 namespace=WS_BASE_NAMESPACE)
        if transport.get('organizations'):
            for organization in transport['organizations']:
                if not V2:
                    emit(Event.SUBSCRIBE,
                         pub_transport,
                         room=Room.city_subscribe(organization.city),
                         namespace=WS_TRANSPORT_NAMESPACE)

                emit(Event.SUBSCRIBE,
                     pub_transport,
                     room=Room.city_subscribe(organization.city),
                     namespace=WS_TRANSPORT_V2_NAMESPACE)
        if not V2:
            emit(Event.SUBSCRIBE,
                 pub_transport,
                 room=line_id,
                 namespace=WS_TRANSPORT_NAMESPACE)
        emit(Event.SUBSCRIBE,
             pub_transport,
             room=line_id,
             namespace=WS_TRANSPORT_V2_NAMESPACE)

        if not V2:
            # BACKWARD COMPATIBILITY
            emit(Event.SUBSCRIBE,
                 pub_transport,
                 room="all",
                 namespace=WS_BASE_NAMESPACE)
    if unknown:
        emit(Event.SUBSCRIBE,
             admin_dump,
             room=Room.UNKNOWN,
             namespace=WS_ADMIN_NAMESPACE)
    else:
        if transport.get('organizations'):
            for organization in transport['organizations']:
                emit(Event.SUBSCRIBE,
                     admin_dump,
                     room=Room.organization_subscribe(organization.id),
                     namespace=WS_ADMIN_NAMESPACE)
        emit(Event.SUBSCRIBE,
             admin_dump,
             room=line_id,
             namespace=WS_ADMIN_NAMESPACE)

        # Driver SocketIO
        emit(Event.SUBSCRIBE,
             admin_dump,
             room=line_id,
             namespace=WS_DRIVER_NAMESPACE)
