import datetime
import json

from inobi.config import KNOT

TRIP_TIME_BOUNDS = datetime.timedelta(minutes=10)

TRIP_MINIMUM_DISTANCE = 0.1


def define_stops(positions):
    if not positions:
        return [], None
    total = {
        "duration": datetime.timedelta()
    }
    stops = []
    stop_id = 0
    for i, position in enumerate(positions[1:], 1):
        prev_time, prev_lat, prev_lng, *_ = positions[i - 1]
        time, lat, lng, *_ = position
        if (time - prev_time) >= TRIP_TIME_BOUNDS:
            duration = time - prev_time
            stops.append({
                "id": stop_id,
                "entry_time": prev_time.isoformat(),
                "leave_time": time.isoformat(),
                "duration": duration.total_seconds(),
                "coordinates": [
                    [prev_lat, prev_lng],
                    [lat, lng]
                ]
            })
            total['duration'] += duration
            stop_id += 1
    total['duration'] = total['duration'].total_seconds()
    return stops, total


def define_dump_stops(rows):
    total = {
        "duration": 0
    }
    stops = []
    for day, device_id, payload in rows:
        if not payload.get('stops'):
            continue
        stops += payload['stops']
        total['duration'] += payload['total']['duration']
    return stops, total


def normalize_attributes(attr):
    attr['totalDistance'] = attr['totalDistance'] / 1000
    attr['distance'] = attr['distance'] / 1000


def define_trips(positions, coordinate_count=False, pop_coordinates=False):
    if not positions:
        return [], None
    total = {
        "distance": 0,
        "max_speed": 0,
        "speeds": [],
        "duration": datetime.timedelta(),
        "out_of_route": 0,
        "total": 0,
    }
    total['filtered_trips'] = filtered_trips = []

    trips = []
    time, lat, lng, attr, speed, altitude = positions[0]
    speed = round(speed * KNOT, 1)
    attr = json.loads(attr)
    normalize_attributes(attr)
    trip_id = 0
    trip = {
        "id": trip_id,
        "distance": 0,
        "entry_mileage": attr.get('totalDistance', 0),
        "leave_mileage": attr.get('totalDistance', 0),
        "entry_time": time,
        "leave_time": time,
        "coordinates": [[lat, lng]],
        "max_speed": speed,
        "speeds": [speed],
        "out_of_route": 0,
        "total": 0
    }

    for i, position in enumerate(positions[1:], 1):
        prev_time, *_ = positions[i-1]
        time, lat, lng, attr, speed, altitude = position
        speed = round(speed * KNOT, 1)
        attr = json.loads(attr)
        normalize_attributes(attr)
        if (time - prev_time) >= TRIP_TIME_BOUNDS:
            trip['average_speed'] = (
                sum(trip['speeds']) / len(trip['speeds'])) * KNOT
            trip['max_speed'] = trip['max_speed'] * KNOT
            duration = trip['leave_time'] - trip['entry_time']
            trip.pop('speeds')

            is_normal_trip = trip['distance'] >= TRIP_MINIMUM_DISTANCE

            if is_normal_trip:
                if trip['max_speed'] > total['max_speed']:
                    total['max_speed'] = trip['max_speed']
                total['speeds'].append(trip['average_speed'])
                total['distance'] += trip['distance']
                total['duration'] += duration

            trip['duration'] = duration.total_seconds()

            trip['entry_time'] = trip['entry_time'].isoformat()
            trip['leave_time'] = trip['leave_time'].isoformat()
            if trip['total'] != 0:
                trip['out_of_route_percent'] = int(
                    trip['out_of_route'] / trip['total'] * 100)
            else:
                trip['out_of_route_percent'] = 0
            trip.pop('out_of_route')
            trip.pop('total')
            if coordinate_count:
                trip['coordinate_count'] = len(trip['coordinates'])
            if pop_coordinates:
                trip.pop('coordinates')

            if is_normal_trip:
                trips.append(trip)
            else:
                filtered_trips.append(trip)

            trip_id += 1

            trip = {
                "id": trip_id,
                "distance": 0,
                "entry_mileage": attr.get('totalDistance', 0),
                "leave_mileage": attr.get('totalDistance', 0),
                "entry_time": time,
                "leave_time": time,
                "max_speed": speed,
                "speeds": [speed],
                "coordinates": [[lat, lng]],
                "out_of_route": 0,
                "total": 0,
            }
        else:
            trip['distance'] += attr['distance']
            trip['leave_mileage'] = attr['totalDistance']
            trip['leave_time'] = time
            trip['speeds'].append(speed)
            if speed > trip['max_speed']:
                trip['max_speed'] = speed
            trip['coordinates'].append([lat, lng])
            if altitude == 1.0:
                trip['out_of_route'] += 1
                total['out_of_route'] += 1
            trip['total'] += 1
            total['total'] += 1

    trip['average_speed'] = (sum(trip['speeds']) / len(trip['speeds'])) * KNOT
    trip['max_speed'] = trip['max_speed'] * KNOT
    duration = trip['leave_time'] - trip['entry_time']
    trip.pop('speeds')

    is_normal_trip = trip['distance'] >= TRIP_MINIMUM_DISTANCE

    if is_normal_trip:
        if trip['max_speed'] > total['max_speed']:
            total['max_speed'] = trip['max_speed']
        total['speeds'].append(trip['average_speed'])
        total['distance'] += trip['distance']
        total['duration'] += duration
        trip['duration'] = duration.total_seconds()

    trip['entry_time'] = trip['entry_time'].isoformat()
    trip['leave_time'] = trip['leave_time'].isoformat()

    if trip['total'] != 0:
        trip['out_of_route_percent'] = int(
            trip['out_of_route'] / trip['total'] * 100)
    else:
        trip['out_of_route_percent'] = 0
    trip.pop('out_of_route')
    trip.pop('total')

    if coordinate_count:
        trip['coordinate_count'] = len(trip['coordinates'])
    if pop_coordinates:
        trip.pop('coordinates')

    if is_normal_trip:
        trips.append(trip)
    else:
        filtered_trips.append(trip)

    if total['total'] != 0:
        total['out_of_route_percent'] = int(
            total['out_of_route'] / total['total'] * 100)
    else:
        total['out_of_route_percent'] = 0
    try:
        total['average_speed'] = sum(total['speeds']) / len(total['speeds'])
    except ZeroDivisionError:
        total['average_speed'] = 0
    total.pop('speeds')
    total['duration'] = total['duration'].total_seconds()

    return trips, total


def define_dump_trips(rows):
    total = {
        "average_speed": 0,
        "distance": 0,
        "duration": 0,
        "max_speed": 0,
        "out_of_route_percent": 0
    }
    total['filtered_trips'] = filtered_trips = []
    trips = []
    speeds = []
    oor_count = 0
    all_count = 0
    for day, device_id, payload in rows:
        if not payload.get('trips'):
            continue
        for trip in payload['trips']:
            is_normal_trip = trip['distance'] >= TRIP_MINIMUM_DISTANCE
            if is_normal_trip:
                trips.append(trip)
            else:
                filtered_trips.append(trip)
            oor_count += (trip['coordinate_count'] *
                          trip['out_of_route_percent']) / 100
            all_count += trip['coordinate_count']
        total['distance'] = payload['total']['distance']
        total['duration'] = payload['total']['duration']
        if payload['total']['max_speed'] > total['max_speed']:
            total['max_speed'] = payload['total']['max_speed']
        speeds.append(payload['total']['average_speed'])
    if speeds:
        total['average_speed'] = sum(speeds) / len(speeds)
    if all_count:
        total['out_of_route_percent'] = (oor_count / all_count) * 100
    total['total'] = all_count
    total['out_of_route'] = oor_count
    return trips, total


def merge_totals(total1: dict, total2: dict):
    total1['average_speed'] = (
        total1['average_speed'] + total2['average_speed']) / 2
    total1['distance'] += total2['distance']
    total1['duration'] += total2['duration']
    if total2['max_speed'] > total1['max_speed']:
        total1['max_speed'] = total2['max_speed']
    if total1['total'] or total2['total']:
        total1['out_of_route_percent'] = (
            total1['out_of_route'] + total2['out_of_route']) / (total1['total'] + total2['total']) * 100
    total1['filtered_trips'] = total1.get(
        'filtered_trips', []) + total2.get('filtered_trips', [])
    return total1


def get_trips_and_total(transport, from_time, to_time, f_calc, f_dump, f_merge):

    now = datetime.datetime.today()
    from_time, to_time = sorted([from_time, to_time])
    from_time = from_time.replace(hour=0, minute=0, second=0)
    to_time = to_time.replace(hour=23, minute=59, second=59)
    if from_time.date() == now.date():
        print(f"[&^&^&^%%$%$] from time is From time is equal with today")
        trips, total = f_calc(transport, from_time, to_time)
    elif to_time.date() != now.date():
        trips, total = f_dump(transport, from_time, to_time)
        if not trips:
            trips, total = f_calc(transport, from_time, to_time)
    else:
        start_today = now.replace(hour=0, minute=0, second=0)
        calc_trips, calc_total = f_calc(transport, from_time, start_today)
        dump_trips, dump_total = f_dump(transport, from_time, start_today)

        trips = calc_trips
        if dump_trips is not None:
            trips += dump_trips

        total_it = filter(bool, [calc_total, dump_total])
        total = next(total_it, {"average_speed": 0,
                                "distance": 0,
                                "duration": 0,
                                "max_speed": 0,
                                "out_of_route_percent": 0,
                                "total": 0,
                                "out_of_route": 0,
                                })

        try:
            total = f_merge(total, next(total_it))
        except StopIteration:
            pass

    return trips, total
