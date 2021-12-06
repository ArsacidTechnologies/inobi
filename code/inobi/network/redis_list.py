
class RedisList:
    def __init__(self, list_key, redis_client):
        self.__redis = redis_client
        self.list_key = list_key

    def __len__(self):
        return self.__redis.llen(self.list_key)

    def push_right(self, val):
        return self.__redis.rpush(self.list_key, val)

    def pop_left(self):
        value = self.__redis.lpop(self.list_key)
        if value is None:
            raise IndexError
        return value

    def pop_right(self):
        value = self.__redis.rpop(self.list_key)
        if value is None:
            raise IndexError
        return value

    def pop_all(self):
        rv = self.__redis.lrange(self.list_key, 0, -1)
        self.__redis.delete(self.list_key)

        return rv

    def __unicode__(self):
        "Represent entire list."
        return u"RedisList(%s)" % (self[0:-1],)

    def __repr__(self):
        "Represent entire list."
        return self.__unicode__()

