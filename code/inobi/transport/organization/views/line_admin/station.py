from inobi.transport.organization import bp
from inobi.utils.converter import converted
from inobi.utils import http_ok
from inobi.security import secured
from flask_cors import cross_origin
from inobi.transport.organization.db.line_admin import station as db
from inobi.transport.organization.utils import organization_required
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec


@bp.route('/v1/stations', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
@converted()
def stations_post(organization, name: str, full_name: str, platforms: list=None):
    if platforms:
        for platform in platforms:
            if not isinstance(platform, dict):
                raise BaseInobiException('platforms must be {"platforms":[{"lat":123, "lng":123}, ...]}',
                                         ec.INCORRECT_PLATFORM_STRUCTURE, 400)
            if 'lat' not in platform or 'lng' not in platform:
                raise BaseInobiException('platforms must be {"platforms":[{"lat":123, "lng":123}, ...]}',
                                         ec.INCORRECT_PLATFORM_STRUCTURE, 400)
            for k, v in platform.items():
                if not isinstance(v, (float, int)):
                    raise BaseInobiException('platforms must be {"platforms":[{"lat":123, "lng":123}, ...]}',
                                                 ec.INCORRECT_PLATFORM_STRUCTURE, 400)
    station = db.create(organization=organization, name=name, full_name=full_name, platforms=platforms)
    return http_ok(station)


@bp.route('/v1/stations/<int:id>', methods=['GET'])
@cross_origin()
@secured()
@organization_required(is_table=False)
def stations_get(organization, id):
    station = db.get(id, organization)
    return http_ok(station)


@bp.route('/v1/stations/<int:id>', methods=['PUT'])
@cross_origin()
@secured()
@organization_required(is_table=True)
@converted()
def stations_patch(organization, id, name: str, full_name: str):
    station = db.update(id=id, organization=organization, name=name, full_name=full_name)
    return http_ok(station)


@bp.route('/v1/stations/<int:id>', methods=['DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
def stations_delete(organization, id):
    station = db.delete(id, organization)
    return http_ok(station)


@bp.route('/v1/stations', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
def stations_get_list(organization):
    stations = db.list_(organization)
    return http_ok(dict(data=stations))


@bp.route('/v1/stations/<int:id>/platforms', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=True)
@converted()
def station_platforms_post(id, organization, platforms: list):
    station = db.link_platforms(organization, id, platforms)
    return http_ok(dict(data=station))

