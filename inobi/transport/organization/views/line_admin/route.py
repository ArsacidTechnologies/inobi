from inobi.transport.organization import bp
from inobi.utils.converter import converted
from inobi.utils import http_ok
from inobi.security import secured
from flask_cors import cross_origin
from inobi.transport.organization.db.line_admin import route as db
from inobi.transport.organization.utils import organization_required
from inobi.transport.configs import RouteTypes, DirectionTypes
from inobi.transport.exceptions import BaseInobiException
from inobi.transport import error_codes as ec


@bp.route('/v1/routes', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
@converted()
def lines_post(organization, name, type: str, from_name: str, to_name: str, directions: list=None, excluded: bool = False):
    if type not in RouteTypes.ALL:
        raise BaseInobiException('type must be one of {}'.format(RouteTypes.ALL), ec.INCORRECT_ROUTE_TYPE, 400)
    # if type not in (RouteTypes.TECHNICAL, RouteTypes.SHUTTLE_BUS):
    #     try:
    #         name = int(name)
    #     except ValueError:
    #         raise BaseInobiException('name must be digit', ec.NAME_MUST_BE_DIGIT, 400)
    if directions:
        if len(directions) != 2:
            raise BaseInobiException('must be 2 directions', ec.DIRECTION_MUST_BE_2, 400)
        for direction in directions:
            if not direction.get('line') or not direction.get('type'):
                raise BaseInobiException('{"directions": [{"line":"string", "type":"backward"}]}',
                                         ec.DIRECTION_FORMAT_INCORRECT, 400)
            if not isinstance(direction['line'], str) or not isinstance(direction['type'], str):
                raise BaseInobiException('{"directions": [{"line":"string", "type":"backward"}]}',
                                         ec.DIRECTION_FORMAT_INCORRECT, 400)
            if direction['type'] not in DirectionTypes.ALL:
                raise BaseInobiException('type must be one of {}'.format(DirectionTypes.ALL),
                                         ec.INCORRECT_DIRECTION_TYPE, 400)
    obj = db.create(organization=organization, name=name, type=type, from_name=from_name, to_name=to_name,
                    directions=directions, excluded=type == RouteTypes.TECHNICAL or excluded)
    return http_ok(obj)


@bp.route('/v1/routes/<int:id>', methods=['GET'])
@cross_origin()
@secured()
@organization_required(is_table=False)
def lines_get(organization, id):
    obj = db.get(id, organization)
    return http_ok(obj)


@bp.route('/v1/routes/<int:id>', methods=['PUT'])
@cross_origin()
@secured()
@organization_required(is_table=True)
@converted()
def lines_patch(organization, id, name, type, from_name: str, to_name: str):
    if type not in RouteTypes.ALL:
        raise BaseInobiException('type must be one of {}'.format(RouteTypes.ALL), ec.INCORRECT_ROUTE_TYPE, 400)
    obj = db.update(id=id, organization=organization, name=name, type=type, from_name=from_name, to_name = to_name)
    return http_ok(obj)


@bp.route('/v1/routes/<int:id>', methods=['DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
def lines_delete(organization, id):
    obj = db.delete(id, organization)
    return http_ok(obj)


@bp.route('/v1/routes', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
def lines_get_list(organization):
    obj = db.list_(organization)
    return http_ok(dict(data=obj))


@bp.route('/v1/routes/<int:id>/directions', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
@converted()
def route_directions_post(id, organization, directions: list):
    # if len(directions) != 2:
    #     raise BaseInobiException('2_DIR_REQUIRED', ec._2_DIR_REQUIRED, 400)
    route = db.link_directions(organization, id, directions)
    return http_ok(route)
