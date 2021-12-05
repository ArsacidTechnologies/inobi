import psycopg2
from inobi.config import SQL_CONNECTION
from inobi.transport.configs import TRACCAR_SQL_CONNECTION
from .transport_v2 import _get_by_ids, get_by_id
from inobi.transport.traccar_md.remote_db import get_positions, dump_day_report as ddr, get_raw_positions
from inobi.utils import date_range
import getpass

def get_summary(*, ids, start_date, end_date, organization):
    log_file = open(f"/home/{getpass.getuser()}/log.txt", "w")
    log_file.write("TEST, IDS:\n" + str(ids) + "\n")
    log_file.write("TEST, START_DATE:\n" + str(start_date) + "\n")
    log_file.write("TEST, ORGANIZATION:\n" + str(organization) + "\n")
    log_file.write("TEST, END_DATE:\n" + str(end_date) + "\n")
    with psycopg2.connect(SQL_CONNECTION) as conn:
        transports = _get_by_ids(conn, ids, organization)
    log_file.write("TEST, TRANSPORTS:\n" + str(transports) + "\n")
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        positions = get_positions(conn, transports, start_date, end_date)
        log_file.write("TEST, POSITIONS:\n" + str(positions) + "\n")
        return positions


def dump_report(date, end_date=None):
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        if end_date:
            for day in date_range(date, end_date):
                ddr(conn, day)
        else:
            ddr(conn, date)

        conn.commit()


def get_transport_time_line(transport_id, start_date, end_date, organization, frequency=None):
    transport = get_by_id(transport_id, organization)
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        positions = get_raw_positions(conn, transport.device_id, start_date, end_date, frequency=frequency)

        return positions

