from inobi.transport.DataBase.transport_report import dump_report
from inobi.utils import getargs, http_err, http_ok
from inobi.utils.converter import converted

from inobi.transport import transport_bp as bp
from flask import request
from datetime import datetime, timedelta
from inobi.transport.organization.views.report import out_of_route, trips
from inobi.transport.traccar_md.remote_db import dump_reports, get_positions_by_filter
from inobi.transport.DataBase.models import Transport
from inobi.transport.configs import TRACCAR_SQL_CONNECTION
import psycopg2


@bp.route('/cron/dump_report')
def dp_report_view():
    date, end_date = getargs(request, 'date', 'end_date')
    if not date:
        date = datetime.now().date() - timedelta(1)
    else:
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return http_err('date is not matching the pattern YYYY-MM-DD', 400)
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return http_err('end_date is not matching the pattern YYYY-MM-DD', 400)
        if date > end_date:
            return http_err('end_date must be greater than date')
        if date == end_date:
            end_date = None
    dump_report(date, end_date)
    dump_all_reports()
    return http_ok(date=date, end_date=end_date)


@bp.route('/cron/dump_all_report')
@converted()
def dump_all_reports(date: str=None):
    if not date:
        date = datetime.now().date() - timedelta(1)
    else:
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return http_err('date is not matching the pattern YYYY-MM-DD', 400)
    start_date = datetime(date.year, date.month, date.day, hour=0, minute=0, second=0)
    end_date = datetime(date.year, date.month, date.day, hour=23, minute=59, second=59)
    cycles = 0
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        for transport in Transport.query.all():
            positions = get_positions_by_filter(conn, transport.device_id, start_date, end_date)
            if not positions:
                continue
            oor_positions = []
            for i, row in enumerate(positions):
                if row and row[5] == 1.0:
                    oor_positions.append(row)
            trip, total = out_of_route.get_calc_trips(transport, start_date, end_date, positions=oor_positions,
                                                      coordinate_count=True)
            for t in trip:
                trip_coordinates = []
                count = len(t['coordinates'])
                if count <= 20:
                    continue
                step = int(count / 20)
                for i in range(0, count, step):
                    trip_coordinates.append(t['coordinates'][i])
                trip_coordinates.append(t['coordinates'][count-1])
                t['coordinates'] = trip_coordinates

            oor = {
                "trips": trip,
                "total": total
            }
            trip, total = trips.get_calc_trips(transport, start_date, end_date, positions=positions,
                                               coordinate_count=True, pop_coordinates=True)
            _trips = {
                "trips": trip,
                "total": total
            }
            stop, total = trips.get_calc_stops(transport, start_date, end_date, positions=positions)
            _stops = {
                "stops": stop,
                "total": total
            }
            dump_reports(conn, transport.id, start_date.date(), oor, _trips, _stops)
            cycles += 1
    return http_ok(cycles=cycles)
