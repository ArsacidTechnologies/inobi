from . import station, out_of_route, trips, transports

from inobi.transport.DataBase.transport_changes import get_driver_report
from inobi.transport.organization import bp
from inobi.utils import getargs, http_ok, http_err
from flask import request, jsonify
from flask_cors import cross_origin
from inobi.security import secured
from inobi.transport import error_codes as ec



@bp.route('/v1/drivers/report')
@cross_origin()
@secured('transport_viewer')
def driver_report(token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403, error_code=ec.ACCESS_DENIED)
    driver, start_date, end_date = getargs(request, 'driver', 'start_date', 'end_date')
    if not isinstance(driver, int):
        try:
            driver = int(driver)
        except:
            return http_err('driver must be digit', 400, error_code=ec.DRIVER_MUST_BE_DIGIT)
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
    report = get_driver_report(start_date, end_date, driver, organization_id)
    return http_ok(dict(data=report, start_date=start_date, end_date=end_date))


from .out_of_route import get_calc_trips