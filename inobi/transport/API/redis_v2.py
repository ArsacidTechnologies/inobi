from inobi.redis import getredis
from inobi.config import RedisSegments
from inobi.transport.DataBase.models import Transport
import pickle
from inobi.transport.configs import TKeys, RouteTypes
from inobi.transport.data_checker import convert_route
from inobi import db
from inobi.transport.DataBase.transport_v2 import get_by_device_id
import psycopg2
from inobi.config import SQL_CONNECTION


def delete(params=None, segment=RedisSegments.BUSES_V2):
    redis = getredis(segment)
    if not params:
        ok = redis.flushdb()
    else:
        ok = redis.delete(*params)
    return ok


def sync():
    redis = getredis(RedisSegments.BUSES_V2)
    pipe = redis.pipeline()
    transports = Transport.query.all()

    raw = redis.hgetall(TKeys.TRANSPORTS)
    with psycopg2.connect(SQL_CONNECTION) as conn:
        for k, v in raw.items():
            t_line, device_id = k.decode().split(':', 1)

            t_line = int(t_line)
            payload = pickle.loads(v)
            found = False
            for transport in transports:
                if device_id == transport.device_id:
                    _t, _e, organizations = get_by_device_id(conn=conn, mac=device_id)
                    found = True
                    route = transport.route
                    if payload.get('device_phone') and payload['device_phone'] != transport.device_phone:
                        transport.device_phone = payload['device_phone']
                        db.session.add(transport)
                    if payload.get('phone'):
                        if payload['phone'] != transport.device_phone:
                            transport.device_phone = payload['phone']
                            db.session.add(transport)
                        payload.pop('phone')

                    payload.update({
                        **transport.as_dict(),
                        "number": convert_route(route.name, route.type, (RouteTypes.TECHNICAL, RouteTypes.SHUTTLE_BUS)),
                        "type": route.type,
                        "organizations": organizations,
                        "city": organizations[0].city
                    })
                    if route.id != t_line:
                        pipe.hdel(TKeys.TRANSPORTS, k)
                    pipe.hset(TKeys.TRANSPORTS, "{}:{}".format(route.id, transport.device_id), pickle.dumps(payload))
            if not found:
                pipe.hdel(TKeys.TRANSPORTS, k)

    p = pipe.execute()
    db.session.commit()
    return p


