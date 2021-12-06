from . import line_queries as queries
from . import tables
import polyline
import psycopg2
from inobi.config import SQL_CONNECTION





def __convert_linestring(linestring):
    linestring = linestring[12:-1]
    raw = []
    for item in linestring.split(','):
        lat, lng = item.split()
        raw.append((float(lat), float(lng)))
    converted = polyline.encode(raw)
    return converted

def refresh():
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(queries.refresh)
            return dict(code=200)

def get_platform_routes(platform_id):
    Platform_routes = '''
        select r.id, r.type, r.name, r.from_name, r.to_name from routes r
            inner join route_directions rd
                on rd.id = r.id
            inner join directions d
                on rd.entry_id = d.id
            inner join direction_platforms dp
                on dp.id = d.id
            inner join platforms p
                on dp.entry_id = p.id
                
            where r.id not in (select route_id from exclude_routes) and

            p.id = %s
    '''

    # sql_platform_info = self.do(Platform_info, params=(platform_id,), out=True)
    # if sql_platform_info['code'] != 200:
    #     return sql_platform_info
    # platform_info = []
    # stations_id = 0
    # for item in sql_platform_info['data']:
    #     stations_id = item[1]
    #     platform_info.append(dict(id=item[0],
    #                               station_id=item[1],
    #                              name=item[2],
    #                              full_name=item[3],
    #                              location=dict(lat=item[4],
    #                                            lng=item[5])))
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(Platform_routes, (platform_id,))
            sql_platform_routes = cursor.fetchall()
            if not sql_platform_routes:
                return dict(code=404, message='data not found')

    bus = []
    trolleybus = []
    shuttle_bus = []
    unknown = []
    for item in sql_platform_routes:
        if item[1] == 'bus':
            bus.append(dict(id=item[0],
                            type=item[1],
                            name=item[2],
                            from_name=item[3],
                            to_name=item[4]))
        elif item[1] == 'trolleybus':
            trolleybus.append(dict(id=item[0],
                                   type=item[1],
                                   name=item[2],
                                   from_name=item[3],
                                   to_name=item[4]))
        elif item[1] == 'shuttle_bus':
            shuttle_bus.append(dict(id=item[0],
                                    type=item[1],
                                    name=item[2],
                                    rom_name=item[3],
                                    to_name=item[4]))
        else:
            unknown.append(dict(id=item[0],
                                type=item[1],
                                name=item[2],
                                from_name=item[3],
                                to_name=item[4]))
    platform_routes = dict()
    if bus:
        platform_routes['bus'] = bus
    if trolleybus:
        platform_routes['trolleybus'] = trolleybus
    if shuttle_bus:
        platform_routes['shuttle_bus'] = shuttle_bus
    if unknown:
        platform_routes['unknown'] = unknown
    return dict(code=200, data=platform_routes)

# def get_platforms_on_scale(locations):
#     # 42.876605, 74.588343
#     # 42.856838, 74.610322
#     SQL = '''
#         select p.id, s.name, s.full_name, p.lat, p.lng from stations s
#                 inner join station_platforms sp
#                     on s.id = sp.id
#                 inner join platforms p
#                     on p.id = sp.entry_id
#                 where p.lat <= %s and p.lng >= %s
#                 and p.lat >= %s and p.lng <= %s
#     '''
#     if len(locations) != 4:
#         return dict(code=400, message='params error')
#
#
#
#
#     self.create_conn()
#     sql_data = self.do(SQL, params=locations, out=True)
#     self.close_conn()
#
#     if sql_data['code'] != 200:
#         return sql_data
#     platforms = []
#     for item in sql_data['data']:
#         platforms.append(dict(id=item[0],
#                               name=item[1],
#                               full_name=item[2],
#                               location=dict(lat=item[3],
#                                             lng=item[4])))
#     return dict(code=200, data=platforms)

def get_route(route_id):
    rid = 0
    rtype = 1
    rname = 2
    rfrom_name = 3
    rto_name = 4
    did = 5
    dtype = 6
    dline = 7
    SQL_directions = '''
            select r.id, r.type, r.name, r.from_name, r.to_name, d.id, d.type, d.line from routes as r
                inner join route_directions as rd
                    on rd.id = r.id
                inner join directions as d
                    on rd.entry_id = d.id
                
                where r.id = %s
                order by rd.pos
            '''
    pid = 0
    plat = 1
    plng = 2
    sname = 3
    sfull_name = 4
    SQL_platforms = '''
        select p.id, p.lat, p.lng, s.name, s.full_name from stations s
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

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL_directions, (route_id,))
            sql_data = cursor.fetchall()
            if not sql_data:
                return dict(code=404, message='data not found')

        with conn.cursor() as cursor:
            directions = []
            for i, route in enumerate(sql_data):

                cursor.execute(SQL_platforms, (route[did],))
                sql_platforms = cursor.fetchall()

                if not sql_platforms:
                    return dict(code=404, message='data not found')
                platforms = []
                for platform in sql_platforms:
                    platforms.append(dict(id=platform[pid],
                                          name=platform[sname],
                                          full_name=platform[sfull_name],
                                          location=dict(lat=platform[plat],
                                                        lng=platform[plng])))
                directions.append(dict(id=route[did],
                                       type=route[dtype],
                                       line=route[dline],
                                       platforms=platforms))

    return dict(code=200, data=dict(id=sql_data[0][rid],
                                    type=sql_data[0][rtype],
                                    name=sql_data[0][rname],
                                    from_name=sql_data[0][rfrom_name],
                                    to_name=sql_data[0][rto_name],
                                    directions=directions))

def get_list_routes():
    SQL = '''
        SELECT 
                r.id, 
                r.type, 
                r.name, 
                r.from_name, 
                r.to_name, 
                c.id as city_id
            FROM routes r
            left join exclude_routes er
                on er.route_id = r.id
            inner join transport_organization_lines tor
                on tor.line = r.id
            inner join transport_organizations "to"
                on "to".id = tor.organization
            inner join cities c
                on c.id = "to".city
                
            where er.route_id is null
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL)
            sql_data = cursor.fetchall()
    if not sql_data:
        return dict(code=200, data=[])

    response = dict(bus=[], shuttle_bus=[], trolleybus=[])
    for id_, type_, name, from_name, to_name, city_id in sql_data:
        response[type_].append(dict(id=id_,
                                    type=type_,
                                    name=name,
                                    from_name=from_name,
                                    to_name=to_name,
                                    city_id=city_id))
    return dict(code=200, data=response)


def get_list_routes_with_excluded():
    SQL = '''
        SELECT 
                r.id, 
                r.type, 
                r.name, 
                r.from_name, 
                r.to_name, 
                c.id as city_id
            FROM routes r
            inner join transport_organization_lines tor
                on tor.line = r.id
            inner join transport_organizations "to"
                on "to".id = tor.organization
            inner join cities c
                on c.id = "to".city
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL)
            sql_data = cursor.fetchall()
    if not sql_data:
        return dict(code=200, data=[])

    response = dict(bus=[], shuttle_bus=[], trolleybus=[], technical=[])
    for id_, type_, name, from_name, to_name, city_id in sql_data:
        response[type_].append(dict(id=id_,
                                    type=type_,
                                    name=name,
                                    from_name=from_name,
                                    to_name=to_name,
                                    city_id=city_id))
    return dict(code=200, data=response)

# def set_stations(self, stations):
#     self.create_conn()
#     data = self.do(query=self.queries.insert_station, params=stations, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_platforms(self, platforms):
#     self.create_conn()
#     data = self.do(self.queries.insert_platform, params=platforms, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_directions(self, directions):
#     self.create_conn()
#     data = self.do(self.queries.insert_direction, params=directions, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_routes(self, routes):
#     self.create_conn()
#     data = self.do(self.queries.insert_route, params=routes, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_direction_platforms(self, direction_platforms):
#     self.create_conn()
#     data = self.do(self.queries.insert_con_direction_platform, params=direction_platforms, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_route_directions(self, route_directions):
#     self.create_conn()
#     data = self.do(self.queries.insert_con_route_direction, params=route_directions, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_station_platforms(self, station_platforms):
#     self.create_conn()
#     data = self.do(self.queries.insert_con_station_platform, params=station_platforms, executemany=True, commit=True)
#     self.close_conn()
#     return data
#
# def set_station_routes(self, station_routes):
#     self.create_conn()
#     data = self.do(self.queries.insert_con_station_route, params=station_routes, executemany=True, commit=True)
#     self.close_conn()
#     return data