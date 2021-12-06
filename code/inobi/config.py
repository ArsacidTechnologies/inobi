
import os

from decouple import config

DEBUG = config('DEBUG', cast=bool, default=False)

SQL_ECHO = config('SQL_ECHO', cast=bool, default=DEBUG)

APP_NAME = config('APP_NAME', cast=str)

BASE_DIR = os.path.abspath(os.path.curdir)

STATIC_DIRECTORY = config('STATIC_DIRECTORY', cast=str, default='inobi/static')
TEMPLATES_DIRECTORY = config('TEMPLATES_DIRECTORY', cast=str, default='inobi/templates')
RESOURCES_DIRECTORY = config('RESOURCES_DIRECTORY', cast=str, default='resources/')

# from .utils import generate_key as _genkey
APP_TOKEN_SECRET = config('APP_TOKEN_SECRET', cast=str)  # _genkey(32)
FLASK_SECRET = config('FLASK_SECRET', cast=str, default=APP_TOKEN_SECRET)
# print(tag, 'WARNING: regenerate key on app start')

# used in phonenumbers module as default region
APP_REGION = config('APP_REGION', cast=str, default='IR')
APP_TIMEZONE = config('APP_TIMEZONE', cast=str, default="Asia/Tehran")


##### Database #####
__conn_propsd = dict(
    dbname=config('DB_NAME', cast=str),
    user=config('DB_USER', cast=str),
    password=config('DB_PASSWORD', cast=str),
    host=config('DB_HOST', cast=str)
)

# Final connection properties. Touch this only
CONNECTION_PROPS = __conn_propsd
SQL_CONNECTION = ' '.join('{}={}'.format(k, v) for k, v in CONNECTION_PROPS.items())
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}/{dbname}'.format(
    **CONNECTION_PROPS
)

# redis connection
redis_conn = dict(
    host=config('REDIS_HOST', cast=str, default='localhost'),
    port=config('REDIS_PORT', cast=int, default=6379),
    password=config('REDIS_PASSWORD', cast=str, default='')
)

REDIS_URL = 'redis://:{password}@{host}:{port}'.format(**redis_conn)


class RedisSegments:
    ADVERTISEMENT = config('REDIS_DB_ADVERTISEMENT', cast=int)
    BUSES = 5
    SOCKET = 3
    BUSES_V2 = config('REDIS_DB_BUSES', cast=int)
    APPLICATION = config('REDIS_DB_APPLICATION', cast=int)

# redis segments
redis_segments = dict(
    buses=RedisSegments.BUSES,
    advertisement=RedisSegments.ADVERTISEMENT,
    socket=RedisSegments.SOCKET
)

KNOT = 1.851999999984

SENTRY_DSN = config('SENTRY_DSN', cast=str, default='')

TOKEN_EXPIRES_AFTER = config('TOKEN_EXPIRATION_MIN', cast=int, default=60)  # minutes
