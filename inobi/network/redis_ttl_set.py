import time


class RedisTTLSet:
    def __init__(self, list_key, redis_client, ttl):
        self.__redis = redis_client
        self.list_key = list_key
        self.ttl = ttl

    def __len__(self):
        return self.__redis.llen(self.list_key)

    def add_item(self, item):
        now = int(time.time())
        # self.__redis.zremrangebyscore(self.list_key, '-inf', now)
        return self.__redis.zadd(self.list_key, item, now + self.ttl)

    def get_all(self):
        now = int(time.time())
        pipeline = self.__redis.pipeline()
        pipeline.zrangebyscore(self.list_key, now, '+inf')
        pipeline.delete(self.list_key)
        return pipeline.execute()[0]
        # rv = self.__redis.zrangebyscore(self.list_key, now, '+inf')
        # self.__redis.delete(self.list_key)
        # return rv

    def __unicode__(self):
        "Represent entire list."
        return u"RedisList(%s)" % (self[0:-1],)

    def __repr__(self):
        "Represent entire list."
        return self.__unicode__()

