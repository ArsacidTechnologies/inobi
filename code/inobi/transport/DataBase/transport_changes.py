import psycopg2
from inobi.transport.DataBase.classes import TransportDriverChanges, Transport
from inobi.mobile_app.db.user import User
from inobi.config import SQL_CONNECTION
from inobi.transport.configs import TRACCAR_SQL_CONNECTION
from inobi.transport.traccar_md.remote_db import get_positions
from inobi.transport.exceptions import TransportException
from inobi.transport.error_codes import DRIVER_DOES_NOT_HAVE_TRANSPORT


def _driver_transport_periods(conn, driver, organization, start_date: float, end_date: float):
    sql = '''
        select tdc.*, t.*, u.* from transport_driver_changes tdc
        inner join transports t
            on tdc.transport = t.id
        inner join "users" u
            on u.id = tdc.issuer
        where 
            %s in (select "user" from transport_organization_drivers where organization = %s) and
            (tdc.time between %s and %s) and
            (tdc.type = 'driver') and
            (tdc.prev = %s or tdc.next = %s)
        ORDER BY tdc.time
    '''
    with conn.cursor() as cursor:
        params = (driver, organization, start_date, end_date, driver, driver)
        cursor.execute(sql, params)
        fetched = cursor.fetchall()
        logs = []
        if not fetched:
            sql_get_transport = '''
                select * from transports
                where driver = %s and
                driver in (select "user" from transport_organization_drivers where organization = %s)
            '''
            cursor.execute(sql_get_transport, (driver, organization))
            row = cursor.fetchone()
            if not row:
                raise TransportException('driver has no transport',
                                         code=DRIVER_DOES_NOT_HAVE_TRANSPORT)
            transport = Transport.make_from_db_row(row)
            return [dict(transport=transport,
                         start_date=start_date,
                         end_date=end_date,
                         payload=dict(issuer=None,
                                      previous_driver=None,
                                      next_driver=None,
                                      time=None,
                                      reason=None))]

        period = dict()
        for i, row in enumerate(fetched):
            log = TransportDriverChanges.make_from_db_row(row)
            transport = Transport.make_from_db_row(row, len(TransportDriverChanges._fields))
            user = User.make(row[len(TransportDriverChanges._fields) + len(Transport._fields):])
            if i == 0:
                if log.prev == driver:
                    period['transport'] = transport
                    period['start_date'] = start_date
                    period['end_date'] = log.time
                    period['payload'] = dict(issuer=user._asdict(),
                                             previous_driver=log.prev,
                                             next_driver=log.next,
                                             time=log.time,
                                             reason=log.reason)
                    logs.append(period)
                    period = dict()
                    continue
            if i == len(fetched) - 1:
                if log.next == driver:
                    period['transport'] = transport
                    period['start_date'] = log.time
                    period['end_date'] = end_date
                    period['payload'] = dict(issuer=user._asdict(),
                                             previous_driver=log.prev,
                                             next_driver=log.next,
                                             time=log.time,
                                             reason=log.reason)
                    logs.append(period)
                    period = dict()
            if log.prev == driver:
                period['end_date'] = log.time
                logs.append(period)
                period = dict()
            elif log.next == driver:
                period['transport'] = transport
                period['start_date'] = log.time
                period['payload'] = dict(issuer=user._asdict(),
                                         previous_driver=log.prev,
                                         next_driver=log.next,
                                         time=log.time,
                                         reason=log.reason)

        return logs


def get_driver_report(start_date: float, end_date: float, driver: int, organization: int):
    with psycopg2.connect(SQL_CONNECTION) as conn:
        periods = _driver_transport_periods(conn, driver, organization, start_date, end_date)
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        passengers_in_total = 0
        passengers_out_total = 0
        distance = 0
        speed = []
        max_speed = 0
        for period in periods:
            print(period)
            position = get_positions(conn, period['transport'], period['start_date'], period['end_date'])
            period['transport'] = period['transport'].asdict()
            period['average_speed'] = 0
            period['total_distance'] = 0
            period['passengers_in'] = 0
            period['passengers_out'] = 0
            period['max_speed'] = 0
            if not position:
                continue
            (position,) = position
            period['average_speed'] = position['average_speed']
            period['total_distance'] = position['total_distance']
            period['passengers_in'] = position['passengers_in']
            period['passengers_out'] = position['passengers_out']
            period['max_speed'] = position['max_speed']
            if position['max_speed'] >= max_speed:
                max_speed = position['max_speed']
            passengers_in_total += position['passengers_in']
            passengers_out_total += position['passengers_out']
            speed.append(position['average_speed'])
            distance += position['total_distance']

        if speed:
            speed = sum(speed) / len(speed)
        else:
            speed = 0
        return dict(periods=periods,
                    passengers_in=passengers_in_total,
                    passengers_out=passengers_out_total,
                    average_speed=speed,
                    total_distance=distance,
                    max_speed=max_speed)

