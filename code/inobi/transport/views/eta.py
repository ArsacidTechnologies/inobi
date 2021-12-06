from inobi.transport import route
from inobi.utils.converter import converted
from inobi.utils import http_ok
from inobi.security import secured, scope, verify
from inobi.transport.configs import INOBI_BOX_TOKEN, TKeys
from inobi.redis import getredis
from inobi.config import RedisSegments
from time import time as now
import json
from marshmallow import Schema, fields
from flask_cors import cross_origin
from datetime import datetime
from ..DataBase.eta import log as save_eta_log, platform_time_travel_log


class ETASerializer(Schema):
    id = fields.Integer(required=True)
    eta = fields.Integer(required=True)


def my_verification(token: str, base64: bool = True) -> dict:
    if token == INOBI_BOX_TOKEN:
        return {'scopes': [scope.Transport.OLD_TOKEN_BOX]}
    return verify(token, base64=base64)


@route('/ping/v1/data', methods=['POST'])
@cross_origin()
@secured([scope.Transport.ADMIN,
          scope.Transport.DRIVER,
          *scope.Transport.ANY_BOXES
          ],
         verify=my_verification)
@converted(rest_key="rest")
def eta_view(id: int, route_id: int=None, route_type: str=None, direction_id: int=None, eta: list=None,
             eta_log: dict = None, platform_time_travel: dict=None, rest: dict = None):
    data = {
        "id": id,
        "route_id": route_id,
        "direction_id": direction_id
    }
    if eta:
        platforms = eta
        platforms = ETASerializer(many=True).load(platforms)
        redis = getredis(RedisSegments.BUSES_V2)
        pipe = redis.pipeline()

        raw_data = redis.hgetall(TKeys.ETA)
        for key, value in raw_data.items():
            transport, platform = key.decode().split(':')
            if id == int(transport):
                pipe.hdel(TKeys.ETA, key)
        resp = []
        time = now()
        for platform in platforms:
            data2 = {
                "platform_id": platform['id'],
                "eta_time": int(time + platform['eta']),
                "line_id": route_id,
                "transport_id": id
            }
            pipe.hset(TKeys.ETA, TKeys.eta_key(id, platform['id']), json.dumps(data2))
            resp.append(data2)
        pipe.execute()
        data['eta'] = resp
    if eta_log:
        data['eta_log'] = save_eta_log(**eta_log, transport_id=id, route_id=route_id)
    if platform_time_travel:
        data['platform_time_travel'] = platform_time_travel_log(**platform_time_travel, transport_id=id)
    return http_ok(data)


def transport_eta(id: int):
    redis = getredis(RedisSegments.BUSES_V2)
    pipe = redis.pipeline()
    raw_data = redis.hgetall(TKeys.ETA)
    rows = []
    for key, value in raw_data.items():
        transport, platform = key.decode().split(':')
        if id == int(transport):
            rows.append(json.loads(value))

    server_time = int(now())
    platforms = []
    for platform in rows:
        if platform['eta_time'] < server_time:
            pipe.hdel(TKeys.ETA, TKeys.eta_key(id, platform['platform_id']))
            continue
        platform['eta_time'] = platform['eta_time'] - server_time
        platforms.append(platform)
    resp = {
        "platforms": platforms,
        "time": server_time
    }
    pipe.execute()
    return http_ok(resp)


@route('/eta/v1/transports/<int:id>', methods=['GET'])
@cross_origin()
@secured()
@converted()
def transport_eta_view(id: int):
    return transport_eta(id)


@route('/eta/v1/transports', methods=['POST'])
@cross_origin()
@secured()
@converted()
def transport_eta_view_post(id: int):
    return transport_eta(id)


@route('/eta/v1/platforms', methods=['POST'])
@cross_origin()
@secured()
@converted()
def platforms_eta(id: int, routes: list=None):
    if routes:
        routes = set(routes)
    redis = getredis(RedisSegments.BUSES_V2)
    raw_data = redis.hgetall(TKeys.ETA)
    pipe = redis.pipeline()
    rows = []
    for key, value in raw_data.items():
        transport, platform = key.decode().split(':')
        if id == int(platform):
            rows.append(json.loads(value))
    server_time = int(now())
    platforms = []
    for platform in rows:
        if platform['eta_time'] < server_time:
            pipe.hdel(TKeys.ETA, TKeys.eta_key(platform['transport_id'], id))
            continue
        platform['eta_time'] = platform['eta_time'] - server_time
        if routes:
            if platform['line_id'] in routes:
                platforms.append(platform)
        else:
            platforms.append(platform)
    resp = {
        "transports": platforms,
        "time": server_time
    }
    pipe.execute()
    return http_ok(resp)



