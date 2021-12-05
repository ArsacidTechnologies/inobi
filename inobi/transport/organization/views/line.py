from ...organization import bp
from flask_cors import cross_origin
from inobi.security import secured
from inobi.utils import http_err, http_ok
from inobi.transport.DataBase.line_v2 import get_lines, get_line_detail
from inobi.transport import error_codes as ec


from inobi.utils.converter import converted, Modifier
from ...API.transport_v2 import get_all_transport
import itertools as IT


@bp.route('/v1/lines', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@converted
def line_list(token_data, with_transport: Modifier.BOOL = False):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403,
                        error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403,
                        error_codes=ec.ACCESS_DENIED)

    lines = get_lines(organization_id=organization_id, asdict=True)
    if with_transport:
        for l in lines:
            l['transport'] = []
        _lines_d = {
            l['id']: l
            for l in lines
        }
        transports = get_all_transport(organization_id=organization_id)
        for line_id, transports_gen in IT.groupby(transports, lambda t: t['line_id']):
            _lines_d[line_id]['transport'].extend(transports_gen)

    return http_ok(data=dict(data=lines), count=len(lines))


@bp.route('/v1/lines/<int:line>', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
def line_detail(line, token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403,
                        error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403,
                        error_code=ec.ACCESS_DENIED)
    line_detail = get_line_detail(line, organization_id)
    if not line_detail:
        return http_err('line not found', 404, error_code=ec.LINE_NOT_FOUND)
    return http_ok(dict(data=line_detail))