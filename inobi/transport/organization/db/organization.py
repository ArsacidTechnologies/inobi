import psycopg2
from inobi.config import SQL_CONNECTION
from ...DataBase.classes import TransportOrganization
from inobi.transport.exceptions import TransportException
from ...DataBase.transport_v2 import get_transports, all_drivers_transports
from ...DataBase.line_v2 import get_lines
from ...DataBase.driver import get_drivers
import itertools as IT
from inobi.transport.error_codes import TRACCAR_SYNC_REQUIRED
from inobi.transport.API.subscribe_v2 import subscribe


def get_organizations(conn):
    with conn.cursor() as cursor:
        sql = '''
            select * from transport_organizations
        '''
        cursor.execute(sql)
        rows = cursor.fetchall()
        orgs = [TransportOrganization.make_from_db_row(row) for row in rows]
        return orgs


def _check_driver_with_organization(conn, driver, organization):
    with conn.cursor() as cursor:
        sql = '''
            select * from transport_organization_drivers
            where 
                user = %s and
                organization = %s
        '''
        cursor.execute(sql, (driver, organization))
        row = cursor.fetchone()
        if not row:
            raise TransportException(msg='unknown driver', code=TRACCAR_SYNC_REQUIRED)
        else:
            return True

def get_organization(organization_id, conn):
    sql = '''
        SELECT * FROM transport_organizations WHERE id = %s
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (organization_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return TransportOrganization.make_from_db_row(row)


from .drivers import drivers_of


def add_last_seen(transports: dict, organization_id):
    subs = subscribe(organization_id=organization_id, exclude=(), all=True, type='admin')

    def last_seen(id):
        for sub in subs:
            if sub['id'] == id:
                return sub['time']
        return None
    for transport in transports:
        transport['last_seen'] = last_seen(transport['id'])



def get_organization_data(organization_id):
    with psycopg2.connect(SQL_CONNECTION) as conn:
        organization = get_organization(organization_id, conn=conn)
        if not organization:
            raise TransportException(msg='organization not found', code=TRACCAR_SYNC_REQUIRED)
        transports = get_transports(organization_id, conn=conn)
        add_last_seen(transports, organization_id)
        lines = get_lines(organization_id, conn=conn, asdict=True)
        # drivers = get_drivers(organization_id, conn=conn, asdict=True)
        atd = all_drivers_transports(organization=organization_id, conn=conn)
        t_by_d = {
            t['driver']: t['id']
            for t in transports if 'driver' in t
        }
        drivers = [d._asdict(available_transport=atd.get(d.driver.id, []), transport=t_by_d.get(d.driver.id, None)) for d in drivers_of(organization_id, with_transport=False)]

        for l in lines:
            l['transport'] = []
        _lines_d = {
            l['id']: l
            for l in lines
        }
        for line_id, transports_gen in IT.groupby(transports, lambda t: t['line_id']):
            _lines_d[line_id]['transport'].extend(transports_gen)
        return dict(organization=organization._asdict(),
                    lines=lines,
                    drivers=drivers)


import typing as T


def dump_transports_to_organization(organization_id: int) -> T.List[int]:
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute('delete from transport_organization_transports where organization = %s', (organization_id, ))
            cursor.execute('select * from dump_transports_to_organization(%s)', (organization_id, ))
            transports = [tid for (tid, ) in cursor]
            return transports
