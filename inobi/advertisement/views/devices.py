

from ..db import devices

from .. import bp

from flask_cors import cross_origin

from inobi.security import secured, scope

from inobi.utils import http_ok, http_err, with_request_as_argument, recursive_dictify
from inobi.utils.converter import converted, Modifier

import datetime


@bp.route('/v1/data/', methods='GET'.split())
@cross_origin()
@secured(scope.Advertisement.VIEWER)
@converted
def data_v1():

    return http_ok(groups=recursive_dictify(devices.fetch_groups(groups=None)),
                   devices=recursive_dictify(devices.fetch(groups=None)),
                   )


@bp.route('/v1/devices/', methods='GET POST'.split())
@cross_origin()
@with_request_as_argument
def devices_v1(request):

    if request.method == 'GET':
        return devices_v1_get()
    else:
        return devices_v1_post()


@secured(scope.Advertisement.VIEWER)
@converted
def devices_v1_get(with_groups: Modifier.BOOL = False):
    return http_ok(devices=recursive_dictify(devices.fetch(groups=with_groups)))


@secured(scope.Advertisement.ADMIN)
@converted
def devices_v1_post(device_id: str,
                    name: str = None,
                    description: str = None,
                    enabled: Modifier.BOOL = True,
                    group_id: int = None,
                    city_id: int = None,
                    location: dict = None,
                    ):
    return http_ok(device=recursive_dictify(devices.create(device_id, name, description, enabled, group_id, city_id, location)))


@bp.route('/v1/devices/<int:device_id>/', methods='GET PUT PATCH DELETE'.split())
@cross_origin()
@with_request_as_argument
def device_v1(request, device_id: int):

    if request.method == 'GET':
        return device_v1_get(device_id)
    elif request.method == 'DELETE':
        return device_v1_delete(device_id)
    else:
        return devices_v1_update(device_id=device_id)


@secured(scope.Advertisement.VIEWER)
def device_v1_get(device_id):

    d = devices.fetch(id=device_id)

    if d is None:
        return http_err('Not Found', 404)

    return http_ok(device=recursive_dictify(d))


@secured(scope.Advertisement.ADMIN)
def device_v1_delete(device_id):

    d = devices.fetch(id=device_id)

    if d is None:
        return http_err('Not Found', 404)

    d.delete()

    return http_ok(deleted=recursive_dictify(d))


@secured(scope.Advertisement.ADMIN)
@converted(rest_key='values')
def devices_v1_update(*, device_id, values: dict):

    d = devices.fetch(id=device_id)

    if d is None:
        return http_err('Not Found', 404)

    devices.update(d, values)

    return http_ok(device=recursive_dictify(d))


@bp.route('/v1/device-groups/', methods='GET POST'.split())
@cross_origin()
@with_request_as_argument
def groups_v1(request):

    if request.method == 'GET':
        return groups_v1_get()
    else:
        return groups_v1_post()


@secured(scope.Advertisement.VIEWER)
@converted
def groups_v1_get(with_groups: Modifier.BOOL = False):
    return http_ok(groups=recursive_dictify(devices.fetch_groups(groups=with_groups)))


@secured(scope.Advertisement.ADMIN)
@converted
def groups_v1_post(name: str,
                   description: str = None,
                   enabled: Modifier.BOOL = True,
                   parent_group_id: int = None,
                   location: dict = None,
                   city_id: int = None,
                   ):

    return http_ok(group=recursive_dictify(devices.create_group(name, description, enabled, parent_group_id, location, city_id).asdict()))


@bp.route('/v1/device-groups/<int:group_id>/', methods='GET PUT PATCH DELETE'.split())
@cross_origin()
@with_request_as_argument
def group_v1(request, group_id: int):

    if request.method == 'GET':
        return group_v1_get(group_id)
    elif request.method == 'DELETE':
        return group_v1_delete(group_id)
    else:
        return group_v1_update(group_id=group_id)


@secured(scope.Advertisement.VIEWER)
def group_v1_get(group_id):

    g = devices.fetch_group(id=group_id)

    if g is None:
        return http_err('Not Found', 404)

    return http_ok(group=recursive_dictify(g))


@secured(scope.Advertisement.ADMIN)
def group_v1_delete(group_id):

    g = devices.fetch_group(id=group_id)

    if g is None:
        return http_err('Not Found', 404)

    g.delete()

    return http_ok(deleted=recursive_dictify(g))


@secured(scope.Advertisement.ADMIN)
@converted(rest_key='values')
def group_v1_update(*, group_id, values: dict):

    g = devices.fetch_group(id=group_id)

    if g is None:
        return http_err('Not Found', 404)

    devices.update_group(g, values)

    return http_ok(group=recursive_dictify(g))
