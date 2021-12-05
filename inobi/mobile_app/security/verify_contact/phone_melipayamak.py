
import typing as T

import requests

from ... import config

_AUTH_PARAMS = dict(zip('username password'.split(), config.MELIPAYAMAK_CREDENTIALS))

from . import (
    Contact, BaseVerifier,
    _generate_verification_code, _generate_request_id,
    getredis, error_codes,
    ContactVerificationException as BaseVerificationException
)


assert config.MELIPAYAMAK_OUTPUT in ('console', )


class PhoneVerificationException(BaseVerificationException):
    pass


class RedisKey:
    REQUEST_IDS = 'app:verification:melipayamak:request_id'
    CODES = 'app:verification:melipayamak:code'
    CHECK_TRY_COUNTS = 'app:verification:melipayamak:check_tries'
    SEND_TRY_COUNTS = 'app:verification:melipayamak:send_tries'


class Api:
    BASE_URL = 'https://rest.payamak-panel.com'
    SEND_SMS = '/api/SendSMS/SendSMS'
    USER_NUMBERS = '/api/SendSMS/GetUserNumbers'
    GET_DELIVERY = '/api/SendSMS/GetDeliveries2'


class Status:
    SMS_SENT_OK = 1


RequestId = str
Phone = Contact


class MelipayamakPhoneVerifier(BaseVerifier):

    __numbers = None

    def _refetch_number(self) -> str:
        self.__numbers = None
        return self._number

    @property
    def _number(self) -> str:
        if config.MELIPAYAMAK_NUMBER:
            return config.MELIPAYAMAK_NUMBER
        if self.__numbers:
            return self.__numbers[0]
        r = requests.post(Api.BASE_URL+Api.USER_NUMBERS, _AUTH_PARAMS)
        # json is like {"MyBase":{"Value":"Ok","RetStatus":1,"StrRetStatus":"Ok"},"Data":[{"Number":"500010604671"}]}
        self.__numbers = [n['Number'] for n in r.json()['Data']]
        return self.__numbers[0]

    def _get_request_id(self, phone, r=None, _rk=RedisKey.REQUEST_IDS) -> T.Optional[RequestId]:
        if not r:
            r = getredis()
        rid = r.get('{}:{}'.format(_rk, phone))
        if type(rid) == bytes:
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
        """Sends verification code to given phone number"""
        phone = contact
        r = getredis()
        # TODO: HERE MUST PREVENT A PHONE FROM SENDING CODE 2 TIME WITH NEW REQUEST_ID
        request_id = mac or (self._get_request_id(phone, r) or _generate_request_id())
        code = _generate_verification_code()
        if config.MELIPAYAMAK_DEBUG:
            if config.MELIPAYAMAK_OUTPUT == 'console':
                print(phone, repr(config.MELIPAYAMAK_CODE_MESSAGE_TEMPLATE.format(code=code)))
            else:
                pass
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


        data = {
            'to': phone,
            'from': self._number,
            'text': config.MELIPAYAMAK_CODE_MESSAGE_TEMPLATE.format(code=code),
            **_AUTH_PARAMS,
        }

        resp = requests.post(Api.BASE_URL + Api.SEND_SMS, data)
        j = resp.json()

        status = j['RetStatus']
        if status == Status.SMS_SENT_OK:
            return request_id
        raise PhoneVerificationException(j['errorReason'],
                                         error_codes.PHONE_VERIFICATION_ERROR)

    def check(self, contact, code, mac=None, cleanup_on_success=True, check=False) -> Contact:
        phone = contact
        r = getredis()
        # FIXME: IF REQUEST_ID DOESN'T EXIST, USER CAN CHECK MULTIPLE TIMES.
        request_id = mac or self._get_request_id(phone, r)
        if request_id is None:
            raise PhoneVerificationException('REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS',
                                             error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS)
        if config.MELIPAYAMAK_DEBUG:
            if config.MELIPAYAMAK_OUTPUT == 'console':
                print(phone, repr(config.MELIPAYAMAK_CODE_MESSAGE_TEMPLATE.format(code=code)))
            else:
                pass
            return request_id

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


melipayamak = MelipayamakPhoneVerifier()
