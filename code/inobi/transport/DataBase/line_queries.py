insert_station = '''
    INSERT INTO stations VALUES(%s, %s, %s)
    '''
insert_route = '''
    INSERT INTO routes VALUES(%s, %s, %s, %s, %s)
    '''
insert_direction = '''
    INSERT INTO directions VALUES(%s, %s, %s)
    '''
insert_platform = '''
    INSERT INTO platforms VALUES(%s, %s, %s)
    '''
insert_con_route_direction = '''
    INSERT INTO route_directions VALUES (%s, %s, %s)
    '''
insert_con_direction_platform = '''
    INSERT INTO direction_platforms VALUES (%s, %s, %s)
    '''
insert_con_station_platform = '''
    INSERT INTO station_platforms VALUES (%s, %s, %s)
    '''
insert_con_station_route = '''
    INSERT INTO station_routes VALUES (%s, %s, %s)
    '''
insert_exclude_routes = '''
    INSERT INTO exclude_routes VALUES (%s)
'''
insert_break_points = '''
    INSERT INTO breakpoints VALUES (%s, %s)
'''
insert_direction_links = '''
    INSERT INTO direction_links VALUES (%s, %s, %s, %s, %s, %s, %s)
'''
get_item = '''
    SELECT * FROM %s
    WHERE id = %s
'''

get_all_items = '''
    SELECT * FROM %s
'''
refresh = '''
TRUNCATE TABLE direction_platforms;
TRUNCATE TABLE route_directions;
TRUNCATE TABLE station_routes;
TRUNCATE TABLE station_platforms;
TRUNCATE TABLE platforms;
TRUNCATE TABLE directions;
TRUNCATE TABLE routes;
TRUNCATE TABLE stations;
TRUNCATE TABLE exclude_routes;
TRUNCATE TABLE direction_links;
TRUNCATE TABLE breakpoints;
'''