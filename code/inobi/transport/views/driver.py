
import time
import functools as FT
import typing as T
import collections as C
import pickle, json

import uuid

from flask import request

from .. import route as _route
from inobi.redis import getredis as _getredis, Redis
from inobi.config import RedisSegments
from inobi.utils.converter import converted, Modifier

from inobi.security import secured


from inobi import add_prerun_hook
from inobi.transport.configs import DriverConfig


from inobi.utils import http_ok, http_err, flask_timeit

from .. import error_codes

from inobi.transport.DataBase.transport_v2 import get_driver_transports
from inobi.transport.API.transport_v2 import update_driver_transports, unassign_driver_transport
from inobi.transport.organization.db.drivers import drivers_by_route
from inobi.transport.organization.utils import organization_required
from inobi import db

PREFIX = '/driver'

route = FT.partial(lambda endpoint, *args, **kwargs: _route(PREFIX + endpoint, *args, **kwargs), methods=('GET', 'POST'))
getredis = FT.partial(_getredis, db=RedisSegments.BUSES)    # type: T.Callable[[], Redis]


if DriverConfig.CLEANUP_ON_APP_START:
    def on_app_run():
        getredis().delete(RedisKeys.POINTS)

    add_prerun_hook(on_app_run)


class RedisKeys:
    POINTS = 'driver_points'


@route('/v1/test')
@flask_timeit
def transport_driver_test_v1():
    return 'OK transport driver test', 200


from geopy.distance import distance


def distance_in_circle(p1: dict, p2: dict,
                       circle_radius: float = DriverConfig.UPDATE_RATHER_THAN_CREATE_POINT_RADIUS
                       ) -> T.Optional[float]:
    p1i = p1['info']
    c1 = (p1i['lat'], p1i['lng'])

    p2i = p2['info']
    c2 = (p2i['lat'], p2i['lng'])

    kms = distance(c1, c2).kilometers
    if kms <= circle_radius:
        return kms


def get_points(driver, transport, type=None) -> T.List[T.Dict]:

    r = getredis()

    points = r.hget(RedisKeys.POINTS, transport['line_id'])

    if points is None:
        return []

    points = json.loads(points.decode())

    now = time.time()

    nonexpired_points = []
    points_to_show = []
    for p in points:
        if p['exp'] > now:
            nonexpired_points.append(p)
            if type is None or p['info']['type'] == type:
                points_to_show.append(p)

    if len(nonexpired_points) != len(points):
        r.hset(RedisKeys.POINTS, transport['line_id'], json.dumps(nonexpired_points, ensure_ascii=False))

    return points_to_show


def post_point(driver, transport, lat, lng, type=None, radius=DriverConfig.UPDATE_RATHER_THAN_CREATE_POINT_RADIUS,
               description=None, payload=None, exp=None) -> dict:

    if type is None:
        type = DriverConfig.DEFAULT_POINT_TYPE

    ts = time.time()

    data = {

        'id': str(uuid.uuid4()),

        'iss': driver['id'],
        'driver': {
            'id': driver['id'],
            'transport': transport['id'],
        },
        'time': ts,
        'exp': ts + exp,

        'info': {
            'type': type,
            'lat': lat,
            'lng': lng,
            'description': description,
            'payload': payload
        },
        'updates': [],
    }

    r = getredis()
    points = r.hget(RedisKeys.POINTS, transport['line_id'])

    points = [] if points is None else json.loads(points.decode())

    points_in_circle = dict()
    for p in points:
        if p['info']['type'] != data['info']['type']:
            continue
        d = distance_in_circle(data, p, circle_radius=radius)
        if d is not None:
            points_in_circle[d] = p

    if points_in_circle:
        nearest_point = min(points_in_circle.items(), key=lambda i: i[0])[1]
        nearest_point['exp'] = data['exp']

        # clearing unnecessary info from data
        del data['id']
        del data['updates']

        nearest_point['updates'].append(data)
        data = nearest_point
        # no need to put updated point back to points array
        # it is already in there and will be updated on dumps
    else:
        points.append(data)

    r.hset(RedisKeys.POINTS, transport['line_id'], json.dumps(points, ensure_ascii=False))

    return data


def delete_point(driver, transport, post_id) -> T.Optional[dict]:

    r = getredis()

    points = r.hget(RedisKeys.POINTS, transport['line_id'])
    points = [] if points is None else json.loads(points.decode())

    points_to_delete = [p for p in points if p['id'] == post_id]

    if len(points_to_delete) == 0:
        return None

    points_left = [p for p in points if p['id'] != post_id]

    r.hset(RedisKeys.POINTS, transport['line_id'], json.dumps(points_left, ensure_ascii=False))

    (deleted_point, ) = points_to_delete

    return deleted_point


@route('/v1/points', methods=('GET', 'POST', 'DELETE'))
@secured('transport_admin transport_driver')
@converted
@flask_timeit
def transport_driver_point_v1(token_data: dict, lat: float = None, lng: float = None, description: str = None,
                              payload: dict = None, exp: float = DriverConfig.DEFAULT_POINT_EXPIRATION_INTERVAL,
                              id: uuid.UUID = None, type: str = DriverConfig.DEFAULT_POINT_TYPE, radius: float = DriverConfig.UPDATE_RATHER_THAN_CREATE_POINT_RADIUS):

    transport = token_data['transport']
    driver = token_data['user']

    if request.method == 'GET':
        points = get_points(driver, transport, type=type)

        return http_ok(points=points, count=len(points))

    if request.method == 'POST':

        if not all([lat, lng]):
            return http_err("'lat' and 'lng' Parameters Required", 400,
                            error_code=error_codes.LAT_LNG_PARAMETER_REQUIRED)

        posted = post_point(
            driver=driver,
            transport=transport,
            lat=lat,
            lng=lng,
            type=type,
            radius=radius,
            description=description,
            payload=payload,
            exp=exp,
        )
        return http_ok(accepted_point=posted)

    if request.method == 'DELETE':

        if not all([id]):
            return http_err("'id' Parameter Required", 400,
                            error_code=error_codes.ID_PARAMETER_REQUIRED)

        deleted = delete_point(
            driver=driver,
            transport=transport,
            post_id=str(id)
        )

        if deleted is None:
            return http_err("No Point With Such Identifier ({})".format(id), 404,
                            error_code=error_codes.POINT_NOT_FOUND)

        return http_ok(deleted_point=deleted)

    return http_err('Method Misunderstood', 405)


@route('/v1/transports', methods=['GET'])
@secured('transport_viewer transport_driver')
def driver_transport(token_data, scopes):
    if 'transport_driver' not in scopes:
        return http_err('FORBIDDEN', 403, error_code=error_codes.ACCESS_DENIED)
    user_id = token_data['user']['id']
    transports = get_driver_transports(driver=user_id, to_dict=True)
    return http_ok(transports=transports)


@route('/v1/transports', methods=['POST', 'DELETE'])
@secured('transport_viewer transport_driver')
@converted
def change_driver_transport(token_data, scopes, transport: int = None):
    if 'transport_driver' not in scopes:
        return http_err('FORBIDDEN', 403, error_code=error_codes.ACCESS_DENIED)
    user_id = token_data['user']['id']
    if request.method == 'POST':
        if not transport:
            return http_err('transport required', 400)
        updated = update_driver_transports(driver=user_id, transport=transport)
    elif request.method == 'DELETE':
        updated = unassign_driver_transport(driver=user_id)
    return http_ok(transport=updated)


@route('/v1/drivers', methods=['GET'])
@secured('transport_viewer transport_driver')
def get_drivers(token_data, scopes):
    if 'transport_driver' not in scopes:
        return http_err('FORBIDDEN', 403, error_code=error_codes.ACCESS_DENIED)
    transport = token_data['transport']
    drivers = [d._asdict() for d in drivers_by_route(transport['line_id'])]
    return http_ok(drivers=drivers)


import psycopg2
from inobi.config import SQL_CONNECTION


@route('/v1/version', methods=['GET'])
@secured('transport_viewer transport_driver')
def drivers_app_version(token_data):
    driver_id = token_data['user']['id']
    sql = '''
        select t.payload from transport_organizations t
        inner join transport_organization_drivers tod
        on t.id = tod.organization
        inner join "users" u
        on u.id = tod."user"
        
        where u.id = %s
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (driver_id,))
            payload = cursor.fetchone()
            if not payload:
                return http_ok({"app_version": 0})
            else:
                payload = payload[0]
    try:
        payload = json.loads(payload)
    except json.JSONDecodeError:
        payload = {}

    version = payload.get('driver_app_version', 0)
    return http_ok({"app_version": version})


@route('/v1/version', methods=['POST'])
@secured('transport_admin')
@organization_required(is_table=True)
@converted
def drivers_app_version_save(organization, version: int):

    try:
        payload = json.loads(organization.payload)
    except json.JSONDecodeError:
        payload = {}
    payload['driver_app_version'] = version
    organization.payload = json.dumps(payload)

    db.session.add(organization)
    db.session.commit()

    return http_ok({"version": version})


from inobi.security import scope
from inobi.transport.data_checker import check_ping, parse
from inobi.transport.API.transport_v2 import ping_handler


@route('/v1/ping', methods=['POST', "GET"])
@secured([scope.Transport.ADMIN,
          scope.Transport.DRIVER
          ])
@converted(rest_key="rest")
def driver_ping_view(token_data, scopes, lat: float, lon: float = None, lng: float = None,
              bearing: float = None, speed: float = None, rest: dict = None):
    if lng is None and lon is None:
        return http_err("'lon' Parameter Is Missing", 400)

    data = dict(
        lat=lat,
        lng=lon or lng or 0.0
    )
    check_ping(rest)
    kwargs = dict(rest)
    parse(kwargs)
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
        return http_err('driver token required', 403, error_code=error_codes.ACCESS_DENIED)

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

    ping = ping_handler(_id, data['lat'], data['lng'], **kwargs)

    return http_ok(data=dict(data=ping))
