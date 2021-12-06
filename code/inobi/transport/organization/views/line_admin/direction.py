from inobi.transport.organization import bp
from inobi.utils.converter import converted
from inobi.utils import http_ok
from inobi.security import secured
from flask_cors import cross_origin
from inobi.transport.organization.db.line_admin import direction as db
from inobi.transport.organization.utils import organization_required
from inobi.transport.configs import DirectionTypes
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec


@bp.route('/v1/directions', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def directions_post(organization, type: str,  line: str, route_id: int):
    if type not in DirectionTypes.ALL:
        raise BaseInobiException('type must be one of {}'.format(DirectionTypes.ALL), ec.INCORRECT_DIRECTION_TYPE, 400)
    obj = db.create(organization=organization, line=line, type=type, route_id=route_id)
    return http_ok(obj)


@bp.route('/v1/directions/<int:id>', methods=['GET'])
@cross_origin()
@secured()
@organization_required(is_table=False)
def directions_get(organization, id):
    obj = db.get(id, organization)
    return http_ok(obj)


@bp.route('/v1/directions/<int:id>', methods=['PUT'])
@cross_origin()
@secured()
@organization_required(is_table=False)
@converted()
def directions_patch(organization, id, line: str, type: str):
    if type not in DirectionTypes.ALL:
        raise BaseInobiException('type must be one of {}'.format(DirectionTypes.ALL), ec.INCORRECT_DIRECTION_TYPE, 400)
    obj = db.update(id=id, organization=organization, line=line, type=type)
    return http_ok(obj)


@bp.route('/v1/directions/<int:id>', methods=['DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
def directions_delete(organization, id):
    obj = db.delete(id, organization)
    return http_ok(obj)


@bp.route('/v1/directions', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def directions_get_list(organization, free: bool=False):
    obj = db.list_(organization, free=free)
    return http_ok(dict(data=obj))


@bp.route('/v1/directions/<int:id>/platforms', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def direction_platforms_post(id, organization, platforms: list):
    direction = db.link_platforms(organization, id, platforms)
    return http_ok(dict(data=direction))
