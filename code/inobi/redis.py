from redis import Redis
from typing import NewType

from inobi.config import redis_conn

from functools import lru_cache


Segment = NewType('Segment', int)


@lru_cache(None)
def getredis(db: Segment = 0) -> Redis:
    return Redis(**redis_conn, db=db)


@lru_cache(None)
def getRedis(db):
    try:
        return dict(code=200, data=Redis(**redis_conn, db=db))
    except:
        return dict(code=500, message='can not connect to redis')
