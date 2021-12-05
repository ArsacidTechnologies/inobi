from inobi.transport import route
from inobi.utils.converter import converted
from inobi.utils import http_ok
from inobi.transport.exceptions import TransportException
from inobi.transport.configs import SSHConf, TKeys
from inobi.transport import error_codes as ec
from inobi.config import RedisSegments
from inobi.security import secured, scope
from inobi.redis import getredis
from inobi.transport.DataBase.models import Transport
import pickle

from inobi.transport.API.redis_v2 import sync


def parse(data):
    if not data:
        return
    organizations = []
    if data.get('organizations'):
        organizations = [org._asdict() for org in data['organizations']]
    data['organizations'] = organizations
    data['path'] = list(data.get('path', []))
    return data


@route('/redis/v1', methods=['GET'])
@secured(scope.Transport.ADMIN)
def redis_list():
    redis = getredis(RedisSegments.BUSES_V2)
    raw = redis.hgetall(TKeys.TRANSPORTS)
    transports = []
    for k, v in raw.items():
        transports.append(parse(pickle.loads(v)))
    return http_ok({"data": transports})


@route('/redis/v1/<device_id>', methods=['GET'])
@secured(scope.Transport.ADMIN)
def redis_view_info(device_id):
    redis = getredis(RedisSegments.BUSES_V2)
    transport = Transport.query.filter(Transport.device_id == device_id).first()
    if not transport:
        ping_data = redis.hget(TKeys.UNKNOWNS, device_id)
    else:
        redis_key = '{}:{}'.format(transport.line_id, transport.device_id)
        ping_data = redis.hget(TKeys.TRANSPORTS, redis_key)
    if ping_data:
        ping_data = pickle.loads(ping_data)
    return http_ok(parse(ping_data))


@route('/redis/v1/sync', methods=['GET'])
@secured('transport_admin')
def redis_sync():
    ok = sync()
    return http_ok({"updated": len(ok)})
