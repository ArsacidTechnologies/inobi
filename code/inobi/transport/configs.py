from os import makedirs
from os.path import abspath, join
from inobi.config import RESOURCES_DIRECTORY
from inobi import add_prerun_hook

RESOURCES_LINE = join(RESOURCES_DIRECTORY, 'transport')
LINE_DB_DIRECTORY = abspath(join(RESOURCES_LINE, 'db/'))
AUDIO_RESOURCES = abspath(join(RESOURCES_LINE, 'audio/'))
AUDIO_INFO_RESOURCES = abspath(join(RESOURCES_LINE, 'audio_info'))
TMP_DIRECTORY = join(RESOURCES_DIRECTORY, 'tmp')

TRANSPORT_PICTURE_DIRECTORY = abspath(join(RESOURCES_LINE, 'pictures/'))
TRANSPORT_REPORT_DIRECTORY = abspath(join(RESOURCES_LINE, 'reports'))


def _mkdirs():
    makedirs(AUDIO_RESOURCES, exist_ok=True)
    makedirs(LINE_DB_DIRECTORY, exist_ok=True)
    makedirs(TRANSPORT_PICTURE_DIRECTORY, exist_ok=True)
    makedirs(TRANSPORT_REPORT_DIRECTORY, exist_ok=True)
    makedirs(AUDIO_INFO_RESOURCES, exist_ok=True)
    makedirs(TMP_DIRECTORY, exist_ok=True)


add_prerun_hook(_mkdirs)

_PREFIX = '/transport'

# Api-Line
__url_line = dict(
    upload='/line/upload',
    list='/line/list',
    line='/line',
    station='/station',
    migrate='/line/update',
    download='/line/download',
    platforms='/platforms',
    platform_routes='/platform_routes'
)

# Api-Bus
__url_bus = dict(
    bus='/bus',
    saveBus='/bus/save',
    deleteBus='/bus/delete',
    listBuses='/bus/list',
    getUnknownBuses='/bus/unknown'
)

# Api-Subscribe
__url_subscribe = dict(
    adminSubscribe='/admin/subscribe',
    subscribe='/subscribe',
    driver='/driver/subscribe'
)


# SocketIO events
class Event:
    SUBSCRIBE = 'subscribe'
    JOIN = 'join'
    LEAVE = 'leave'
    NOTIFICATION = 'notification'

    class NotificationType:
        ADD = 'add'
        DELETE = 'delete'


# SocketIO Rooms
class Room:
    UNKNOWN = 'unknown'
    CITY = 'city'
    ORGANIZATION = 'organization'
    NOTIFICATION_TEMPLATE = 'notification_{}'

    @classmethod
    def notification(cls, to_id: int) -> str:
        return cls.NOTIFICATION_TEMPLATE.format(to_id)

    @classmethod
    def organization_subscribe(cls, to_id: int) -> str:
        return "{}_{}".format(cls.ORGANIZATION, to_id)

    @classmethod
    def city_subscribe(cls, to_id: int) -> str:
        return "{}_{}".format(cls.CITY, to_id)

# Transport scopes
scope = dict(
    admin='transport_admin',
    viewer='transport_viewer',
    app='public',
    transport='transport'
)




# WS NAMESPACES
WS_ADMIN_NAMESPACE = '/transport/admin'
WS_TRANSPORT_NAMESPACE = '/transport'
WS_BASE_NAMESPACE = '/'
WS_DRIVER_NAMESPACE = '/transport/driver'
WS_TRANSPORT_V2_NAMESPACE = '/transport/v2'


from decouple import config

# TRACCAR MIDDLEWARE
TRACCAR_SYNC_ACTIVE = config('TRACCAR_SYNC_ACTIVE', cast=bool, default=True)
traccar_url = config('TRACCAR_API_URL', cast=str)
# traccar_url = 'http://192.168.1.241:8082/api'
# traccar_url = 'http://192.168.1.88:8082/api'
traccar_dbpath = RESOURCES_LINE + '/traccarMD.db'
# traccar_username = 'inobi'
# traccar_password = 'BaKT0#@123&7230p'
traccar_username = config('TRACCAR_API_USERNAME', cast=str)
traccar_password = config('TRACCAR_API_PASSWORD', cast=str)
traccar_region = config('TRACCAR_REGION', cast=str)
traccar_colors = dict(forward='blue',
                      backward='green',
                      circular='blue')
traccar_force_update_line = config('TRACCAR_FORCE_UPDATE_ROUTES', cast=bool, default=False)
traccar_db_connection = dict(host=config('TRACCAR_DB_HOST', cast=str),
                             password=config('TRACCAR_DB_PASSWORD', cast=str),
                             dbname=config('TRACCAR_DB_NAME', cast=str),
                             user=config('TRACCAR_DB_USER', cast=str))
TRACCAR_SQL_CONNECTION = ' '.join('{}={}'.format(k, v) for k, v in traccar_db_connection.items())

INOBI_BOX_TOKEN = 'ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SjBhVzFsSWpveE5UTXdNVEF4T0RNM0xDSnpZMjl3WlhNaU9sc2lkSEpoYm5Od2IzSjBYM1Z1YVhRaUxDSjBjbUZ1YzNCdmNuUmZkVzVwZENoa1pXWmhkV3gwS1NKZExDSnBZWFFpT2pFMU16QXdPVGs1TWpRc0ltbHpjeUk2SW1seWMyRnNZV0prUUdkdFlXbHNMbU52YlNKOS45X1RlUGw3SGowckhEemhlMWpfal9mWkRCNWN2SjRyOXJ6R2ZDM1FhT0lJ'


class DriverConfig:

    CLEANUP_ON_APP_START = False
    DEFAULT_POINT_EXPIRATION_INTERVAL = 15*60

    UPDATE_RATHER_THAN_CREATE_POINT_RADIUS = 0.3  # kilometers

    DEFAULT_POINT_TYPE = 'be_aware'


class TONotificationSettingKeys:
    MAX_SPEED = 'max_speed'
    BALANCE = 'balance'


VOICE_ANNOUNCEMENT_LANGUAGES = config('VOICE_ANNOUNCEMENT_LANGUAGES',
                                      cast=lambda x: [y.strip().lower() for y in x.split(',') if y.strip()] if x else None,
                                      default=None)


class AudioConfig:
    MD5_HASH_FILE = 'md5_hash'
    MIMETYPE = ['audio/wave', 'audio/x-wav', 'audio/wav']
    FORMAT = 'wav'
    FORMAT_ = '.wav'

    class Lang:
        ALL = VOICE_ANNOUNCEMENT_LANGUAGES if VOICE_ANNOUNCEMENT_LANGUAGES else []

    class Type:
        CURRENT = 'current'
        NEXT = 'next'
        ALL = [CURRENT, NEXT]


BOX_INSTRUCTIONS = {
    "obd_pids": []
}

if VOICE_ANNOUNCEMENT_LANGUAGES:
    BOX_INSTRUCTIONS['voice'] = {
        "lang": {
            i + 1: {
                "name": lang,
                "action": 0
            }
            for i, lang in enumerate(VOICE_ANNOUNCEMENT_LANGUAGES)
        }
    }


class TKeys:
    TRANSPORTS = 'transports'
    LINES = 'lines'
    UNKNOWNS = 'unknowns'
    ORGANIZATIONS = 'organizations'
    ORGANIZATION_LINES = 'organization_lines'
    INSTRUCTIONS = 'instructions'
    INSTRUCTION_RESULTS = 'instruction_results'
    ETA = 'transports_eta'
    ETA_KEY = '{transport}:{platform}'
    ETA_EXP_SEC = 3600

    CACHED_SUBSCRIBES = 'cached_subscribe:{line_id}'

    @classmethod
    def eta_key(cls, transport, platform):
        return cls.ETA_KEY.format(transport=transport, platform=platform)

    @classmethod
    def cached_subs_key(cls, line_id):
        return cls.CACHED_SUBSCRIBES.format(line_id=line_id)


class Reasons:
    CHECKED_IN = 'driver checked in'
    CHECKED_OUT = 'driver checked out'


class Attachment:
    REPORT = 'report'


class DirectionTypes:
    FORWARD = 'forward'
    BACKWARD = 'backward'
    CIRCULAR = 'circular'

    ALL = [FORWARD, BACKWARD, CIRCULAR]


class RouteTypes:
    BUS = 'bus'
    TROLLEYBUS = 'trolleybus'
    SHUTTLE_BUS = 'shuttle_bus'

    TECHNICAL = 'technical'

    ALL = [BUS, TROLLEYBUS, SHUTTLE_BUS, TECHNICAL]


class LinkPossibilities:
    STATION_ROUTES = 'station_routes'
    STATION_PLATFORMS = 'station_platforms'
    ROUTE_DIRECTIONS = 'route_directions'
    DIRECTION_PLATFORMS = 'direction_platforms'
    PLATFORMS_DIRECTIONS = 'platforms_directions'

    ALL = [STATION_PLATFORMS]


# email verification settings
SMTP_LOGIN_USERNAME = config('SMTP_LOGIN_USERNAME', cast=str, default='')
SMTP_LOGIN_PASSWORD = config('SMTP_LOGIN_PASSWORD', cast=str, default='')
SMTP_SERVER = config('SMTP_SERVER', cast=str, default='')
SMTP_LOGIN = (SMTP_LOGIN_USERNAME, SMTP_LOGIN_PASSWORD)


# SSH PART
class SSHConf:
    DEFAULT_PORT = 22
    DEFAULT_HOST = 'box@devz.inobi.kg'


class PlatformConfig:

    BUFFER_LIMIT = config("BUFFER_LIMIT", cast=int, default=10)
    IS_ADJUSTMENT_ACTIVE = config('IS_ADJUSTMENT_ACTIVE', cast=bool, default=False)
    PINGS_TIME_LIMIT = config('PINGS_TIME_LIMIT', cast=int, default=60*5)
    OUT_OF_ROUTE_DISTANCE_LIMIT = config('OUT_OF_ROUTE_DISTANCE_LIMIT', cast=int, default=300)

    NOTIFICATION_ENTRY_DISTANCE = config('NOTIFICATION_ENTRY_DISTANCE', cast=int, default=100)
    NOTIFICATION_LEAVE_INTERVAL = config('NOTIFICATION_LEAVE_INTERVAL',
                                         cast=lambda x: [int(y.strip()) for y in x.split(',')],
                                         default='20, 120')

    PLATFORMS_LAYER = 'platforms'
