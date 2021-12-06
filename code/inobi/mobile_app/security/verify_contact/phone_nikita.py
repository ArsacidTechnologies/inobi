import time
import typing as T
import calendar

import httplib2

from ... import config

from . import (
    Contact, BaseVerifier,
    _generate_verification_code, _generate_request_id,
    getredis, error_codes,
    ContactVerificationException as BaseVerificationException
)


assert config.NIKITA_OUTPUT in ('console', )


class PhoneVerificationException(BaseVerificationException):
    pass


class RedisKey:
    REQUEST_IDS = 'app:verification:nikita:request_id'
    CODES = 'app:verification:nikita:code'
    CHECK_TRY_COUNTS = 'app:verification:nikita:check_tries'
    SEND_TRY_COUNTS = 'app:verification:nikita:send_tries'


class Api:
    BASE_URL = 'http://smspro.nikita.kg'
    SEND_SMS = '/api/message'


class Status:
    SMS_SENT_OK = 1


RequestId = str
Phone = Contact


class NikitaPhoneVerifier(BaseVerifier):

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
        if config.NIKITA_DEBUG:
            if config.NIKITA_OUTPUT == 'console':
                print(phone, repr(config.NIKITA_CODE_MESSAGE_TEMPLATE.format(code=code)))
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

        id = calendar.timegm(time.gmtime())
        data = """<?xml version=\"1.0\" encoding=\"UTF-8\"?> 
            <message> 
                <login>%(user)s</login> 
                <pwd>%(password)s</pwd> 
                <sender>Tez Taxi</sender> 
                <id>%(id)s</id> 
                <text>%(code)s</text> 
                <phones> 
                    <phone>%(phone)s</phone>
                </phones>
            </message>"""

        values = {
            "user": "" + str(config.NIKITA_USERNAME),
            "password": str(config.NIKITA_PASSWORD),
            "phone": str(phone),
            "id": str(calendar.timegm(time.gmtime())),
            "code": str(config.NIKITA_CODE_MESSAGE_TEMPLATE.format(code=code))
        }
        data = data % values

        http = httplib2.Http()
        response, content = http.request(
            Api.BASE_URL + Api.SEND_SMS,
            'POST',
            headers={'Content-Type': 'application/xml'},
            body=data.encode('utf-8')
        )

        status = response['status']
        if status == Status.SMS_SENT_OK:
            return request_id
        raise PhoneVerificationException("Send failed",
                                         error_codes.PHONE_VERIFICATION_ERROR)

    def check(self, contact, code, mac=None, cleanup_on_success=True, check=False) -> Contact:
        phone = contact
        r = getredis()
        # FIXME: IF REQUEST_ID DOESN'T EXIST, USER CAN CHECK MULTIPLE TIMES.
        request_id = mac or self._get_request_id(phone, r)
        if request_id is None:
            raise PhoneVerificationException('REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS',
                                             error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS)
        if config.NIKITA_DEBUG:
            if config.NIKITA_OUTPUT == 'console':
                print(phone, repr(config.NIKITA_CODE_MESSAGE_TEMPLATE.format(code=code)))
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


nikita = NikitaPhoneVerifier()
