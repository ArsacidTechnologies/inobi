from ...organization import bp
from inobi.security import secured, scope
from flask_cors import cross_origin
from inobi.utils import http_err, http_ok
from ..db.organization import get_organization_data, dump_transports_to_organization

from inobi.transport import error_codes as ec


@bp.route('/v1/data', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
def organization_data(token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403,
                        error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403,
                        error_code=ec.ACCESS_DENIED)

    organization_data = get_organization_data(organization_id)
    return http_ok(organization_data)


@bp.route('/v1/dump-transports/<int:organization_id>', methods='POST'.split())
@cross_origin()
@secured(scope.Transport.INOBI)
def organization_sync_v1(organization_id):

    transports = dump_transports_to_organization(organization_id)

    return http_ok(
        count=len(transports),
        dumped_transports=transports,
    )
