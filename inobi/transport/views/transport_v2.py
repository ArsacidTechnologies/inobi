import os
from inobi.transport import route
from inobi.transport.configs import INOBI_BOX_TOKEN, AUDIO_RESOURCES, TKeys
from inobi.security import secured, verify as default_verification, scope
from inobi.transport.API.transport_v2 import ping_handler, get_unknowns, delete_unknowns
from inobi.transport.API.transport_v2 import get_all_buses_info, get_bus_status_report
from flask import send_from_directory, request
from inobi.utils import http_ok, http_err, getargs
from inobi.utils.converter import converted
from flask_cors import cross_origin
from inobi.redis import getredis
from inobi.config import RedisSegments
# from inobi.transport.platform_travel.platform_travel_app import App as PlatformTravel
from inobi.transport.data_checker import check_ping, TransportVariables, parse
from datetime import datetime
import requests
from flask import request as freq


# plt = PlatformTravel()


def my_verification(token: str, base64: bool = True) -> dict:
    if token == INOBI_BOX_TOKEN:
        return {'scopes': [scope.Transport.OLD_TOKEN_BOX]}
    return default_verification(token, base64=base64)


@route('/bus', methods=['POST', "GET"])
@secured([scope.Transport.ADMIN,
          scope.Transport.DRIVER,
          *scope.Transport.ANY_BOXES
          ],
         verify=my_verification)
@converted(rest_key="rest")
def ping_view(token_data, scopes, id: str, lat: float, lon: float = None, lng: float = None,
              status: int = 1, bearing: float = None, speed: float = None, rest: dict = None):
    if lng is None and lon is None:
        return http_err("'lon' Parameter Is Missing", 400)


    # ========================================================================

    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    params_dict = dict(freq.args)
    params_dict["timestamp"] = timestamp
    device_imei = params_dict["id"]
    if params_dict['NS'] and int(params_dict["NS"]) >= 4:
        response = requests.post("http://localhost:5055", params=params_dict)
        print(f"[!!!!!!] TRACCAR INSERTION STATUS CODE {response.status_code} FOR DEVICE {device_imei}")

    # ========================================================================

    
    
    data = dict(
        id=id,
        lat=lat,
        lng=lon or lng or 0.0,
        bus_status=status,
        time=timestamp,
        satellites=params_dict['NS'] if 'NS' in params_dict else '-',
        hardware=params_dict['HV'] if 'HV' in params_dict else '-',
        software=params_dict['SV'] if 'SV' in params_dict else '-'
    )
    check_ping(rest)
    kwargs = dict(rest)
    parse(kwargs)
    if kwargs.get('phone'):
        kwargs['device_phone'] = kwargs.pop('phone')
    kwargs['speed'] = speed
    if bearing is not None:
        kwargs['bearing'] = bearing
    if scope.Transport.DRIVER in scopes:
        transport = token_data.get('transport')
        if not transport:
            return http_err('Forbidden', 403)
        _id = transport.get('device_id')
        if not _id:
            return http_err('Forbidden', 403)
        user = token_data.get('user')
        if not user:
            return http_err('Forbidden', 403)
        kwargs['driver'] = user['id']
        data['id'] = _id
    else:
        _id = data['id']

    if kwargs.get('passengers_in'):
        try:
            kwargs['passengers_in'] = int(kwargs['passengers_in'])
        except ValueError:
            return http_err('passengers_in must be digit', 400)
    if kwargs.get('passengers_out'):
        try:
            kwargs['passengers_out'] = int(kwargs['passengers_out'])
        except ValueError:
            return http_err('passengers_out must be digit', 400)
    ping = ping_handler(_id, data['lat'], data['lng'], data['bus_status'], data['time'], data['hardware'], data['software'], data['satellites'], **kwargs)

    # BACKWARD COMPATIBILITY
    # bus(data)
    # plt.process_message(ping)

    return http_ok(data=dict(data=ping))


from inobi.utils.converter import converted
from ..API import transport_v2 as r_db
from inobi.security import sign


TOKEN_EXPIRATION_INTERVAL = 3*60*60


@route('/v1/login', methods='GET POST'.split())
@converted
def transport_login_v1(id: str):

    device = r_db.get_device(id)

    payload = device
    if payload is None:
        payload = dict(device_id=id)

    scopes = [scope.Transport.BOX, scope.Transport.UNKNOWN_BOX] \
        if device is None else [scope.Transport.BOX]

    token = sign(payload, scopes, expires_after=TOKEN_EXPIRATION_INTERVAL)

    return http_ok(token=token, device=device)


@route('/v2/unknowns', methods='GET DELETE'.split())
@cross_origin()
# @secured('transport_admin')
def un_list():
    if request.method == 'GET':
        transports = get_unknowns()
        return http_ok(dict(data=transports), count=len(transports))
    else:
        return http_ok(deleted=delete_unknowns())


import json
from inobi.transport.DataBase.transport_v2 import get_all_transports



@route('/v1/buses/info', methods=['GET'])
@secured([scope.Transport.ADMIN])
def buses_info_list():
    infos = get_all_buses_info()
    if not infos:
        return http_ok(data=dict(data=[]))
    else:
        return http_ok(data=dict(data=infos))



@route('/v1/buses/instructions', methods=['GET', 'DELETE'])
@secured('transport_inobi')
def box_settings():
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hgetall(TKeys.INSTRUCTIONS)
    if not raw:
        return http_ok(data=dict(data=[]))
    settings = []
    for id_, v in raw.items():
        id_ = id_.decode()
        v = json.loads(v.decode())
        settings.append(dict(transport=id_, instructions=v))
    if request.method == 'DELETE':
        redis.delete(TKeys.INSTRUCTIONS)
    return http_ok(data=dict(data=settings))


@route('/v1/buses/instructions/<id>')
@secured('transport_inobi')
def box_settings_individual(id):
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hget(TKeys.INSTRUCTIONS, id)
    if not raw:
        return http_ok(data={})
    data = json.loads(raw.decode())
    resp = dict(transport=id, instructions=data)
    return http_ok(data=resp)


@route('/v1/buses/instructions/<id>', methods=['DELETE'])
@secured('transport_inobi')
def box_settings_individual_delete(id):
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hget(TKeys.INSTRUCTIONS, id)
    if not raw:
        return http_ok(data={})
    data = json.loads(raw.decode())
    resp = dict(transport=id, instructions=data)
    redis.hdel(TKeys.INSTRUCTIONS, id)
    return http_ok(data=resp)


@route('/v1/buses/instructions/<id>', methods=['PATCH'])
@secured('transport_inobi')
def box_settings_individual_update(id):
    new_data = request.get_json(force=True, silent=True)
    if not new_data:
        return http_err('json required', 400)
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hget(TKeys.INSTRUCTIONS, id)
    if not raw:
        data = dict()
    else:
        data = json.loads(raw.decode())
    data.update(new_data)
    redis.hset(TKeys.INSTRUCTIONS, id, json.dumps(data))
    resp = dict(transport=id, instructions=data)
    return http_ok(data=resp)


@route('/v1/buses/instructions', methods=['POST'])
@secured('transport_inobi')
def box_settings_save():
    data = request.get_json(force=True, silent=True)
    if not data:
        return http_err('json required', 400)
    if not data.get('instructions'):
        return http_err('instructions parameter required', 400)
    if not data.get('transports'):
        db_transport = get_all_transports()
        requested_transports = [t.device_id for t in db_transport]
    else:
        requested_transports = data['transports']
    redis = getredis(RedisSegments.BUSES_V2)
    resp = []
    for transport_id in requested_transports:
        redis.hset(TKeys.INSTRUCTIONS, transport_id, json.dumps(data['instructions']))
        resp.append(dict(transport=transport_id, instructions=data['instructions']))
    return http_ok(data=dict(data=resp))


@route('/v1/buses/instructions/results', methods=['GET'])
@secured('transport_inobi')
def box_settings_results():
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hgetall(TKeys.INSTRUCTION_RESULTS)
    result = []
    for rid, rtext in raw.items():
        result.append(dict(
            device_id=rid.decode(),
            text=rtext.decode()
        ))
    return http_ok(data=dict(data=result))


@route('/v1/buses/instructions/results', methods=['DELETE'])
@secured('transport_inobi')
def box_settings_results_del():
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hgetall(TKeys.INSTRUCTION_RESULTS)
    result = []
    for rid, rtext in raw.items():
        result.append(dict(
            device_id=rid.decode(),
            text=rtext.decode()
        ))
    redis.delete(TKeys.INSTRUCTION_RESULTS)
    return http_ok(data=dict(data=result))


@route('/v1/buses/instructions/<id>/results', methods=['DELETE'])
@secured('transport_inobi')
def box_settings_result_del(id):
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hget(TKeys.INSTRUCTION_RESULTS, id)
    result = dict(
        device_id=id,
        text=raw.decode()
    )
    redis.delete(TKeys.INSTRUCTION_RESULTS)
    return http_ok(data=dict(data=result))


@route('/v1/buses/instructions/<id>/results')
@secured('transport_inobi')
def box_settings_result(id):
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hget(TKeys.INSTRUCTION_RESULTS, id)
    result = dict(
        device_id=id,
        text=raw.decode()
    )
    return http_ok(data=dict(data=result))

