from ...organization import bp
from inobi.utils import getargs, http_ok, http_err, converter
from flask import request, send_file, make_response
from flask_cors import cross_origin
from inobi.security import secured
from inobi.transport import error_codes as ec
from inobi.transport.DataBase.transport_report import get_summary, get_transport_time_line
from inobi.transport.organization.utils import save_to_xlsx
from uuid import uuid4
import os
from inobi.transport.configs import TRANSPORT_REPORT_DIRECTORY


@bp.route('/v1/buses/report', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
def transport_summary_report(token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403, error_code=ec.ACCESS_DENIED)
    transports, start_date, end_date = getargs(request, 'transports', 'start_date', 'end_date')
    if not isinstance(transports, list):
        return http_err('transports must be list', 400, error_code=ec.TRANSPORT_MUST_BE_LIST)
    for t_id in transports:
        if not isinstance(t_id, int):
            return http_err('transports must consist only digits', 400)
    if not isinstance(start_date, (int, float)):
        try:
            start_date = float(start_date)
        except:
            return http_err('start_date must be digit', 400, error_code=ec.START_DATE_MUST_BE_DIGIT)
    if not isinstance(end_date, (int, float)):
        try:
            end_date = float(end_date)
        except:
            return http_err('end_date must be digit', 400, error_code=ec.END_DATE_MUST_BE_DIGIT)
    if end_date <= start_date:
        return http_err('end_date must be greater then start_date', 400)
    report = get_summary(start_date=start_date, end_date=end_date, ids=transports, organization=organization_id)
    return http_ok(dict(data=report, start_date=start_date, end_date=end_date))


@bp.route('/v1/buses/report/xlsx', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
def xlsx_generator():
    report = request.get_json(silent=True, force=True)
    if not report:
        return http_err('json required', 400)
    if not report.get('title'):
        return http_err('title is missing', 400)
    if not report.get('data'):
        return http_err('data is missing', 400)
    if not isinstance(report['data'], list):
        return http_err('data must be list', 400)

    for item in report['data']:
        if not isinstance(item, dict):
            return http_err('data must be array of dict', 400)
    filename = '{}.xlsx'.format(uuid4())
    filename = os.path.join(TRANSPORT_REPORT_DIRECTORY, filename)
    file = save_to_xlsx(report, filename)
    fn = os.path.basename(filename)
    r = make_response(send_file(file, as_attachment=True, attachment_filename=fn))
    r.headers['X-Filename'] = fn
    return r


@bp.route('/v1/buses/log', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@converter.converted()
def transport_logs(token_data, id: int, start_date: float, end_date: float, frequency: int = 2):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403, error_code=ec.ACCESS_DENIED)
    if end_date <= start_date:
        return http_err('end_date must be greater then start_date', 400)
    report = get_transport_time_line(id, start_date, end_date, organization_id, frequency=frequency)
    return http_ok(dict(data=report, start_date=start_date, end_date=end_date))
