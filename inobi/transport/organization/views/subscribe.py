from ...organization import bp
from inobi.security import secured
from flask_cors import cross_origin
from flask import request
from inobi.utils import http_err, http_ok
from ...API.subscribe_v2 import subscribe, admin_subscribe
from inobi.transport import error_codes as ec


@bp.route('/v1/subscribe', methods=['GET', 'POST'])
@cross_origin()
@secured(['transport_viewer'])
def v2_subscribe_view(token_data):
    if request.method == 'POST':
        req = request.get_json(force=True, silent=True)
        if not req:
            return http_err('json is required', 400, error_code=ec.JSON_REQUIRED)
        _type = req.get('type', 'admin')
        line_id = req.get('line_id', None)
        if line_id == 'all':
            line_id = None
        inactive = req.get('inactive', False)
    else:
        inactive = False
        line_id = None
        _type = 'admin'
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err('Organization Data Is Missing', 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err('Organization Id Is Missing', 403, error_code=ec.ACCESS_DENIED)
    if _type not in ['admin', 'public']:
        return http_err('type argument is unknown, "admin" "public" available', 400, error_code=ec.TYPE_NOT_FOUND)
    subscribes = admin_subscribe(line_id, inactive, organization_id=organization_id)
    return http_ok(dict(data=subscribes), count=len(subscribes))
