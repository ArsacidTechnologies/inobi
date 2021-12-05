from inobi.redis import getRedis
from inobi.config import redis_segments
import pickle

class redis_controller:
    def delete(self, segment):
        redis = getRedis(redis_segments['buses'])
        if redis['code'] != 200:
            return redis
        redis = redis['data']
        buses = []
        keys = redis.hgetall(segment)
        if not keys:
            return dict(code=404, message='there is no unknowns')
        for value in keys.values():
            bus = pickle.loads(value)
            bus['path'] = list(bus['path'])
            buses.append(bus)
        deleted = redis.delete(segment)
        if not deleted:
            return dict(code=500, message='INTERNAL REDIS ERROR')
        return dict(code=200, data=buses)

    def flushall(self):
        redis = getRedis(redis_segments['buses'])
        if redis['code'] != 200:
            return redis
        redis = redis['data']
        answer = redis.flushdb()
        if answer:
            return dict(code=200)
        else:
            return dict(code=500, message='{}'.format(answer))


