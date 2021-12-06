from inobi.transport.DataBase.classes import Transport as transport_db, TransportDriverChanges, Route, TransportOrganization
from inobi.transport.DataBase.classes import BusInfo
from inobi.config import SQL_CONNECTION
import psycopg2
from psycopg2 import errorcodes
import json
import time
from inobi.transport import error_codes as ec
import typing as T
from inobi.utils import connected
from inobi.transport.exceptions import TransportException
from datetime import datetime

def get_conn(sql_connection=SQL_CONNECTION):
    return psycopg2.connect(sql_connection)



def save_bus_info(device_id: int, lat: float, lng: float, status: int, time: int, total_time_on: int = 0):
    SQL = '''
            insert into bus_info (device_id, lat, lng, status, time, total_time_on)
            values(%s, %s, %s, %s, %s, %s) returning *
          '''
    
    params = (device_id, lat, lng, status, time, total_time_on)
    conn = get_conn()
    with conn.cursor() as cursor:
        cursor.execute(SQL, params)
        conn.commit()
        row = cursor.fetchone()
        info = BusInfo.make_from_db_row(row)
        return info

def get_bus_info_records(device_id: str, conn=None):
    if not conn: conn = psycopg2.connect(SQL_CONNECTION)
    else: conn = conn
    with conn.cursor() as cursor:
        cursor.execute("SELECT status, time, total_time_on FROM bus_info WHERE device_id = %s order by time desc;", (device_id,))
        rows = cursor.fetchall()
        return rows


def calculate_total_time_on(device_id: str, from_time: datetime, to_time: datetime):
    from_time = from_time.replace(hour=0, minute=0, second=0)
    from_time_date = from_time.date()
    from_time_time = from_time.time()
    from_time_str = str(from_time_date) + ' ' +  str(from_time_time)
    from_timestamp = int(datetime.strptime(from_time_str, '%Y-%m-%d %H:%M:%S').timestamp()) # store timestamp of utc
    # ===========================================================
    to_time = to_time.replace(hour=23, minute=59, second=59)
    to_time_date = to_time.date()
    to_time_time = to_time.time()
    to_time_str = str(to_time_date) + ' ' +  str(to_time_time)
    to_timestamp = int(datetime.strptime(to_time_str, '%Y-%m-%d %H:%M:%S').timestamp()) # store timestamp of utc

    with psycopg2.connect(SQL_CONNECTION).cursor() as cursor:
        if from_time.utcoffset(): # change the timezone of database to get the query based on the client timezone
            tzname = from_time.utcoffset().total_seconds() / 3600
            cursor.execute('set timezone=%s', (tzname,))
        cursor.execute("""
                        select count(*) from (select  time,device_id,status,lag(status) over(order by time ) as prev_status from bus_info) bus_info 
                        where (prev_status = %s and status = %s and device_id = %s and time between %s and %s)
                        or (prev_status = %s and status = %s and device_id = %s and time between %s and %s);
                        """, (1, 0, device_id, from_timestamp, to_timestamp, 0, 1, device_id, from_timestamp, to_timestamp))
        number_of_status_changes = cursor.fetchone()[0]
        
        cursor.execute("SELECT time FROM bus_info WHERE time > %s and device_id = %s;", (from_timestamp, device_id))
        first_match_with_from = cursor.fetchone()
        if first_match_with_from:
            first_match_with_from = first_match_with_from[0]
        else:
            first_match_with_from = 0
        
        cursor.execute("SELECT time FROM bus_info WHERE time < %s and device_id = %s order by time desc;", (to_timestamp, device_id))
        first_match_with_to = cursor.fetchone()
        if first_match_with_to:
            first_match_with_to = first_match_with_to[0]
        else:
            first_match_with_to = 0

        cursor.execute("SELECT total_time_on FROM bus_info WHERE time = %s and device_id = %s;", (str(first_match_with_from), device_id))
        from_total_time_on = cursor.fetchone()
        if from_total_time_on:
            from_total_time_on = from_total_time_on[0]
        else:
            from_total_time_on = 0
        
        cursor.execute("SELECT total_time_on FROM bus_info WHERE time = %s and device_id = %s;", (str(first_match_with_to), device_id))
        to_total_time_on = cursor.fetchone()
        if to_total_time_on:
            to_total_time_on = to_total_time_on[0]
        else:
            to_total_time_on = 0

    if first_match_with_from == 0 or first_match_with_to == 0:
        return [{"device_id": device_id, "total_time_on": 0, "total_time_off": 0, "number_of_status_changes": number_of_status_changes}]
    else:
        total_time_on = to_total_time_on - from_total_time_on
        total_time_off = (first_match_with_to - first_match_with_from) - total_time_on
        if total_time_off < 0: # NOTE - from is greater than to - this is a bug from the box itself
            return [{"device_id": device_id, "total_time_on": 0, "total_time_off": 0, "number_of_status_changes": number_of_status_changes}]
        else:
            return [{"device_id": device_id, "total_time_on": total_time_on, "total_time_off": total_time_off, "number_of_status_changes": number_of_status_changes}]


def get_buses_info(conn=None):
    if not conn: conn = psycopg2.connect(SQL_CONNECTION)
    else: conn = conn
    with conn.cursor() as cursor: 
        SQL = ''' SELECT * FROM bus_info '''
        cursor.execute(SQL)
        rows = cursor.fetchall()
        bus_infos = []
        for row in rows:
            row = BusInfo.make_from_db_row(row).asdict()
            bus_infos.append(row)
        return bus_infos
          


def save_transport_driver_changes(conn, transport_id: int, type_: str,
                                  prev: int, next: int, issuer: int, reason: str=None):
    sql = '''
        insert into transport_driver_changes
            (transport, time, type, prev, next, reason, issuer)
        values (%s, %s, %s, %s, %s, %s, %s)
        returning *
    '''
    if type_ not in ['driver', 'line']:
        raise TypeError('unknown type, "driver" and "line" allowed')
    params = (transport_id, time.time(), type_, prev, next, reason, issuer)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return TransportDriverChanges.make_from_db_row(cursor.fetchone())


def _save_transport_organization(conn, transport_id, organization_id):
    with conn.cursor() as cursor:
        sql = '''
            insert into transport_organization_transports
            values (%s, %s)
            returning *
        '''
        cursor.execute(sql, (organization_id, transport_id))
        saved = cursor.fetchone()
        return saved


def _save_transport(conn, device_id, ip, port, tts, line_id=None, name=None,
                    driver=None, device_phone=None, independent=True,
                    payload=None, device_type=None, **kwargs):
    with conn.cursor() as cursor:
        try:
            SQL = '''
                INSERT INTO transports
                    (device_id, line_id, name, driver, device_phone, independent, payload, device_type, ip, port, tts)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            '''
            params = (str(device_id), line_id, name, driver, device_phone, independent, payload, device_type, ip, port, tts)

            cursor.execute(SQL, params)
            row = cursor.fetchone()
            transport = transport_db.make_from_db_row(row)
            return transport
        except psycopg2.IntegrityError as e:
            if errorcodes.lookup(e.pgcode) == 'UNIQUE_VIOLATION':
                if 'device_id' in e.pgerror:
                    raise TransportException('device_id must be unique', code=ec.TRANSPORT_DEVICE_ID_MUST_BE_UNIQUE)
                if 'driver' in e.pgerror:
                    raise TransportException('driver already has a transport', code=ec.DRIVER_ALREADY_HAS_A_TRANSPORT)
            else:
                raise e


def _check_line_with_organization(conn, line, organization):
    with conn.cursor() as cursor:
        sql = '''
            select * from transport_organization_lines
            where 
                line = %s and
                organization = %s
        '''
        cursor.execute(sql, (line, organization))
        row = cursor.fetchone()
        if not row:
            raise TransportException('unknown line_id', code=ec.LINE_NOT_FOUND)
        else:
            return True


def _check_driver_with_organization(conn, driver, organization):
    with conn.cursor() as cursor:
        sql = '''
            select "user" from transport_organization_drivers
            where 
                "user" = %s and
                organization = %s
        '''
        cursor.execute(sql, (driver, organization))
        row = cursor.fetchone()
        if not row:
            raise TransportException('unknown driver', code=ec.DRIVER_NOT_FOUND)
        return row


def _check_transport_with_organization(*, conn: psycopg2.connect, transport: int, organization: int):
    with conn.cursor() as cursor:
        sql = '''
            select transport from transport_organization_transports tot
            where tot.organization = %s and tot.transport = %s
        '''
        cursor.execute(sql, (organization, transport))
        row = cursor.fetchone()
        if not row:
            raise TransportException('unknown transport', code=ec.TRANSPORT_NOT_FOUND)
        return row


def save(device_id, organization_id, ip, port, tts, line_id, name=None,
         driver=None, device_phone=None, independent=True,
         payload=None, **kwargs) -> transport_db:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        _check_line_with_organization(conn, line_id, organization_id)
        if driver:
            row = _check_driver_with_organization(conn, driver, organization_id)
            with conn.cursor() as cursor:
                sql = '''
                    update transports set driver = null where driver = %s
                '''
                cursor.execute(sql, row)
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        transport = _save_transport(conn,
                                    device_id,
                                    ip, port, tts,
                                    line_id,
                                    name, driver,
                                    device_phone, independent,
                                    payload, **kwargs)

        _save_transport_organization(conn, transport.id, organization_id)
        return transport


@connected
def get_by_device_id(conn, mac, *args, **kwargs):
    with conn.cursor() as cursor:
        sql = '''
            SELECT t.*, r.*
                FROM transports t
            INNER JOIN routes r 
                ON t.line_id = r.id 
            WHERE 
                t.device_id = %s
        '''

        cursor.execute(sql, (mac,))
        row = cursor.fetchone()
        if not row:
            return None, None, None

        transport = transport_db.make_from_db_row(row)
        route = Route.make_from_db_row(row, start_index=len(transport_db._fields))
        organizations_sql = '''
            SELECT o.* FROM transport_organizations o
            INNER JOIN transport_organization_transports tot
                ON o.id = tot.organization
            WHERE tot.transport = %s
        '''
        cursor.execute(organizations_sql, (transport.id,))
        org_rows = cursor.fetchall()
        organizations = [TransportOrganization.make_from_db_row(row) for row in org_rows]
        return transport, route, organizations


def _get_by_id(conn, id, organization_id):
    with conn.cursor() as cursor:
        SQL = '''
            SELECT t.*
                FROM transports t
            INNER JOIN transport_organization_transports tot
                ON tot.transport = t.id
            WHERE 
                t.id = %s AND
                tot.organization = %s
        '''
        cursor.execute(SQL, (id, organization_id))
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        transport = transport_db.make_from_db_row(row)
        return transport


def _get_by_ids(conn, ids, organization_id):
    with conn.cursor() as cursor:
        SQL = '''
            SELECT t.*
                FROM transports t
            INNER JOIN transport_organization_transports tot
                ON tot.transport = t.id
            WHERE 
                t.id in ({}) AND
                tot.organization = %s
        '''.format(", ".join(str(id) for id in ids if isinstance(id, int)))
        cursor.execute(SQL, (organization_id,))
        rows = cursor.fetchall()
        if not rows:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        transports = [transport_db.make_from_db_row(row) for row in rows]
        return transports


def get_by_id(id, organization_id, conn=None) -> transport_db:
    if not conn:
        with psycopg2.connect(SQL_CONNECTION) as conn:
            return _get_by_id(conn, id, organization_id)
    return _get_by_id(conn, id, organization_id)


def _get_transports_conn(organization_id, conn=None, asdict=True):
    with conn.cursor() as cursor:
        SQL = '''
            SELECT t.* 
                FROM transports t
            INNER JOIN transport_organization_transports tot
                ON tot.transport = t.id
            WHERE tot.organization = %s
        '''
        cursor.execute(SQL, (organization_id,))
        rows = cursor.fetchall()
        transports = []
        for row in rows:
            if asdict:
                transports.append(transport_db.make_from_db_row(row).asdict())
            else:
                transports.append(transport_db.make_from_db_row(row))
        return transports


def get_all_transports(conn=None):
    if not conn:
        with psycopg2.connect(SQL_CONNECTION) as conn:
            with conn.cursor() as cursor:
                SQL = '''
                    SELECT * FROM transports
                '''
                cursor.execute(SQL)
                rows = cursor.fetchall()
                transports = []
                for row in rows:
                    transports.append(transport_db.make_from_db_row(row))
                return transports
    else:
        with conn.cursor() as cursor:
            SQL = '''
                   SELECT * FROM transports
               '''
            cursor.execute(SQL)
            rows = cursor.fetchall()
            transports = []
            for row in rows:
                transports.append(transport_db.make_from_db_row(row))
            return transports


def get_transports(organization_id, asdict=True, conn=None) -> ['transport_db']:
    if not conn:
        with psycopg2.connect(SQL_CONNECTION) as conn:
            return _get_transports_conn(organization_id, conn, asdict)
    return _get_transports_conn(organization_id, conn, asdict)


def _update(conn, id, organization_id, **kwargs):
    line_id = kwargs.get('line_id')
    if line_id:
        _check_line_with_organization(conn, line_id, organization_id)
    driver = kwargs.get('driver')
    if driver:
        row = _check_driver_with_organization(conn, driver, organization_id)
        with conn.cursor() as cursor:
            sql = '''
                update transports set driver = null where driver = %s
            '''
            cursor.execute(sql, row)
    with conn.cursor() as cursor:

        sql_str = ', '.join('{} = %s'.format(k) for k, v in kwargs.items() if k in transport_db._fields)

        SQL = '''
            UPDATE transports SET
                {}
            WHERE 
                id = %s AND 
                id IN (SELECT transport from transport_organization_transports WHERE organization = %s)
            RETURNING *'''.format(sql_str)
        params = [json.dumps(v) if isinstance(v, dict) else v for k, v in kwargs.items() if k in transport_db._fields]
        params.append(id)
        params.append(organization_id)
        try:
            cursor.execute(SQL, params)
        except psycopg2.IntegrityError as e:
            if errorcodes.lookup(e.pgcode) == 'UNIQUE_VIOLATION':
                if 'device_id' in e.pgerror:
                    raise TransportException('device_id must be unique', code=ec.TRANSPORT_DEVICE_ID_MUST_BE_UNIQUE)
                if 'driver' in e.pgerror:
                    raise TransportException('driver already has a transport', code=ec.DRIVER_ALREADY_HAS_A_TRANSPORT)
            else:
                raise e
        row = cursor.fetchone()
        transport = transport_db.make_from_db_row(row)
        return transport


def update(id, organization_id, conn=None, **kwargs) -> 'Transport':
    if not conn:
        with psycopg2.connect(SQL_CONNECTION) as conn:
            return _update(conn, id, organization_id, **kwargs)
    return _update(conn, id, organization_id, **kwargs)



def _delete_transport(conn, id, organization_id):
    with conn.cursor() as cursor:
        SQL = '''
            DELETE FROM transports
            WHERE 
                id = %s AND 
                id IN (SELECT transport from transport_organization_transports WHERE organization = %s)
            RETURNING *
        '''
        cursor.execute(SQL, (id, organization_id))
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        transport = transport_db.make_from_db_row(row)
        return transport


def _delete_transport_organization_transports(conn, id, organization_id):
    with conn.cursor() as cursor:
        SQL = '''
            DELETE FROM transport_organization_transports
            WHERE 
                transport = %s AND 
                organization = %s
            RETURNING *
        '''
        cursor.execute(SQL, (id, organization_id))
        row = cursor.fetchone()
        if not row:
            return None
        return row


def delete(id, organization_id) -> 'Transport':
    with psycopg2.connect(SQL_CONNECTION) as conn:
        deleted = _delete_transport(conn, id, organization_id)
        _delete_transport_organization_transports(conn, id, organization_id)
        delete_driver_transports_by_transport(conn=conn, transport=id)
        return deleted


def get_by_ids(conn, device_ids):
    sql = '''
        select * from transports where id in ({})
    '''.format(", ".join("'{}'".format(dev_id) for dev_id in device_ids))
    with conn.cursor() as cursor:
        cursor.execute(sql, (device_ids,))
        transports = [transport_db.make_from_db_row(row)
                      for row in cursor]
        return transports

def get_by_device_id_from_transports_table(device_id, conn=None):
    if not conn: conn = psycopg2.connect(SQL_CONNECTION)
    else: conn = conn
    with conn.cursor() as cursor:
        sql = '''select * from transports where device_id = %s;'''
        cursor.execute(sql, (device_id,))
        transports = [transport_db.make_from_db_row(row) for row in cursor]
        return transports


def get_driver_transports(*, driver: int, to_dict=False) -> T.List[transport_db]:
    sql = '''
        SELECT t.* from transports t
        INNER JOIN driver_transports dt
            ON t.id = dt.transport
        WHERE dt.driver = %s
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (driver,))
            return [transport_db.make_from_db_row(row).asdict()
                    if to_dict else transport_db.make_from_db_row(row)
                    for row in cursor]


@connected
def all_drivers_transports(*, organization: int, conn=None):
    sql = '''
        SELECT dt.driver, array_agg(dt.transport) from transports t
        INNER JOIN transport_organization_transports tot
            ON t.id = tot.transport
        INNER JOIN driver_transports dt
            ON t.id = dt.transport
        WHERE tot.organization = %s
        GROUP BY dt.driver
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (organization,))
        resp = dict()
        for row in cursor:
            resp[row[0]] = row[1]
        return resp


@connected
def save_driver_transports(conn, driver: int, transports: T.Union[list, set], organization: int):
    sql = '''
            INSERT INTO driver_transports (driver, transport) VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        '''
    _check_driver_with_organization(conn, driver, organization)
    for transport in transports:
        _check_transport_with_organization(conn=conn, transport=transport, organization=organization)
    with conn.cursor() as cursor:
        params = [[driver, transport] for transport in transports]
        cursor.executemany(sql, params)


def delete_all_driver_transports(*, conn,  driver: int, organization: int):
    sql = '''
        DELETE FROM driver_transports
        WHERE driver = %s AND driver IN (SELECT "user" FROM transport_organization_drivers WHERE organization=%s)
        returning *
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (driver, organization))
        return cursor.fetchone()


@connected
def delete_driver_transports(driver: int, organization: int, transports: T.Union[list, set] = None, conn=None):
    sql = '''
        DELETE FROM driver_transports
        WHERE driver = %s and transport = %s
        RETURNING *
    '''
    sql_force = '''
        DELETE FROM driver_transports
        WHERE driver = %s
    '''
    _check_driver_with_organization(conn, driver, organization)
    if transports:
        for transport in transports:
            _check_transport_with_organization(conn=conn, transport=transport, organization=organization)
        with conn.cursor() as cursor:
            params = [[driver, transport] for transport in transports]
            cursor.executemany(sql, params)
    else:
        with conn.cursor() as cursor:
            cursor.execute(sql_force, (driver,))


@connected
def delete_driver_transports_by_transport(transport, conn=None):
    sql = '''
        delete from driver_transports
        where transport = %s
        returning *
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (transport,))
        return cursor.fetchall()


def assign_driver(*, conn, transport: int, driver: int):
    sql = '''
        update transports set driver = %s
        where id = %s and id in (select transport from driver_transports where driver = %s)
        returning *
    '''
    with conn.cursor() as cursor:
        params = (driver, transport, driver)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        return transport_db.make_from_db_row(row)


def unassign_driver(*, conn, driver: int, organization: int = None) -> transport_db:
    sql = '''
        update transports set driver = null
        where driver = %s and id in (select transport from driver_transports where driver = %s)
        returning *
    '''
    sql_admin = '''
        update transports set driver = null
        where driver = %s and id in(select transport from transport_organization_transports where organization = %s)
        returning *
    '''
    with conn.cursor() as cursor:
        if not organization:
            params = (driver, driver)
            cursor.execute(sql, params)
        else:
            params = (driver, organization)
            cursor.execute(sql_admin, params)
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        return transport_db.make_from_db_row(row)


def get_by_driver(*, conn, driver: int) -> transport_db:
    sql = '''
        select * from transports where driver = %s
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (driver,))
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        return transport_db.make_from_db_row(row)


def get_by_id_filter_driver(*, conn, transport: int, driver: int):
    sql = '''
            select * from transports
            where id = %s and id in (select transport from driver_transports where driver = %s)
        '''
    with conn.cursor() as cursor:
        params = (transport, driver)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if not row:
            raise TransportException('transport not found', code=ec.TRANSPORT_NOT_FOUND)
        return transport_db.make_from_db_row(row)


@connected
def update_transports_phone(conn, id, phone):
    sql = '''
        update transports set device_phone = %s where id = %s
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (phone, id))

from .models import Transport

def _transport_by_device_id(device_id):
    transport = Transport.query.filter(Transport.device_id == device_id).first()
