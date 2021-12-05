from .models import ETAPassesTime, PlatformTimeTravel as PlatformTimeTravelDB
from inobi import db
from marshmallow import Schema, fields, post_load


class ETAPassesTimeSerializer(Schema):
    transport_id = fields.Integer()
    route_id = fields.Integer()
    route_type = fields.String()
    hour = fields.Integer()
    quarter = fields.Integer()
    weekday = fields.Integer()
    start_platform = fields.Integer()
    start_time = fields.Integer()
    end_platform = fields.Integer()
    end_time = fields.Integer()


def log(commit=True, **data):
    data = ETAPassesTimeSerializer().load(data)
    eta_log = ETAPassesTime(**data)
    db.session.add(eta_log)
    if commit:
        db.session.commit()
    return data

    # global eta_log_buffer
    # eta_log = ETAPassesTimeSerializer().load(data)
    # eta_log_buffer.append(eta_log)
    # if len(eta_log_buffer) > 10:
    #     [db.session.add(l) for l in eta_log_buffer]
    #     db.session.commit()
    #     eta_log_buffer[:] = []


class PlatformTimeTravel(Schema):
    id = fields.Integer()
    platform_id = fields.Integer()
    transport_id = fields.Integer()
    entry_time = fields.Float()
    leave_time = fields.Float()


def platform_time_travel_log(commit=True, **data):
    data = PlatformTimeTravel().load(data)
    platform_log = PlatformTimeTravelDB(**data)
    db.session.add(platform_log)
    if commit:
        db.session.commit()
    return data


def scheduled_eta(platform_id, from_time, weekday, route_ids, quarter, hour=None):
    q = db.session.query(ETAPassesTime.route_id, ETAPassesTime.time)\
        .filter(ETAPassesTime.time > from_time,
                ETAPassesTime.weekday == weekday,
                ETAPassesTime.route_id.in_(route_ids),
                ETAPassesTime.end_platform == platform_id,
                ETAPassesTime.quarter == quarter)

    if hour:
        q = q.filter(ETAPassesTime.hour == hour)

    data = q.order_by(ETAPassesTime.time).all()
    schedule = {}
    if data:
        route_id, time = data[0]
        schedule[route_id] = {
            "prev_time": time,
            "diffs": []
        }

    for i, row in enumerate(data[1:], 1):
        route_id, time = row
        if route_id not in schedule:
            schedule[route_id] = {
                "prev_time": time,
                "diffs": []
            }
        else:
            prev_time = schedule[route_id]['prev_time']
            diff = time - prev_time
            schedule[route_id]['prev_time'] = time
            schedule[route_id]['diffs'].append(diff.seconds)
    resp = {}
    for key, val in schedule.items():
        length = len(val['diffs'])
        if length > 0:
            resp[key] = round(sum(val['diffs']) / length, 2)
    return resp

