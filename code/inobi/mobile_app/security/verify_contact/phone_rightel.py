
import typing as T

from zeep import Client
from zeep.cache import InMemoryCache
from zeep.transports import Transport

from . import (
    Contact, BaseVerifier,
    _generate_verification_code, _generate_request_id,
    getredis, error_codes,
    ContactVerificationException as BaseVerificationException
)
from ... import config

assert config.RIGHTEL_OUTPUT in ('console', )


wsdl_cache = InMemoryCache(timeout=config.RIGHTEL_WSDL_CACHE_TIMEOUT)


class PhoneVerificationException(BaseVerificationException):
    pass


class RedisKey:
    CHECK_TRY_COUNTS = 'app:verification:rightel:check_tries'
    SEND_TRY_COUNTS = 'app:verification:rightel:send_tries'
    REQUEST_IDS = 'app:verification:rightel:request_id'
    CODES = 'app:verification:rightel:code'


class Api:
    WSDL = config.RIGHTEL_WSDL_URL
    ENQUEUE = 'enqueue'


class Status:
    """
    responses :
    8 digit length => messageID: successful submit, reference for further delivery report check
    0=> error: required parameters are null
    3=>error: destination parameter is null
    12=>error: the 9200400000 balance is not enough to send message
    20=>error: the message length is not permitted
    51=>error: the credentials are not correct
    53=>error: the No. of submitted messages exceeded the limit
    17=> error: web service access is not allowed. please contact the technical team.
    """
    REQUIRED_PARAMS_NULL = 0
    DESTINATION_NULL = 3
    BALANCE_NOT_ENOUGH = 12
    SERVICE_UNAVAILABLE = 17
    MESSAGE_LENGTH_NOT_PERMITTED = 20
    CREDENTIALS_NOT_CORRENT = 51
    MESSAGES_NUMBER_LIMIT_EXCEED = 53

    OK = None

    @classmethod
    def detect(cls, v) -> T.Optional[str]:
        for an in dir(cls):
            if not an.startswith('_') and an.isupper() and v == getattr(cls, an):
                return an
        return cls.OK  # OK is None


RequestId = str
Phone = Contact


class RightelPhoneVerifier(BaseVerifier):

    def code(self, request_id) -> T.Optional[str]:
        return getredis().hget(RedisKey.CODES, request_id)

    def _get_request_id(self, phone, r=None, _rk=RedisKey.REQUEST_IDS) -> T.Optional[RequestId]:
        if not r:
            r = getredis()
        rid = r.get('{}:{}'.format(_rk, phone))
        if rid:
            return rid.decode()
        return rid

    def _get_code(self, request_id, r=None, _rk=RedisKey.CODES):
        if not r:
            r = getredis()
        return_value = r.get('{}:{}'.format(_rk, request_id))
        if type(return_value) == bytes:
            return_value = return_value.decode()
        return return_value

    def send(self, contact, *args, mac=None, **kwargs) -> RequestId:
        phone = contact
        """Sends verification code to given phone number"""
        r = getredis()
        code = _generate_verification_code()
        request_id = mac or (self._get_request_id(phone, r) or _generate_request_id())

        if config.RIGHTEL_DEBUG:
            if config.RIGHTEL_OUTPUT == 'console':
                print(phone, code)
            return request_id

        send_try_counts_key = '{}:{}'.format(RedisKey.SEND_TRY_COUNTS, mac or request_id)
        send_tries_count = r.incr(send_try_counts_key, 1)
        r.expire(send_try_counts_key, config.VERIFICATION_REQUEST_TIMEOUT)
        if type(send_tries_count) == bytes:
            send_tries_count = send_tries_count.decode()
        if int(send_tries_count) > config.VERIFICATION_MAX_SEND_ATTEMPTS:
            raise PhoneVerificationException('Too Many Send Attempts',
                                             error_codes.TOO_MANY_SEND_ATTEMPTS)
        r.setex('{}:{}'.format(RedisKey.REQUEST_IDS, phone), request_id, config.VERIFICATION_REQUEST_TIMEOUT)
        r.setex('{}:{}'.format(RedisKey.CODES, request_id), code, config.VERIFICATION_REQUEST_TIMEOUT)

        enqueue_args = {
            'username': config.RIGHTEL_USERNAME,
            'password': config.RIGHTEL_PASSWORD,
            'domain': config.RIGHTEL_MESSAGE_DOMAIN,
            'msgType': 0,
            'messages': [config.PHONE_VERIFIER_MESSAGE_TEMPLATE.format(code=code)],
            'destinations': [phone],
            'originators': [config.RIGHTEL_PHONE_NUMBER],
            'udhs': [''],
            'mClass': [''],
        }
        client = Client(config.RIGHTEL_WSDL_URL, transport=Transport(cache=wsdl_cache))
        # r = client.service.enqueue(**enqueue_args)
        response = getattr(client.service, Api.ENQUEUE)(**enqueue_args) # r is "8 digit length number"
        # if not isinstance(r, list):
        #     raise PhoneVerificationException('1. Phone provider WSDL error.', error_codes.PHONE_VERIFICATION_ERROR)
        # (response, ) = response
        # if not isinstance(response, int):
        #     raise PhoneVerificationException('2. Phone provider WSDL error.', error_codes.PHONE_VERIFICATION_ERROR)
        status = Status.detect(response)

        if status in (Status.OK, None):
            return request_id
        raise PhoneVerificationException('{}: {}'.format(r, status), error_codes.PHONE_VERIFICATION_ERROR)

    def check(self, contact, code, mac=None, cleanup_on_success=True, check=False) -> Contact:
        phone = contact
        r = getredis()
        # FIXME: IF REQUEST_ID DOESN'T EXIST, USER CAN CHECK MULTIPLE TIMES.
        request_id = mac or self._get_request_id(phone, r)
        if request_id is None:
            raise PhoneVerificationException('REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS',
                                             error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS)
        if config.RIGHTEL_DEBUG:
            if config.RIGHTEL_OUTPUT == 'console':
                print(phone, code)
            return phone

        check_tries_count = '{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, mac or request_id)
        r.incr(check_tries_count, 1)
        r.expire(check_tries_count, config.VERIFICATION_REQUEST_TIMEOUT)
        tries_count = r.get(check_tries_count)
        if type(tries_count) == bytes:
            tries_count = tries_count.decode()
        tries_count = int(tries_count)
        if tries_count > config.VERIFICATION_MAX_CHECK_ATTEMPTS:
            raise PhoneVerificationException('Too Many Check Attempts',
                                             error_codes.TOO_MANY_CHECK_ATTEMPTS)

        redis_phone_code = self._get_code(mac or request_id, r)
        if redis_phone_code == code:
            if cleanup_on_success:
                self._clean(phone, r)
            return phone
        raise PhoneVerificationException('Invalid code',
                                         error_codes.INVALID_CODE)

    def _clean(self, phone, _r=None, **kwargs):
        if _r is None:
            _r = getredis()
        request_id = _r.hget(RedisKey.REQUEST_IDS, phone)
        _r.delete('{}:{}'.format(RedisKey.SEND_TRY_COUNTS, request_id))
        _r.delete('{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, request_id))
        _r.delete('{}:{}'.format(RedisKey.CODES, request_id))
        _r.delete('{}:{}'.format(RedisKey.REQUEST_IDS, phone))

    def status(self, value, status_type="all", request_id=None, mac=None):
        r = getredis()

        if not request_id:
            request_id = self._get_request_id(value)

        output = {
            "send_code_attempt": {
                "status_code": 704,
                "total_requests": None,
                "block_duration": None,
                "is_blocked": False
            },
            "verify_code_attempt": {
                "status_code": 704,
                "total_requests": None,
                "block_duration": None,
                "is_blocked": False
            }
        }

        if (request_id is None) and (mac is None):
            return output

        send_tries_count = r.get('{}:{}'.format(RedisKey.SEND_TRY_COUNTS, mac or request_id))
        if send_tries_count:
            if type(send_tries_count) == bytes:
                send_tries_count = send_tries_count.decode()
            send_tries_count = send_tries_count.decode()
            output['send_code_attempt']['total_requests'] = int(send_tries_count)
            if int(send_tries_count) > config.VERIFICATION_MAX_SEND_ATTEMPTS:
                block_duration = r.ttl('{}:{}'.format(RedisKey.SEND_TRY_COUNTS, mac or request_id))
                output['send_code_attempt']['block_duration'] = block_duration
                output['send_code_attempt']['status_code'] = 700
                output['send_code_attempt']['is_blocked'] = True
            else:
                output['send_code_attempt']['status_code'] = 700

        check_tries_count = r.get('{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, mac or request_id))
        if check_tries_count:
            if type(check_tries_count) == bytes:
                check_tries_count = check_tries_count.decode()
            output['verify_code_attempt']['total_requests'] = int(check_tries_count)
            if int(check_tries_count) > config.VERIFICATION_MAX_CHECK_ATTEMPTS:
                block_duration = r.ttl('{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, mac or request_id))
                output['verify_code_attempt']['block_duration'] = block_duration
                output['verify_code_attempt']['status_code'] = 700
                output['verify_code_attempt']['is_blocked'] = True
            else:
                output['verify_code_attempt']['status_code'] = 700

        return output

rightel = RightelPhoneVerifier()
