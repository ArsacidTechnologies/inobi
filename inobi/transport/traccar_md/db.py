from inobi.transport.configs import traccar_dbpath
import sqlite3
from inobi.transport.exceptions import TransportException
from ..error_codes import TRACCAR_SYNC_REQUIRED


def init_db(conn: sqlite3.connect):
    INIT_SQL = '''
    create table if not exists transport_device(
        transport int,
        device int
    );
    create table if not exists line_group(
        line int,
        'group' int
    );
    create table if not exists direction_geofence(
        direction int,
        geofence int
    );
    create table if not exists organization_user(
        organization int,
        'user' int
    );
    create unique index if not exists ind_transport_device on transport_device(transport, device);
    create unique index if not exists ind_line_group on line_group(line, 'group');
    create unique index if not exists ind_direction_geofence on direction_geofence(direction, geofence);
    create unique index if not exists ind_organization_user on organization_user(organization, 'user');
    '''
    cursor = conn.cursor()
    cursor.executescript(INIT_SQL)
    conn.commit()


def save_all(transport_device: [], line_group: [], direction_geofence: [], organization_user: []):
    with sqlite3.connect(traccar_dbpath) as conn:
        init_db(conn)
        sql_transport_device = '''
            insert into transport_device values (?, ?)
        '''
        sql_line_group = '''
            insert into line_group values (?, ?)
        '''
        sql_direction_geofence = '''
            insert into direction_geofence values (?, ?)
        '''
        sql_organization_user = '''
            insert into organization_user values (?, ?)
        '''
        cursor = conn.cursor()
        cursor.executemany(sql_transport_device, transport_device)
        cursor.executemany(sql_line_group, line_group)
        cursor.executemany(sql_direction_geofence, direction_geofence)
        cursor.executemany(sql_organization_user, organization_user)


def save_transport(conn, transport, device):
    sql = 'insert into transport_device values (?, ?)'
    cursor = conn.cursor()
    cursor.execute(sql, (transport, device))


def get_group_by_line(conn, line):
    sql = 'select "group" from line_group where line = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (line,))
    group = cursor.fetchone()
    if not group:
        text = 'unknown line_id {} in line_group table, sync project first (restart)'.format(line)
        raise TransportException(msg=text, code=TRACCAR_SYNC_REQUIRED)
    return group[0]


def get_line_by_group(conn, group):
    sql = 'select line from line_group where "group" = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (group,))
    line = cursor.fetchone()
    if not line:
        text = 'unknown group {} in line_group table, sync project first (restart)'.format(group)
        raise TransportException(msg=text, code=TRACCAR_SYNC_REQUIRED)
    return line[0]


def get_device_by_transport(conn, transport):
    sql = 'select device from transport_device where transport = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (transport,))
    device = cursor.fetchone()
    if not device:
        text = 'unknown transport {} in transport_device table, sync project first (restart)'.format(transport)
        raise TransportException(msg=text, code=TRACCAR_SYNC_REQUIRED)
    return device[0]


def get_user_by_organization(conn, organization):
    sql = 'select user from organization_user where organization = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (organization,))
    user = cursor.fetchone()
    if not user:
        text = 'unknown organization {} in organization_user table, sync project first (restart)'.format(organization)
        raise TransportException(msg=text, code=TRACCAR_SYNC_REQUIRED)
    return user[0]


def get_geofence_by_direction(conn, direction):
    sql = 'select geofence from direction_geofence where direction = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (direction,))
    geofence = cursor.fetchone()
    if not geofence:
        text = 'unknown geofence {} in direction_geofence table, sync project first (restart)'.format(direction)
        raise TransportException(msg=text, code=TRACCAR_SYNC_REQUIRED)
    return geofence[0]

