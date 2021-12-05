
import enum


def convert_route(route_name, route_type, exclude_from_converting):
    if route_type not in exclude_from_converting:
        num = ''.join(n for n in route_name if n.isdigit())
        if not num.isdigit():
            number = 0
        else:
            number = int(num)
    else:
        number = route_name
    return number


class TransportVariables:
    PASSENGERS_IN = 'passengers_in'
    PASSENGERS_OUT = 'passengers_out'
    CMD = 'cmd'
    TIME = 'time'
    OBD = 'obd'
    SHARED = 'shared_info'
    PHONE = 'phone'
    IMEI = 'imei'
    ADJUSTMENT_LAT = 'adjustment_lat'
    ADJUSTMENT_LNG = 'adjustment_lng'
    DIRECTION_ID = 'direction_id'
    POSITION = 'position'
    BALANCE = 'balance'
    SSH_INFO = 'ssh_info'
    SSH = 'ssh'
    BEARING = "bearing"
    SPEED = "speed"
    PING_TYPE = 'ping_type'

    all = (PASSENGERS_IN, PASSENGERS_OUT, CMD, TIME, OBD, SHARED, PHONE, IMEI, ADJUSTMENT_LAT, ADJUSTMENT_LNG,
           DIRECTION_ID, POSITION, BALANCE, SSH_INFO, PING_TYPE)

    PUBLIC = ("id", "line_id", "path", "location", TIME, "number", "type", SPEED, BEARING, "name", DIRECTION_ID, POSITION)

    # will update on every ping
    online_fields = (PASSENGERS_IN, PASSENGERS_OUT, POSITION, SPEED, BEARING, SSH_INFO)

    class PingType(enum.Enum):
        IDLE = 'idle'
        NORMAL = 'normal'


def check_ping(ping: dict):
    to_del = set()
    for key in ping:
        if key not in TransportVariables.all:
            to_del.add(key)
    for key in to_del:
        ping.pop(key)


_modify_ping = [
    (TransportVariables.ADJUSTMENT_LAT, float, 0),
    (TransportVariables.ADJUSTMENT_LNG, float, 0),
    (TransportVariables.DIRECTION_ID, int, None),
    (TransportVariables.POSITION, float, None),
]


def parse(ping: dict):

    for key, cast, default in _modify_ping:
        ping[key] = cast(ping[key]) if ping.get(key) else default

    if TransportVariables.PING_TYPE not in ping:
        ping[TransportVariables.PING_TYPE] = TransportVariables.PingType.NORMAL.value
