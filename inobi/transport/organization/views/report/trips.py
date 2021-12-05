from inobi.transport.organization import bp
from inobi.transport.organization.serializers.reports import ReportRequestSchema
from inobi.security import secured
from inobi.utils.converter import converted
from flask_cors import cross_origin
from inobi.utils import http_ok
from inobi.transport.organization.utils import organization_required
from inobi.transport.DataBase.models import Transport
from inobi.transport.API.transport_v2 import get_bus_status_report
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec

from inobi.transport.configs import TRACCAR_SQL_CONNECTION
import psycopg2
from inobi.transport.traccar_md.remote_db import get_positions_by_filter, get_raw_positions_for_animation, get_trips as get_dump

from .trip_utils import define_trips, define_stops, define_dump_stops, define_dump_trips, get_trips_and_total, merge_totals
from inobi.security.scope import Transport as TransportScope
from datetime import datetime


def get_dump_trips(transport, from_time, to_time):
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        rows = get_dump(conn, transport.id, from_time, to_time)
        if not rows:
            return None, None
        trips, total = define_dump_trips(rows)
    return trips, total


def get_calc_trips(transport, from_time, to_time, positions=None, coordinate_count=False, pop_coordinates=True):
    if not positions:
        with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
            positions = get_positions_by_filter(
                conn, transport.device_id, from_time, to_time)
    trips, total = define_trips(positions, coordinate_count, pop_coordinates)
    return trips, total


def get_dump_stops(transport, from_time, to_time):
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        rows = get_dump(conn, transport.id, from_time, to_time)
        if not rows:
            return None, None
        trips, total = define_dump_stops(rows)
    return trips, total


def get_calc_stops(transport, from_time, to_time, positions=None):
    if not positions:
        with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
            positions = get_positions_by_filter(
                conn, transport.device_id, from_time, to_time)
    trips, total = define_stops(positions)
    return trips, total


def merge_stop_totals(total1, total2):
    total1['duration'] += total2['duration']
    return total1


@bp.route('/v1/reports/trips', methods=['GET'])
@cross_origin()
@secured(TransportScope.VIEWER)
@organization_required(is_table=True)
@converted(rest_key='rest')
def trips_report(id: int, from_time: str, to_time: str, organization, rest=None):

    print(f"[!!!!!!] from time is {from_time} to time is {to_time}")

    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
    transport = organization.transports.filter(Transport.id == id).first()
    if not transport:
        raise BaseInobiException(
            'transport not found', ec.TRANSPORT_NOT_FOUND, 404)
    trips, total = get_trips_and_total(
        transport, from_time, to_time, get_calc_trips, get_dump_trips, merge_totals)
    return http_ok({
        "data": trips,
        "from_time": from_time.isoformat(),
        "to_time": to_time.isoformat(),
        "id": id,
        "total": total
    })


@bp.route('/v1/reports/stops', methods=['GET'])
@cross_origin()
@secured(TransportScope.VIEWER)
@organization_required(is_table=True)
@converted(rest_key='rest')
def stops_report(id: int, from_time: str, to_time: str, organization, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
    transport = organization.transports.filter(Transport.id == id).first()
    if not transport:
        raise BaseInobiException(
            'transport not found', ec.TRANSPORT_NOT_FOUND, 404)
    trips, total = get_trips_and_total(
        transport, from_time, to_time, get_calc_stops, get_dump_stops, merge_stop_totals)
    return http_ok({
        "data": trips,
        "from_time": from_time.isoformat(),
        "to_time": to_time.isoformat(),
        "id": id,
        "total": total
    })


# NOTE - this api is ran on another microservice for only report processes
# NOTE - TIME FORMAT : Y-M-D H:M:S
# @bp.route('/v1/reports/status', methods=['GET'])
# @cross_origin()
# @secured(TransportScope.VIEWER)
# @organization_required(is_table=True)
# @converted(rest_key='rest')
# def status_report(id: int, from_time: str, to_time: str, organization, rest=None):
#     import requests
#     r_data = ReportRequestSchema().load({
#         "id": id,
#         "from_time": from_time,
#         "to_time": to_time
#     })
#     id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
#     from_time = from_time.isoformat()
#     to_time = to_time.isoformat()
#     response = requests.get(f"http://localhost:7366/avl/api/reports/status/{id}/{from_time}/{to_time}")
#     print(f"[!!!!!!] STATUS REPORT ======== {response.status_code}")


# NOTE - TIME FORMAT : Y-M-D H:M:S
@bp.route('/v1/reports/status', methods=['GET'])
@cross_origin()
@secured(TransportScope.VIEWER)
@organization_required(is_table=True)
@converted(rest_key='rest')
def status_report(id: int, from_time: str, to_time: str, organization, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": from_time,
        "to_time": to_time
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
    transport = organization.transports.filter(Transport.id == id).first()
    if not transport:
        raise BaseInobiException(
            'transport not found', ec.TRANSPORT_NOT_FOUND, 404)
    reports, total = get_bus_status_report(
        transport.device_id, from_time, to_time), {}
    return http_ok({
        "data": reports,
        "from_time": from_time.isoformat(),
        "to_time": to_time.isoformat(),
        "id": id,
        "total": total
    })


# NOTE - TIME FORMAT : Y-M-D H:M:S
@bp.route('/v1/reports/animation', methods=['GET'])
@cross_origin()
@secured(TransportScope.VIEWER)
@organization_required(is_table=True)
@converted(rest_key='rest')
def animation_report(id: int, time: str, organization, rest=None):
    r_data = ReportRequestSchema().load({
        "id": id,
        "from_time": time,
        "to_time": time.replace("00:00:00", "23:59:00")
    })
    id, from_time, to_time = r_data['id'], r_data['from_time'], r_data['to_time']
    transport = organization.transports.filter(Transport.id == id).first()
    if not transport:
        raise BaseInobiException(
            'transport not found', ec.TRANSPORT_NOT_FOUND, 404)
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        from_time = from_time.replace(hour=0, minute=0, second=0)
        to_time = to_time.replace(hour=23, minute=59, second=59)
        positions, total = get_raw_positions_for_animation(
            conn, transport.device_id, from_time, to_time), {}
    return http_ok({
        "data": positions,
        "from_time": from_time,
        "to_time": to_time,
        "id": id,
        "total": total
    })
