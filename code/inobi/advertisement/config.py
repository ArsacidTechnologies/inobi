from os.path import join
from os import makedirs

from inobi.config import RESOURCES_DIRECTORY
from inobi import add_prerun_hook

NAME = 'Advertisement'

PREFIX = '/advertisement'

RESOURCES_ADS = join(RESOURCES_DIRECTORY, 'advertisement/')


_p = lambda x: join(RESOURCES_ADS, x, '')

DIRECTORIES = {
    'media': _p('media'),
    'temp': _p('temp'),
    'thumbnail_media': _p('media/thumbnail'),
    'thumbnail_temp': _p('temp/thumbnail'),
    'box_updates': _p('box_updates'),
    'external': _p('external'),
}


def on_app_run():
    for _, directory in DIRECTORIES.items():
        makedirs(directory, exist_ok=True)

add_prerun_hook(on_app_run)


BOX_UPDATE_FILE = 'update'

ALLOW_INTERNET_OPTIONS = frozenset(('true', 'on', 'allow', True))

AD_MIN_RADIUS_PARAMETER = 0.5
AD_MAX_RADIUS_PARAMETER = 3.0
AD_DEFAULT_RADIUS_PARAMETER = AD_MIN_RADIUS_PARAMETER

SECURITY_BOX_SECRET = 'x7oV13J6nn33OFDog11lxIzO1lNNbsxBKUlAL1Zd'

IMAGE_EXTENSIONS = ('jpg', 'png', 'bmp', 'jpeg')  # todo: check "jpeg" format compatibility when uploading files
VIDEO_EXTENSIONS = ('mp4', 'flv', 'avi')
IFRAME_EXTENSIONS = ('html', )

ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS + IFRAME_EXTENSIONS

from datetime import timedelta
from decouple import config

USER_DEVICE_VERIFIED_INTERVAL = timedelta(days=config('ADVERTISEMENT_USER_DEVICE_VERIFIED_INTERVAL', cast=float, default=365))
AD_USER_MAX_LOGIN_DAY = config('AD_USER_MAX_LOGIN_DAY', cast=int, default=2)
AD_USER_LOGIN_BLOCK_DURATION = config('AD_USER_LOGIN_BLOCK_DURATION', cast=int, default=5)
AD_USER_CONNECTION_DURATION = config('AD_USER_CONNECTION_DURATION', cast=int, default=1)
AD_SKIP_TIMER = config('AD_SKIP_TIMER', cast=int, default=5)

SHAHKAR_DEBUG = config('SHAHKAR_DEBUG', cast=bool, default=False)
SHAHKAR_HOST = config('SHAHKAR_HOST', cast=str, default='http://185.24.139.58:80')
SHAHKAR_WIFIMOBILE_API = config(
    'SHAHKAR_WIFIMOBILE_API', cast=str,
    default='/AraShahkartest/RestService/wifimobile',
)
SHAHKAR_WIFIMOBILE_CLOSE_API = config(
    'SHAHKAR_WIFIMOBILE_CLOSE_API', cast=str,
    default='/AraShahkartest/RestService/wifimobile/close',
)
SHAHKAR_ID_MATCHING_API = config(
    'SHAHKAR_ID_MATCHING_API', cast=str,
    default='/AraShahkartest/RestService/serviceID-Matching',
)
SHAHKAR_CLOSE_REGISTRATION_IMMEDIATELY = config(
    'SHAHKAR_CLOSE_REGISTRATION_IMMEDIATELY', cast=bool, default=False,
)
