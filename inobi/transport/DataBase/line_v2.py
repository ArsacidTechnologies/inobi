import psycopg2
from inobi.config import SQL_CONNECTION
from inobi.transport.DataBase.classes import Route, Direction, Platform, Stations
from inobi.utils import connected


def get_transport_organization_lines(organization_id):
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            sql = '''
                SELECT line FROM transport_organization_lines
                WHERE organization = %s
            '''
            cursor.execute(sql, (organization_id,))
            lines = cursor.fetchall()

            return [i[0] for i in lines]


@connected
def get_lines(organization_id, conn=None, asdict=False) -> []:
    with conn.cursor() as cursor:
        sql = '''
            SELECT r.id, r.type, r.name, r.from_name, r.to_name FROM routes r
            where r.id in (select line from transport_organization_lines where organization=%s)
        '''
        cursor.execute(sql, (organization_id,))
        rows = cursor.fetchall()
        if asdict:
            lines = [Route.make_from_db_row(row).asdict() for row in rows]
        else:
            lines = [Route.make_from_db_row(row) for row in rows]
        return lines


def get_all_lines(conn, asdict=False) -> []:
    with conn.cursor() as cursor:
        sql = '''
            SELECT r.id, r.type, r.name, r.from_name, r.to_name FROM routes r
            where r.id not in (select route_id from exclude_routes)
        '''
        cursor.execute(sql)
        rows = cursor.fetchall()
        if asdict:
            lines = [Route.make_from_db_row(row).asdict() for row in rows]
        else:
            lines = [Route.make_from_db_row(row) for row in rows]
        return lines


def get_directions_admin(conn, route_id, convert=False):
    sql = '''
            select d.id, d.type, d.line from routes as r
            inner join route_directions as rd
                on rd.id = r.id
            inner join directions as d
                on rd.entry_id = d.id

            where r.id = %s
            order by rd.pos
        '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (route_id,))
        directions = [Direction.make_from_db_row(row, convert=convert) for row in cursor.fetchall()]
        return directions


def get_directions(conn, route_id, organization_id, convert=False):
    sql = '''
        select d.id, d.type, d.line from routes as r
        inner join route_directions as rd
            on rd.id = r.id
        inner join directions as d
            on rd.entry_id = d.id

        where r.id = %s and
        r.id in (select line from transport_organization_lines where organization = %s)
        order by rd.pos
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (route_id, organization_id))
        directions = [Direction.make_from_db_row(row, convert=convert) for row in cursor.fetchall()]
        return directions


def get_all_directions(conn, organization=None):
    sql = '''
        select d.*, r.* from directions d
        inner join route_directions as rd
            on rd.entry_id = d.id
        inner join routes as r
            on rd.id = r.id
        where r.id not in (select route_id from exclude_routes)
    '''
    if organization:
        sql = '''
            select d.*, r.* from directions d
            inner join route_directions as rd
                on rd.entry_id = d.id
            inner join routes as r
                on rd.id = r.id
            inner join transport_organization_lines tol
                on tol.line = r.id
            where r.id not in (select route_id from exclude_routes) and
            tol.organization = %s
        '''

    with conn.cursor() as cursor:
        if organization:
            cursor.execute(sql, (organization,))
        else:
            cursor.execute(sql)
        directions = [(Direction.make_from_db_row(row, start_index=0, convert=True),
                       Route.make_from_db_row(row, start_index=len(Direction._fields)))
                      for row in cursor.fetchall()]
        return directions


def get_line_detail(line, organization):
    with psycopg2.connect(SQL_CONNECTION) as conn:
        detail = _get_route_with_directions(conn, line, organization)
        if not detail:
            return None
        directions = []
        for route, direction in detail:
            platforms = [dict(id=platform.id,
                              name=station.name,
                              full_name=station.full_name,
                              location=dict(lat=platform.lat,
                                            lng=platform.lng))
                         for platform, station in _get_platforms(conn, direction.id)]
            directions.append(dict(id=direction.id,
                                   type=direction.type,
                                   line=direction.line,
                                   platforms=platforms))
        return dict(id=detail[0][0].id,
                    type=detail[0][0].type,
                    name=detail[0][0].name,
                    from_name=detail[0][0].from_name,
                    to_name=detail[0][0].to_name,
                    directions=directions)


def _get_platforms(conn, direction):
    sql = '''
        select p.*, s.* from stations s
            inner join station_platforms sp
                on s.id=sp.id
            inner join platforms p
                on p.id = sp.entry_id
            inner join direction_platforms dp
                on p.id = dp.entry_id
            inner join directions d
                on d.id = dp.id
            where d.id = %s
            order by dp.pos
        '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (direction,))
        return [(Platform.make_from_db_row(row),
                 Stations.make_from_db_row(row, start_index=len(Platform._fields)))
                for row in cursor.fetchall()]


def _get_route_with_directions(conn, line, organization):
    with conn.cursor() as cursor:
        sql = '''
            select r.*, d.* from routes as r
                inner join route_directions as rd
                    on rd.id = r.id
                inner join directions as d
                    on rd.entry_id = d.id
    
                where r.id = %s
                and r.id in (select line from transport_organization_lines where organization = %s)
                order by rd.pos
            '''
        cursor.execute(sql, (line, organization))
        data = [(Route.make_from_db_row(row, start_index=0),
                Direction.make_from_db_row(row, start_index=len(Route._fields)))
                for row in cursor.fetchall()]
        return data