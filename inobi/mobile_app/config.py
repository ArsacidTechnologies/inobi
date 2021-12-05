from os import makedirs
from os.path import abspath, join
from inobi.config import RESOURCES_DIRECTORY, APP_NAME
from inobi import add_prerun_hook
from decouple import config


APP_VERSION = 2

TOKEN_EXPIRES_AFTER = config('TOKEN_EXPIRATION_MIN', cast=int, default=60)  # minutes

PREFIX = '/app'

RESOURCES_APP = join(RESOURCES_DIRECTORY, 'app/')

APP_USER_PICTURES_DIRECTORY = join(RESOURCES_APP, 'users/pictures/')

APP_DB_DIRECTORY = abspath(join(RESOURCES_APP, 'db/'))


def _mkdirs():
    makedirs(APP_USER_PICTURES_DIRECTORY, exist_ok=True)
    makedirs(APP_DB_DIRECTORY, exist_ok=True)

add_prerun_hook(_mkdirs)


DB_NAME_UNFORMATTED = 'inobi_v{}.db'
DB_ZIP_FILENAME_UNFORMATTED = 'inobi_v{}.zip'

DB_FILENAME_IN_ARCHIVE = 'data.db'
DB_TEMP_FILENAME = 'uploaded.db.tmp'
DB_VERSION_INDEX = '.version.index'


# socials credentials
FACEBOOK_APP_ID = '188634255031476'
FACEBOOK_APP_ACCESS_TOKEN = '188634255031476|D9I3p1THt3SGlw9tcMfqEcCC-co'

GOOGLE_CLIENT_IDS = [
    '752187413491-s6hiqpbtekjqchomsbauc07478tqcnte.apps.googleusercontent.com',
    '752187413491-kt6hphosmedoo4h26jnkuhc1of7k6dbg.apps.googleusercontent.com',
    '752187413491-e2oubasj3mpuns7ebqfhljif2v4st4jt.apps.googleusercontent.com',
    '432037877850-cdmp2m9nci5826r1fldesa7k2oes3mfq.apps.googleusercontent.com'
]


# directions config
DIRECTIONS_DB_PATH = join(RESOURCES_APP, 'directions.db')

# directions config
DIRECTIONS_BFS_DB_PATH = join(RESOURCES_APP, 'bfs_directions.db')


##################
## VERIFICATION ##
##################

PHONE_VERIFIER = config('PHONE_VERIFIER', cast=str)  # enum: 'melipayamak', 'verifire'
EMAIL_VERIFIER = config('EMAIL_VERIFIER', cast=str)   # enum: 'email_smtp',

VERIFICATION_REQUEST_TIMEOUT = config('VERIFICATION_REQUEST_TIMEOUT', cast=int, default=int(24 * 60 * 60))
VERIFICATION_MAX_CHECK_ATTEMPTS = config('VERIFICATION_MAX_CHECK_ATTEMPTS', cast=int, default=5)
VERIFICATION_MAX_SEND_ATTEMPTS = config('VERIFICATION_MAX_SEND_ATTEMPTS', cast=int, default=5)

# VERIFIER settings
VERIFIRE_FROM = config('VERIFIRE_FROM', cast=str, default=False)  # = APP_NAME

# for tests in Bishkek
# VERIFIRE_CREDENTIALS = ('1349a8f7b1cdb085ffe739c8fc8a1401', '67c177e75dc651c73cccf5b6f9269fbf')

# prod for Iran
VERIFIRE_DEBUG = config('VERIFIRE_DEBUG', cast=bool, default=False)
VERIFIRE_OUTPUT = config('VERIFIRE_OUTPUT', cast=str, default='console')
VERIFIRE_USERNAME = config('VERIFIRE_USERNAME', cast=str, default='')
VERIFIRE_PASSWORD = config('VERIFIRE_PASSWORD', cast=str, default='')
VERIFIRE_CREDENTIALS = (VERIFIRE_USERNAME, VERIFIRE_PASSWORD)


PHONE_VERIFIER_MESSAGE_TEMPLATE = "Your verfication code: {code}"

# MELIPAYAMAK (Iran sms provider) verification settings
MELIPAYAMAK_DEBUG = config('MELIPAYAMAK_DEBUG', cast=bool, default=False)
MELIPAYAMAK_OUTPUT = config('MELIPAYAMAK_OUTPUT', cast=str, default='console')
MELIPAYAMAK_USERNAME = config('MELIPAYAMAK_USERNAME', cast=str, default='')
MELIPAYAMAK_PASSWORD = config('MELIPAYAMAK_PASSWORD', cast=str, default='')
MELIPAYAMAK_CREDENTIALS = (MELIPAYAMAK_USERNAME, MELIPAYAMAK_PASSWORD)
MELIPAYAMAK_NUMBER = config('MELIPAYAMAK_NUMBER', cast=str, default='500010604671')  # '500010604671'
MELIPAYAMAK_CODE_MESSAGE_TEMPLATE = PHONE_VERIFIER_MESSAGE_TEMPLATE


NIKITA_DEBUG = config('NIKITA_DEBUG', cast=bool, default=False)
NIKITA_OUTPUT = config('NIKITA_OUTPUT', cast=str, default='console')
NIKITA_USERNAME = config('NIKITA_USERNAME', cast=str, default='')
NIKITA_PASSWORD = config('NIKITA_PASSWORD', cast=str, default='')
NIKITA_NUMBER = config('NIKITA_NUMBER', cast=str, default='500010604671')  # '500010604671'
NIKITA_SENDER = config('NIKITA_SENDER', cast=str, default='Tez')
NIKITA_CODE_MESSAGE_TEMPLATE = PHONE_VERIFIER_MESSAGE_TEMPLATE


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


# email verification settings
SMTP_LOGIN_USERNAME = config('SMTP_LOGIN_USERNAME', cast=str, default='')
SMTP_LOGIN_PASSWORD = config('SMTP_LOGIN_PASSWORD', cast=str, default='')
SMTP_SERVER = config('SMTP_SERVER', cast=str, default='')
SMTP_LOGIN = (SMTP_LOGIN_USERNAME, SMTP_LOGIN_PASSWORD)
SMTP_DEBUG = config('SMTP_DEBUG', cast=bool, default=False)
SMTP_OUTPUT = config('SMTP_OUTPUT', cast=str, default='console')

# SMTP_SERVER = 'smtp.yandex.ru:465'
# SMTP_LOGIN = ('noreply@inobi.kg', 'doh3Uth7oV5i')

# SMTP_SERVER = 'smtp.gmail.com:587'
# SMTP_LOGIN = ('inobinoreply@gmail.com', '7n3dyjFn2o8e')

RIGHTEL_DEBUG = config('RIGHTEL_DEBUG', cast=bool, default=False)
RIGHTEL_USERNAME = config('RIGHTEL_USERNAME', cast=str, default='')
RIGHTEL_PASSWORD = config('RIGHTEL_PASSWORD', cast=str, default='')
RIGHTEL_PHONE_NUMBER = config('RIGHTEL_PHONE_NUMBER', cast=str, default='9200000000')
RIGHTEL_WSDL_URL = config('RIGHTEL_WSDL_URL', cast=str, default='http://example.com/wsdl')
RIGHTEL_OUTPUT = config('RIGHTEL_OUTPUT', cast=str, default='console')
RIGHTEL_WSDL_CACHE_TIMEOUT = config('RIGHTEL_WSDL_CACHE_TIMEOUT', cast=float, default=60*60)
RIGHTEL_MESSAGE_DOMAIN = 'publictransport'
