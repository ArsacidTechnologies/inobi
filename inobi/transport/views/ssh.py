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


def parse_data(raw: dict):
    if 'ssh' in raw or 'ssh_info' in raw:
        data = {
            k: v
            for k, v in raw.items() if k in ['ssh', 'ssh_info', 'device_id']
        }
        return data
    return dict()


@route('/v1/ssh')
@secured(scope.Transport.ADMIN)
def ssh_active_sessions():
    redis = getredis(RedisSegments.BUSES_V2)
    transports = redis.hgetall(TKeys.TRANSPORTS)
    unknowns = redis.hgetall(TKeys.UNKNOWNS)

    finals = []

    for k, v in {**transports, **unknowns}.items():
        data = parse_data(pickle.loads(v))
        if data:
            finals.append(data)

    return http_ok({'data': finals})


@route('/v1/ssh/<device_id>', methods=['POST'])
@secured(scope.Transport.ADMIN)
@converted()
def ssh_view(device_id, remote_port: int,
             host: str = SSHConf.DEFAULT_HOST, port: int = SSHConf.DEFAULT_PORT,
             _additional_cmd_args: list = (), _additional_envvars: dict=None):
    if any(not isinstance(arg, str) for arg in _additional_cmd_args):
        raise TransportException('additional_cmd_args: [str, str]', ec.INVALID_FORMAT, 400)

    redis = getredis(RedisSegments.BUSES_V2)
    transport = Transport.query.filter(Transport.device_id == device_id).first()
    ssh_data = {
        'remote_port': remote_port,
        'host': host,
        'port': port,
        '_additional_cmd_args': _additional_cmd_args,
        '_additional_envvars': _additional_envvars
    }
    if not transport:
        ping_data = redis.hget(TKeys.UNKNOWNS, device_id)
        if ping_data:
            ping_data = pickle.loads(ping_data)
            ping_data['ssh'] = ssh_data
            redis.hset(TKeys.UNKNOWNS, device_id, pickle.dumps(ping_data))
    else:
        redis_key = '{}:{}'.format(transport.line_id, transport.device_id)
        ping_data = redis.hget(TKeys.TRANSPORTS, redis_key)
        if ping_data:
            ping_data = pickle.loads(ping_data)
            ping_data['ssh'] = ssh_data
            redis.hset(TKeys.TRANSPORTS, redis_key, pickle.dumps(ping_data))
    if not ping_data:
        raise TransportException('transport is dead', ec.DEAD_TRANSPORT, 409)

    return http_ok(parse_data(ping_data))


@route('/v1/ssh/<device_id>', methods=['GET'])
@secured(scope.Transport.ADMIN)
def ssh_view_info(device_id):
    redis = getredis(RedisSegments.BUSES_V2)
    transport = Transport.query.filter(Transport.device_id == device_id).first()
    if not transport:
        ping_data = redis.hget(TKeys.UNKNOWNS, device_id)
    else:
        redis_key = '{}:{}'.format(transport.line_id, transport.device_id)
        ping_data = redis.hget(TKeys.TRANSPORTS, redis_key)
    if ping_data:
        ping_data = pickle.loads(ping_data)
    return http_ok(parse_data(ping_data))


@route('/v1/ssh/<device_id>', methods=['DELETE'])
@secured(scope.Transport.ADMIN)
@converted()
def ssh_view_delete(device_id):
    redis = getredis(RedisSegments.BUSES_V2)
    transport = Transport.query.filter(Transport.device_id == device_id).first()
    if not transport:
        ping_data = redis.hget(TKeys.UNKNOWNS, device_id)
        if ping_data:
            ping_data = pickle.loads(ping_data)
            ping_data['ssh'] = None
            redis.hset(TKeys.UNKNOWNS, device_id, pickle.dumps(ping_data))
    else:
        redis_key = '{}:{}'.format(transport.line_id, transport.device_id)
        ping_data = redis.hget(TKeys.TRANSPORTS, redis_key)
        if ping_data:
            ping_data = pickle.loads(ping_data)
            ping_data['ssh'] = None
            redis.hset(TKeys.TRANSPORTS, redis_key, pickle.dumps(ping_data))

    return http_ok(parse_data(ping_data))

