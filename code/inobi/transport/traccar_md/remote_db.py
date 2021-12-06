import datetime, json

KNOT = 1.851999999984


class Tables:
    out_of_route = 'inobi_out_of_route_trips'
    trips = 'inobi_trips'
    stops = 'inobi_stops'
    transport = 'transport_report'


def dump_day_report(conn, datetime):
    with conn.cursor() as cursor:
        cursor.execute('select dump_transport_report(%s)', (datetime,))


def get_out_of_route(conn, device_id, start, end):
    with conn.cursor() as cursor:
        cursor.execute('select day, device_id, out_of_route from inobi_device_dump where device_id = %s and day between %s and %s',
                       (device_id, start, end))
        return cursor.fetchall()


def get_trips(conn, device_id, start, end):
    with conn.cursor() as cursor:
        cursor.execute('select day, device_id, trips from inobi_device_dump where device_id = %s and day between %s and %s',
                       (device_id, start, end))
        return cursor.fetchall()


def get_stops(conn, device_id, start, end):
    with conn.cursor() as cursor:
        cursor.execute('select day, device_id, stops from inobi_device_dump where device_id = %s and day between %s and %s',
                       (device_id, start, end))
        return cursor.fetchall()


def dump_reports(conn, device_id, day, out_of_route, trips, stops):
    with conn.cursor() as cursor:
        cursor.execute('insert into inobi_device_dump (device_id, day, out_of_route, trips, stops) values(%s, %s, %s, %s, %s)',
                       (device_id, day, json.dumps(out_of_route), json.dumps(trips), json.dumps(stops)))


def get_positions_by_filter(conn, device_id, start: datetime.datetime, end: datetime.datetime, altitude: float=None):
    # return (
    #     (datetime.datetime(2018, 11, 7, 18, 0, 1), 1, 1, json.dumps(dict(distance=1, totalDistance=10)), 65),
    #     (datetime.datetime(2018, 11, 7, 18, 0, 3), 1, 1, json.dumps(dict(distance=2, totalDistance=12)), 75),
    #     (datetime.datetime(2018, 11, 7, 18, 0, 10), 1, 1, json.dumps(dict(distance=1, totalDistance=13)), 10),
    #     (datetime.datetime(2018, 11, 7, 18, 2, 10), 1, 1, json.dumps(dict(distance=5, totalDistance=20)), 50),
    #     (datetime.datetime(2018, 11, 7, 18, 2, 11), 1, 1, json.dumps(dict(distance=1, totalDistance=21)), 12),
    # )

    with conn.cursor() as cursor:
        cursor.execute('select id from devices where uniqueid = %s', (device_id,))
        id = cursor.fetchone()
        if not id:
            return None
        (id,) = id
    with conn.cursor() as cursor:
        if start.utcoffset():
            tzname = start.utcoffset().total_seconds() / 3600
            cursor.execute('set timezone=%s', (tzname,))
        if altitude:
            sql = 'select * from get_positions(%s, %s, %s, %s)'
            params = (start, end, id, altitude)
        else:
            sql = 'select * from get_positions(%s, %s, %s)'
            params = (start, end, id)

        cursor.execute(sql, params)
        data = cursor.fetchall()
        return data


def get_dumped_report(conn, ids, start, end):
    sql = '''
        select 
            deviceid,
            avg(average_speed) as average_speed,
            max(max_speed) as max_speed,
            sum(passengers_in),
            sum(passengers_out),
            sum(distance)
        from (
            select 
                deviceid,
                average_speed, 
                max_speed, 
                passengers_in,
                passengers_out,
                distance
            from transport_report 
            where 
                day between %s and %s and
                deviceid in ({}) 
        ) q group by deviceid
                   
    '''.format(", ".join("'{}'".format(id) for id in ids))
    with conn.cursor() as cursor:
        cursor.execute(sql, (start, end))
        return cursor.fetchall()


def get_calc_report(conn, ids, start, end):
    with conn.cursor() as cursor:
        sql = '''
        select 
            deviceid as device_id, 
            (avg(speed) * 1.852) as average_speed, 
            (max(speed) * 1.852) as max_speed, 
            coalesce(sum((attrs->>'passengers_in')::float::int), 0) as passengers_in, 
            coalesce(sum((attrs->>'passengers_out')::float::int), 0) as passengers_out, 
            sum((attrs->>'distance')::float)/1000 as distance
        from (
            select 
                case
                    when speed > 54 then null
                    when speed < 54 then speed
                end as speed,
                deviceid, 
                fixtime, 
                attributes::json as attrs 
            from positions 
            where 
                fixtime between %s and %s and
                deviceid in ({})
        ) q group by deviceid
        '''.format(", ".join("'{}'".format(id) for id in ids))
        cursor.execute(sql, (start, end))
        return cursor.fetchall()


def get_positions(conn, transports: list, start: float, end: float):
    if not isinstance(transports, list):
        transports = (transports,)
    with conn.cursor() as cursor:
        sql = '''
        select id, uniqueid from devices where uniqueid in ({})
        '''.format(", ".join("'{}'".format(dev_id.device_id) for dev_id in transports))
        cursor.execute(sql)
        ids = dict()
        for tid, device_id in cursor:
            for transport in transports:
                if transport.device_id == device_id:
                    ids[tid] = transport.id

    now = datetime.datetime.now()
    start = datetime.datetime.fromtimestamp(start)
    end = datetime.datetime.fromtimestamp(end)

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59)

    now_date = now.date()
    start_date = start.date()
    end_date = end.date()

    device_ids = [k for k in ids.keys()]

    if start_date == now_date:
        fetched = get_calc_report(conn, device_ids, start, end)
    elif end_date != now_date:
        fetched = get_dumped_report(conn, device_ids, start, end)
        if not fetched:
            fetched = get_calc_report(conn, device_ids, start, end)
    else:
        start_calc = now.replace(hour=0, minute=0, second=0)
        fetched_dump = get_dumped_report(conn, device_ids, start, start_calc)
        if not fetched_dump:
            start_calc = start
        fetched_calc = get_calc_report(conn, device_ids, start_calc, end)

        final = {}


        for d in fetched_dump + fetched_calc:
            device_id_d, average_speed_d, max_speed_d, passengers_in_d, passengers_out_d, distance_d = d

            if device_id_d in final:
                device_id_c, average_speed_c, max_speed_c, passengers_in_c, passengers_out_c, distance_c = final[device_id_d]
                final[device_id_d] = (
                    device_id_c,
                    (average_speed_c + average_speed_d) / 2,
                    max(max_speed_d, max_speed_c),
                    passengers_in_c + passengers_in_d,
                    passengers_out_c + passengers_out_d,
                    distance_c + distance_d
                )
            else:
                final[device_id_d] = d

        fetched = final.values()

            # return [
            #     dict(
            #         id=ids[device_id],
            #         average_speed=average_speed,
            #         max_speed=max_speed,
            #         passengers_in=passengers_in,
            #         passengers_out=passengers_out,
            #         total_distance=distance
            #     )
            #     for device_id, average_speed, max_speed, passengers_in, passengers_out, distance in final.values()
            # ]

        # fetched = []

        # fetched_dump += fetched_calc
        # joined = set()

        # for i, item in enumerate(fetched_dump):
        #     device_id_d, average_speed_d, max_speed_d, passengers_in_d, passengers_out_d, distance_d = item
        #     found = False
        #     for device_id_c, average_speed_c, max_speed_c, passengers_in_c, passengers_out_c, distance_c in fetched_dump[i:]:
        #         if device_id_c in joined:
        #             found = True
        #             continue
        #         if device_id_d == device_id_c:
        #             found = True
        #             joined.add(device_id_c)
        #             fetched.append((
        #                 device_id_c,
        #                 (average_speed_c + average_speed_d) / 2,
        #                 max_speed_d if max_speed_d > max_speed_c else max_speed_c,
        #                 passengers_in_c + passengers_in_d,
        #                 passengers_out_c + passengers_out_d,
        #                 distance_c + distance_d
        #             ))
        #             break
        #     if not found:
        #         fetched.append((
        #             device_id_d,
        #             average_speed_d,
        #             max_speed_d,
        #             passengers_in_d,
        #             passengers_out_d,
        #             distance_d
        #         ))

    result = []
    if fetched:
        for device_id, average_speed, max_speed, passengers_in, passengers_out, distance in fetched:
            result.append(
                dict(
                    id=ids[device_id],
                    average_speed=average_speed,
                    max_speed=max_speed,
                    passengers_out=passengers_out,
                    passengers_in=passengers_in,
                    total_distance=distance
                )
            )

    return result

import datetime


def get_raw_positions(conn, unique_id, start, end, frequency=None):
    sql = '''
        select p.latitude, p.longitude, p.fixtime from positions p
        inner join devices d
        on p.deviceid = d.id
        
        where d.uniqueid = %s
        
        and p.fixtime between %s and %s
    '''

    start = datetime.datetime.fromtimestamp(start)
    end = datetime.datetime.fromtimestamp(end)
    with conn.cursor() as cursor:
        cursor.execute(sql, (unique_id, start, end))
        data = {}
        for i, row in enumerate(cursor):
            if frequency:
                if i % frequency != 0:
                    continue
            lat, lng, time = row
            if int(lat) == 0 and int(lng) == 0:
                continue
            key = str(time.replace(hour=0, minute=0, second=0, microsecond=0))
            if key not in data:
                data[key] = []
                data[key].append([lat, lng])
            data[key].append([lat, lng])
    return data


def get_raw_positions_for_animation(conn, unique_id, start: datetime.datetime, end: datetime.datetime):
    sql = '''
        select p.latitude, p.longitude, p.speed, p.fixtime, 
        (p.attributes::json->>'status')::float::int as status from positions p
        inner join devices d on p.deviceid = d.id 
        where d.uniqueid = %s and p.fixtime between %s and %s
    '''

    with conn.cursor() as cursor:
        if start.utcoffset(): # change the timezone of database to get the query based on the client timezone
            tzname = start.utcoffset().total_seconds() / 3600
            cursor.execute('set timezone=%s', (tzname,))
        cursor.execute(sql, (unique_id, start, end))
        data = []
        for i, row in enumerate(cursor):
            lat, lng, speed, utc_time, status = row # utc_time is a datetime object
            if int(lat) == 0 and int(lng) == 0 and int(speed) == 0:
                continue
            data.append({"time": str(utc_time.time()), "lat": lat, "lng": lng, "speed": speed, "status": status})
    return data


def get_devices(conn):
    with conn.cursor() as cursor:
        cursor.execute('select uniqueid from devices')
        devices = cursor.fetchall()
        if devices:
            devices = [d[0] for d in devices]
        return devices


def get_by_device_id(conn, device_id):
    with conn.cursor() as cursor:
        cursor.execute('select id from devices where unique_id = %s', (device_id,))
        return cursor.fetchone()
