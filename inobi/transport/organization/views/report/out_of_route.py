from inobi.transport.organization import bp
from inobi.transport.organization.serializers.reports import ReportRequestSchema
from inobi.security import secured
from inobi.utils.converter import converted
from flask_cors import cross_origin
from inobi.utils import http_ok
from inobi.transport.organization.utils import organization_required
from inobi.transport.DataBase.models import Transport
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec
from inobi.security.scope import Transport as TransportScope

from inobi.transport.configs import TRACCAR_SQL_CONNECTION
import psycopg2
from inobi.transport.traccar_md.remote_db import get_positions_by_filter, get_out_of_route as get_dump

from .trip_utils import define_trips, define_dump_trips, get_trips_and_total, merge_totals


def get_dump_trips(transport, from_time, to_time):
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        rows = get_dump(conn, transport.id, from_time, to_time)
        if not rows:
            return None, None
        trips, total = define_dump_trips(rows)
    return trips, total


def get_calc_trips(transport, from_time, to_time, positions=None, coordinate_count=False, pop_coordinates=False):
    if not positions:
        with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
            # altitude 1 is defining out of route
            positions = get_positions_by_filter(conn, transport.device_id, from_time, to_time, altitude=1.0)
    trips, total = define_trips(positions, coordinate_count, pop_coordinates)
    return trips, total


@bp.route('/v1/reports/out_of_route', methods=['GET'])
@cross_origin()
@secured(TransportScope.VIEWER)
@organization_required(is_table=True)
@converted(rest_key='rest')
def out_of_route_report(id: int, from_time: str, to_time: str, organization, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
    transport = organization.transports.filter(Transport.id == id).first()
    if not transport:
        raise BaseInobiException('transport not found', ec.TRANSPORT_NOT_FOUND, 404)
    trips, total = get_trips_and_total(transport, from_time, to_time, get_calc_trips, get_dump_trips, merge_totals)
    return http_ok({
        "data": trips,
        "from_time": from_time.isoformat(),
        "to_time": to_time.isoformat(),
        "id": id,
        "total": total
    })
