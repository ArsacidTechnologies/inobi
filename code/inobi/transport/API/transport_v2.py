from inobi.transport.DataBase import transport_v2 as t_db, models
from inobi.transport.exceptions import TransportException
from inobi.config import RedisSegments, KNOT
from inobi.redis import getredis
import pickle
import time as Time
from collections import deque
from math import radians, sin, cos, degrees, atan2
from .subscribe_v2 import socket_emit
import os
from inobi.transport.configs import TRANSPORT_PICTURE_DIRECTORY, BOX_INSTRUCTIONS, TKeys, Reasons, RouteTypes
from inobi.transport.error_codes import TRANSPORT_NOT_FOUND
from .notification import check_for_notification
import json
from inobi.utils import connected
from inobi.transport.data_checker import convert_route, TransportVariables
from .common import dump_ping
from datetime import datetime
import time

def get_bearing(point1, point2):
    lng1, lat1, lng2, lat2 = map(radians, [point1['lng'], point1['lat'], point2['lng'], point2['lat']])

    dlng = lng2 - lng1
    y = sin(dlng) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlng)
    bearing = degrees(atan2(y, x))
    return round((bearing + 360) % 360, 3)


def update_ping(old: dict, lat, lng, status, hv, sv, sn, **kwargs):
    current_time = time.time()
    path = old.get('path', deque(maxlen=5))
    if int(lat) != 0 and int(lng) != 0:
        path.append(
            dict(
                lat=lat,
                lng=lng,
                time=current_time
            )
        )





    # ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ [BUS STATUS ALGO] ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡
    device_id = old['device_id']
    if "last_total_time_on" in old:
        last_status        = old['bus_status']
        last_time          = old['time']
        if last_status == 1 and status == 1:
            how_long_on = current_time - last_time # how long the bus was on
            old["last_total_time_on"] += abs(how_long_on) # get abs in those case that current_time is smaller than the old ; this won't happend never ever! unless the incoming time is smaller than the past time!!!!!!!
    else:
        old["last_total_time_on"] = 0 # if there are no cache for this device_id then we have to insert a new one and its total_time_on is 0
    inserted_bus_info_row = t_db.save_bus_info(device_id, lat, lng, status, current_time, old["last_total_time_on"]) # insert infos into bus_info table
    # ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡






        
    old['path'] = path
    old['location'] = dict(
        lat=lat,
        lng=lng
    )

    old['time'] = current_time
    old['bus_status'] = status
    old['hardware'] = hv
    old['software'] = sv
    old['satellites'] = sn






    
    if kwargs.get('speed'):
        kwargs['speed'] = kwargs['speed'] * KNOT
    for param in TransportVariables.online_fields:
        if param in old:
            del old[param]
    old.update(kwargs)

    ### SSH PART
    if TransportVariables.SSH in old:
        ssh = old[TransportVariables.SSH]

        # if TransportVariables.SSH_INFO in old and ssh is not None:
        #     ssh_info = old[TransportVariables.SSH_INFO]
        #     if ssh_info is not None:
        #         if ssh.get('remote_port', 1) == ssh_info.get('remote_port', 2):
        #             del old[TransportVariables.SSH]
        if ssh is None and old.get(TransportVariables.SSH_INFO) is None:
            del old[TransportVariables.SSH]
    return old


def save_instruction_results(ping: dict, *, redis: getredis):
    # is not used for now 31.10.18
    return
    if 'cmd' not in ping:
        return
    device_id = ping['device_id']
    text = ping['cmd']
    instruction = redis.hget(TKeys.INSTRUCTIONS, device_id)
    if instruction:
        instruction = json.loads(instruction.decode())
        if 'cmd' in instruction:
            del instruction['cmd']
        redis.hset(TKeys.INSTRUCTIONS, device_id, json.dumps(instruction))
    redis.hset(TKeys.INSTRUCTION_RESULTS, device_id, text)
    del ping['cmd']


def update_box_settings(ping, redis: getredis):
    settings = dict(BOX_INSTRUCTIONS)
    ping['instructions'] = settings

    # is not used for now 31.10.18
    return
    raw = redis.hget(TKeys.INSTRUCTIONS, ping['device_id'])
    settings = dict(BOX_INSTRUCTIONS)
    if raw:
        a = json.loads(raw.decode())
        settings.update(a)
    ping['instructions'] = settings

@connected
def db_case(conn, redis, pipe, device_id, lat, lng, status, hv, sv, sn, **kwargs):
    db_transport, route, organizations = t_db.get_by_device_id(conn=conn, mac=device_id)
    if not db_transport:
        ping = update_ping(dict(device_id=device_id), lat, lng, status, hv, sv, sn, **kwargs)
        save_instruction_results(ping, redis=redis)
        redis.hset(TKeys.UNKNOWNS,
                   device_id,
                   pickle.dumps(ping))
        if ping['path']:
            ping['path'] = [ping['path'][0], ]
        else:
            ping['path'] = []
        socket_emit(ping, unknown=True)
    else:
        exclude_from_converting = (RouteTypes.SHUTTLE_BUS, RouteTypes.TECHNICAL)
        # number = int(''.join(n for n in route.name if n.isdigit())) if route.type not in exclude_from_converting else route.name
        number = convert_route(route.name, route.type, exclude_from_converting)

        ping = update_ping(db_transport.asdict(), lat, lng, status, hv, sv, sn, **kwargs,
                           number=number, type=route.type, organizations=organizations, city=organizations[0].city)
        save_instruction_results(ping, redis=redis)
        for organization in organizations:
            organization = organization._asdict()
            check_for_notification({}, ping, organization)
            # pipe.hset(TKeys.ORGANIZATIONS, organization['id'], json.dumps(organization))

        pipe.hset(TKeys.LINES, db_transport.device_id, db_transport.line_id)
        pipe.hset(TKeys.TRANSPORTS,
                  '{}:{}'.format(db_transport.line_id, db_transport.device_id),
                  pickle.dumps(ping))
        if ping.get('path'):
            ping['path'] = [ping['path'][0], ]
        else:
            ping['path'] = []
        socket_emit(ping, line_id=ping['line_id'])

        if ping.get('device_phone') and ping['device_phone'] != db_transport.device_id:
            t_db.update_transports_phone(conn=conn, id=db_transport.id, phone=ping['device_phone'])
    return ping


def ping_handler(device_id, lat, lng, status, time, hv, sv, sn, **kwargs):
# ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ [BUS STATUS OPS] ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡
# NOTE - use datetime.fromtimestamp(int(time.time())) to turn the timestamp into UTC

    # incoming_time = int(datetime.strptime(time, '%Y-%m-%dT%H:%M:%S').timestamp())
    # transport_device = t_db.get_by_device_id_from_transports_table(device_id)
    # recs = t_db.get_bus_info_records(device_id)
    # if recs:
        # last_status        = recs[0][0]
        # last_time          = recs[0][1]
        # last_total_time_on = recs[0][2] # the first one is the last total_time_on - see get_bus_info_records api
        # if last_status == 1 and status == 1:
            # how_long_on = incoming_time - last_time # how long the bus was on
            # last_total_time_on += abs(how_long_on) # get abs in those case that incoming_time is smaller than the old ; this won't happend never ever! unless the incoming time is smaller than the past time!!!!!!!
        # else:
            # # NOTE - if the bus is off or switching to on/off the last total_time_on will be the one from the last record
            # pass
    # else:
        # last_total_time_on = 0 # if there are no records with this device_id then we're inserting a new one and its total_time_on is 0
    # if transport_device:
        # inserted_bus_info_row = t_db.save_bus_info(device_id, lat, lng, status, incoming_time, last_total_time_on) # insert infos into bus_info table

# ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡
    redis = getredis(RedisSegments.BUSES_V2)
    pipe = redis.pipeline()
    line_id = redis.hget(TKeys.LINES, device_id)
    if not line_id:
        unknown = redis.hget(TKeys.UNKNOWNS, device_id)
        if not unknown:
            ping = db_case(redis=redis, pipe=pipe, device_id=device_id, lat=lat, lng=lng, status=status, hv=hv, sv=sv, sn=sn, **kwargs)
        else:
            unknown = pickle.loads(unknown)
            ping = update_ping(unknown, lat, lng, status, hv, sv, sn, **kwargs)
            save_instruction_results(ping, redis=redis)
            redis.hset(TKeys.UNKNOWNS,
                       unknown['device_id'],
                       pickle.dumps(ping))
            if ping['path']:
                ping['path'] = [ping['path'][0], ]
            else:
                ping['path'] = []
            socket_emit(ping, unknown=True)

    else:
        line_id = line_id.decode()
        old = redis.hget(TKeys.TRANSPORTS, '{}:{}'.format(line_id, device_id))
        if not old:
            ping = db_case(redis=redis, pipe=pipe, device_id=device_id, lat=lat, lng=lng, status=status, hv=hv, sv=sv, sn=sn, **kwargs)
        else:
            old_ping = pickle.loads(old)
            if kwargs.get('device_phone') and kwargs['device_phone'] != old_ping.get('device_phone'):
                t_db.update_transports_phone(id=old_ping['id'], phone=kwargs['device_phone'])
            ping = update_ping(old_ping, lat, lng, status, hv, sv, sn, **kwargs)
            save_instruction_results(ping, redis=redis)
            organizations = ping.get('organizations')
            if not organizations:
                db_transport, route, organizations = t_db.get_by_device_id(mac=device_id)
                ping['organizations'] = organizations
            for organization in organizations:
                check_for_notification(old_ping, ping, organization._asdict())

            pipe.hset(TKeys.TRANSPORTS,
                      '{}:{}'.format(line_id, device_id),
                      pickle.dumps(ping))
            if ping['path']:
                ping['path'] = [ping['path'][0], ]
            else:
                ping['path'] = []
            socket_emit(ping, line_id=ping['line_id'])
    if ping['path']:
        ping['path'] = [ping['path'][0], ]
    else:
        ping['path'] = []
    pipe.execute()
    update_box_settings(ping, redis)
    return dump_ping(ping)


import typing as T


def get_device(device_id) -> T.Optional[dict]:
    redis = getredis(RedisSegments.BUSES_V2)
    line_id = redis.hget(TKeys.LINES, device_id)
    if not line_id:
        unknown = redis.hget(TKeys.UNKNOWNS, device_id)
        if not unknown:
            db_transport, *_ = t_db.get_by_device_id(mac=device_id)
            if not db_transport:
                return None
            else:
                return db_transport.asdict()
        else:
            unknown = pickle.loads(unknown)
            if 'path' in unknown:
                del unknown['path']
            return unknown

    else:
        line_id = line_id.decode()
        old = redis.hget(TKeys.TRANSPORTS, '{}:{}'.format(line_id, device_id))
        if not old:
            db_transport, *_ = t_db.get_by_device_id(mac=device_id)
            if not db_transport:
                return None
            else:
                return db_transport.asdict()
        else:
            old_ping = pickle.loads(old)
            if 'path' in old_ping:
                del old_ping['path']
            return old_ping


def save_transport(device_id, organization_id, **kwargs) -> dict:
    transport = t_db.save(device_id, organization_id, **kwargs)
    redis = getredis(RedisSegments.BUSES_V2)
    redis.hdel(TKeys.UNKNOWNS, transport.device_id)
    redis.hset(TKeys.LINES, transport.device_id, transport.line_id)

    return transport.asdict()


@connected
def unassign_driver_transport(conn, driver: int, reason: str = Reasons.CHECKED_OUT,
                              organization: int = None, redis: getredis = None):
    try:
        transport = t_db.get_by_driver(conn=conn, driver=driver)
    except TransportException:
        return None
    t_db.unassign_driver(conn=conn, driver=driver, organization=organization)
    t_db.save_transport_driver_changes(conn=conn, transport_id=transport.id, type_='driver',
                                       prev=driver, next=None, issuer=driver, reason=reason)
    if not redis:
        redis = getredis(RedisSegments.BUSES_V2)
    cached_transport = redis.hget(TKeys.TRANSPORTS, '{}:{}'.format(transport.line_id, transport.device_id))
    transport_dict = transport.asdict()
    if cached_transport:
        cached_transport = pickle.loads(cached_transport)
        cached_transport.update(transport_dict)
        redis.hset(TKeys.TRANSPORTS, '{}:{}'.format(transport.line_id, transport.device_id), pickle.dumps(cached_transport))
    return transport_dict


@connected
def update_driver_transports(conn, driver: int, transport: int, organization: int = None, redis=None):
    try:
        if not organization:
            old = t_db.get_by_id_filter_driver(conn=conn, transport=transport, driver=driver)
        else:
            old = t_db.get_by_id(id=transport, organization_id=organization, conn=conn)
        if old.driver == driver:
            return old.asdict()
        try:
            transport_old = t_db.get_by_driver(conn=conn, driver=driver)
            if transport_old.driver:
                t_db.save_transport_driver_changes(conn=conn, transport_id=transport_old.id,
                                                   type_='driver', prev=transport_old.driver, next=None,
                                                   issuer=driver, reason=Reasons.CHECKED_OUT)
        except TransportException:
            ...
        t_db.unassign_driver(conn=conn, driver=driver)

    except TransportException:
        old = None
    new = t_db.assign_driver(conn=conn, transport=transport, driver=driver)
    if old:
        old_driver = old.driver
    else:
        old_driver = None
    t_db.save_transport_driver_changes(conn, new.id, 'driver', old_driver, new.driver, driver,
                                       reason=Reasons.CHECKED_IN)
    if not redis:
        redis = getredis(RedisSegments.BUSES_V2)
    # redis.hdel(TKeys.TRANSPORTS, '{}:{}'.format(new.line_id, new.device_id))
    cached_transport = redis.hget(TKeys.TRANSPORTS, '{}:{}'.format(new.line_id, new.device_id))
    transport_dict = new.asdict()
    if cached_transport:
        cached_transport = pickle.loads(cached_transport)
        cached_transport.update(transport_dict)
        redis.hset(TKeys.TRANSPORTS, '{}:{}'.format(new.line_id, new.device_id), pickle.dumps(cached_transport))
    return transport_dict


from ..DataBase.models import Routes


def __update_transport(conn, id: int, organization_id, issuer, reason=None, **kwargs) -> dict:
    old = t_db.get_by_id(id, organization_id, conn)
    if not old:
        raise TransportException('Transport Does Not Exist', code=TRANSPORT_NOT_FOUND)
    old_picture = None
    if kwargs.get('payload'):
        if old.payload:
            old_picture = old.payload.get('picture')
            old.payload.update(kwargs['payload'])
            kwargs['payload'] = old.payload
    new = t_db.update(id, organization_id, conn=conn, **kwargs)
    if old_picture:
        try:
            os.remove(TRANSPORT_PICTURE_DIRECTORY + '/' + old_picture)
        except:
            ...
    is_line_changed = False
    if old.line_id != new.line_id:
        is_line_changed = True
        t_db.save_transport_driver_changes(conn, new.id, 'line', old.line_id, new.line_id, issuer, reason)
    elif old.driver != new.driver:
        t_db.save_transport_driver_changes(conn, new.id, 'driver', old.driver, new.driver, issuer, reason)

    redis = getredis(RedisSegments.BUSES_V2)
    pipe = redis.pipeline()
    number = None
    route_type = None
    if is_line_changed:
        route = Routes.query.get(new.line_id)
        if route:
            number = convert_route(route.name, route.type, (RouteTypes.TECHNICAL,))
            route_type = route.type
        pipe.hdel(TKeys.LINES, old.device_id)
        pipe.hset(TKeys.LINES, new.device_id, new.line_id)
    transport_old_redis_key = '{}:{}'.format(old.line_id, old.device_id)
    transport_new_redis_key = '{}:{}'.format(new.line_id, new.device_id)

    cached_transport = redis.hget(TKeys.TRANSPORTS, transport_old_redis_key)
    transport_dict = new.asdict()
    if number:
        transport_dict['number'] = number
        transport_dict['type'] = route_type
    if cached_transport:
        cached_transport = pickle.loads(cached_transport)
        cached_transport.update(transport_dict)
        pipe.hset(TKeys.TRANSPORTS, transport_new_redis_key, pickle.dumps(cached_transport))
    if transport_old_redis_key != transport_new_redis_key:
        pipe.hdel(TKeys.TRANSPORTS, transport_old_redis_key)
    pipe.execute()
    return transport_dict


def update_transport(id: int, organization_id, issuer, reason=None, conn=None, **kwargs) -> dict:
    if not conn:
        with t_db.get_conn() as conn:
            return __update_transport(conn, id, organization_id, issuer, reason, **kwargs)
    else:
        return __update_transport(conn, id, organization_id, issuer, reason, **kwargs)


def delete_transport(id: int, organization_id) -> dict:
    transport = t_db.delete(id, organization_id)
    redis = getredis(RedisSegments.BUSES_V2)
    redis.hdel(TKeys.TRANSPORTS, '{}:{}'.format(transport.line_id, transport.device_id))
    redis.hdel(TKeys.LINES, transport.device_id)
    if transport.payload:
        if 'picture' in transport.payload:
            try:
                os.remove(TRANSPORT_PICTURE_DIRECTORY + '/' + transport.payload.get('picture'))
            except:
                ...
    return transport.asdict()


def get_transport(id: int, organization_id) -> dict:
    transport = t_db.get_by_id(id, organization_id)
    return transport.asdict()


def get_all_buses_info() -> []:
    buses_info = t_db.get_buses_info()
    return buses_info

def get_bus_status_report(device_id: str, _from: str, _to: str) -> [{}]:
    bus_status_report = t_db.calculate_total_time_on(device_id, _from, _to)
    return bus_status_report

def get_all_transport(organization_id) -> []:
    transports = t_db.get_transports(organization_id)
    return transports


def get_unknowns() -> []:
    redis = getredis(RedisSegments.BUSES_V2)
    transports_hash_dict = redis.hgetall(TKeys.UNKNOWNS)
    transports = []
    for _, value in transports_hash_dict.items():
        transport = pickle.loads(value)
        transport['path'] = list(transport['path'])
        transports.append(transport)
    return transports


def delete_unknowns():
    redis = getredis(RedisSegments.BUSES_V2)
    try:
        return redis.hlen(TKeys.UNKNOWNS)
    finally:
        redis.delete(TKeys.UNKNOWNS)
