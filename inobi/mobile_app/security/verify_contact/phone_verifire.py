
import requests
from requests.auth import HTTPBasicAuth

from inobi.utils.converter import Modifier
from ... import config

from ...config import VERIFIRE_CREDENTIALS, VERIFIRE_FROM

_AUTH = HTTPBasicAuth(*VERIFIRE_CREDENTIALS)


from . import (
    Contact, RequestId, BaseVerifier,
    getredis, error_codes, T,
    ContactVerificationException as BaseVerificationException,
)


class PhoneVerificationException(BaseVerificationException):
    pass


class RedisKey:
    CHECK_TRY_COUNTS = 'app:verification:verifire:check_tries'
    SEND_TRY_COUNTS = 'app:verification:verifire:send_tries'
    REQUEST_IDS = 'app:verification:verifire:request_id'


class Api:
    BASE_URL = 'https://api.boomware.com'
    VERIFY = '/v1/verify'
    SMS = '/v1/sms'

    VERIFY_CHECK = VERIFY + '/check'
    VERIFY_INFO = VERIFY + '/info'


class VerificationMethod:
    CALL = 'call'
    SMS = 'sms'
    VOICE = 'voice'

    check = Modifier.COLLECTION(CALL, SMS, VOICE)


class Language:
    EN = 'en'
    RU = 'ru'
    FA = 'fa'

    check = Modifier.COLLECTION(EN, RU, FA)


Phone = Contact


class VerifirePhoneVerifier(BaseVerifier):

    def _save(self, phone, request_id, r=None) -> RequestId:
        if not r:
            r = getredis()

        r.setex('{}:{}'.format(RedisKey.REQUEST_IDS, phone), request_id, config.VERIFICATION_REQUEST_TIMEOUT)

        return request_id

    def _get_request_id(self, phone, r=None, _rk=RedisKey.REQUEST_IDS) -> T.Optional[RequestId]:
        if not r:
            r = getredis()
        rid = r.get('{}:{}'.format(_rk, phone))
        if rid:
            return rid.decode()
        return rid

    def send(self, contact, method=VerificationMethod.SMS, language=Language.EN,
             code_length=4, client_ip=None, mac=None) -> RequestId:

        phone = contact
        """Sends verification code to given phone number"""
        r = getredis()
        # TODO: HERE MUST PREVENT A PHONE FROM SENDING CODE 2 TIME WITH NEW REQUEST_ID
        request_id = mac or self._get_request_id(phone, r)
        if config.VERIFIRE_DEBUG:
            if config.VERIFIRE_OUTPUT == 'console':
                print(phone, repr(request_id))
            return request_id

        send_try_counts_key = '{}:{}'.format(RedisKey.SEND_TRY_COUNTS, mac or request_id)
        send_tries_count = r.incr(send_try_counts_key, 1)
        r.expire(send_try_counts_key, config.VERIFICATION_REQUEST_TIMEOUT)
        if type(send_tries_count) == bytes:
            send_tries_count = send_tries_count.decode()
        if int(send_tries_count) > config.VERIFICATION_MAX_SEND_ATTEMPTS:
            raise PhoneVerificationException('Too Many Send Attempts',
                                             error_codes.TOO_MANY_SEND_ATTEMPTS)

        data = dict(
            number=phone,
            method=method,
            language=language,
            codeLength=code_length,
            ip=client_ip,
        )
        if VERIFIRE_FROM:
            data['from'] = VERIFIRE_FROM

        resp = requests.post(Api.BASE_URL + Api.VERIFY, data=data, auth=_AUTH)
        j = resp.json()

        try:
            request_id = j['requestId']
        except KeyError:
            raise PhoneVerificationException(j['errorReason'],
                                             error_codes.PHONE_VERIFICATION_ERROR)

        r.setex('{}:{}'.format(RedisKey.REQUEST_IDS, phone), request_id, config.VERIFICATION_REQUEST_TIMEOUT)
        return request_id

    def check(self, contact, code, cleanup_on_success=True, check=False, mac=None) -> Phone:
        phone = contact
        r = getredis()
        # FIXME: IF REQUEST_ID DOESN'T EXIST, USER CAN CHECK MULTIPLE TIMES.
        request_id = mac or self._get_request_id(phone, r)
        if request_id is None:
            raise PhoneVerificationException('REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS',
                                             error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS)
        if config.VERIFIRE_DEBUG:
            if config.VERIFIRE_OUTPUT == 'console':
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

        data = dict(
            requestId=request_id,
            code=code
        )

        resp = requests.post(Api.BASE_URL + Api.VERIFY_CHECK, data=data, auth=_AUTH)
        j = resp.json()

        try:
            number = j['number']
            method = j['method']
            verified_at = j['verifiedAt']
        except KeyError:
            raise PhoneVerificationException('{} (code {})'.format(j['errorReason'], j['errorCode']),
                                             error_codes.PHONE_VERIFICATION_ERROR)
        else:
            if cleanup_on_success:
                self._clean(phone, r)
            return phone

    def _clean(self, phone, _r=None, **kwargs):
        if _r is None:
            _r = getredis()
        request_id = _r.hget(RedisKey.REQUEST_IDS, phone)
        _r.delete('{}:{}'.format(RedisKey.SEND_TRY_COUNTS, request_id))
        _r.delete('{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, request_id))
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


verifire = VerifirePhoneVerifier()
