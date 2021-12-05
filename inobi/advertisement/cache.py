from pickle import loads, dumps
from functools import partial
import traceback, sys

from inobi.config import RedisSegments
from inobi.redis import getredis

from .utils import debug_exception

from redis.exceptions import ConnectionError


tag = '@ads.cache:'


def _getredis():
    r = getredis(RedisSegments.ADVERTISEMENT)
    r.ping()
    return r


class CKeys:
    BOX_VERSION = 'advertisement:box_version'
    INTERNET = 'advertisement:internet'


def getcached(key, default=None):
    try:
        r = _getredis()
    except ConnectionError as e:
        debug_exception(tag, e, True)
        return default

    redis_value = r.get(key)
    if redis_value is None:
        return default
    return loads(redis_value)


def cache(key, value, **kwargs) -> bool:
    try:
        r = _getredis()
    except ConnectionError as e:
        debug_exception(tag, e, True)
        return False

    if value is None:
        return r.delete(key) > 0
    pickled = dumps(value)
    return r.set(key, pickled, **kwargs)
