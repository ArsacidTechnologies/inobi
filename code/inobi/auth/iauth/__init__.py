import redis as Redis
import json
from .config import Codes
from .exceptions import get_exception, InternalServerError
import string, random


def generate_random(length=10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


class Auth:
    key = None
    redis = None
    pubsub = None
    timeout = 5

    get_info = 'get'
    set_info = 'set'
    login_ = 'login'

    user_info = 'info'
    user_infos = 'infos'

    def __init__(self, api_key, redis_url, timeout=5):
        self.key = api_key
        self.redis = Redis.StrictRedis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        self.timeout = timeout

    def __open_conn(self):
        self.pubsub = self.redis.pubsub()

    def __close_conn(self):
        self.pubsub.close()

    import typing as T

    def infos(self, ids: T.Iterable[int], timeout=timeout) -> T.Dict[int, dict]:
        data = {
            "user_ids": list(ids),
        }
        r = self.__communicate(data, type=self.user_infos)
        return {u['id']: u for u in r}

    def info(self, id: int, timeout=timeout) -> T.Optional[dict]:
        data = {
            "user_id": id,
        }
        return self.__communicate(data, type=self.user_info)

    def payload(self, token, timeout=timeout):
        data = {
            "token": token,
        }
        return self.__communicate(data, type=self.get_info)

    def add_to_payload(self, token: str, data: dict, timeout=timeout):
        data = {
            "token": token,
            "payload": data,
        }
        return self.__communicate(data, type=self.set_info)

    def __parse_response(self, r):
        if r and r['type'] == 'message':
            response = json.loads(r['data'].decode())
            if response['code'] != Codes.ok:
                raise get_exception(response['code'])()
            return response['data']
        raise InternalServerError(msg='auth sever is unreachable')

    def login(self, username, password, timeout=timeout):
        data = {
            "username": username,
            "password": password
        }
        return self.__communicate(data, self.login_)

    def __communicate(self, data, type=get_info):
        pubsub = self.redis.pubsub()
        listener_id = generate_random()
        pubsub.subscribe(listener_id)
        data['id'] = self.key
        data['listener_id'] = listener_id
        self.redis.publish(type, json.dumps(data))
        none_count = 0
        while 1:
            r = pubsub.get_message(True, 0.1)
            if not r:
                if none_count >= 5:
                    break
                else:
                    none_count += 1
            else:
                break

        pubsub.close()
        return self.__parse_response(r)



