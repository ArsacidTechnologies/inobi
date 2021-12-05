
import smtplib

from ... import config

from ...utils import send_email as _send_email

from . import (
    Contact, BaseVerifier,
    _generate_request_id, _generate_verification_code,
    getredis, error_codes, T,
    ContactVerificationException as BaseVerificationException,
)


class EmailVerificationException(BaseVerificationException):
    pass


class RedisKey:
    REQUEST_IDS = 'app:verification:email:request_id'
    CODES = 'app:verification:email:code'
    CHECK_TRY_COUNTS = 'app:verification:email:check_tries'
    SEND_TRY_COUNTS = 'app:verification:email:send_tries'


RequestId = str
Email = Contact


class EmailSMTPVerification(BaseVerifier):
    def _get_request_id(self, email, r=None, _rk=RedisKey.REQUEST_IDS) -> T.Optional[RequestId]:
        if not r:
            r = getredis()
        rid = r.get('{}:{}'.format(_rk, email))
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
        email = contact
        """Sends verification code to given email"""
        r = getredis()
        # TODO: HERE MUST PREVENT A email FROM SENDING CODE 2 TIME WITH NEW REQUEST_ID
        request_id = mac or (self._get_request_id(email, r) or _generate_request_id())
        code = _generate_verification_code()

        # TODO: set cache for these debugs in all providers
        if config.SMTP_DEBUG:
            if config.SMTP_OUTPUT == 'console':
                print(request_id, code)
            return request_id

        send_try_counts_key = '{}:{}'.format(RedisKey.SEND_TRY_COUNTS, mac or request_id)
        send_tries_count = r.incr(send_try_counts_key, 1)
        r.expire(send_try_counts_key, config.VERIFICATION_REQUEST_TIMEOUT)
        if type(send_tries_count) == bytes:
            send_tries_count = send_tries_count.decode()
        if int(send_tries_count) > config.VERIFICATION_MAX_SEND_ATTEMPTS:
            raise EmailVerificationException('Too Many Send Attempts',
                                             error_codes.TOO_MANY_SEND_ATTEMPTS)
        r.setex('{}:{}'.format(RedisKey.REQUEST_IDS, email), request_id, config.VERIFICATION_REQUEST_TIMEOUT)
        r.setex('{}:{}'.format(RedisKey.CODES, request_id), code, config.VERIFICATION_REQUEST_TIMEOUT)

        try:
            _send_email(from_address='Inobi',
                        to_address=email,
                        subject='Email verification',
                        message='Your verification code: {}'.format(code))
        except smtplib.SMTPException:
            raise EmailVerificationException('Sending email failed',
                                             error_codes.SMTP_VERIFICATION_ERROR)

        return request_id

    def check(self, contact, code, mac=None, cleanup_on_success=True, check=False) -> Contact:
        email = contact
        r = getredis()
        # FIXME: IF REQUEST_ID DOESN'T EXIST, USER CAN CHECK MULTIPLE TIMES.
        request_id = mac or self._get_request_id(email, r)
        if request_id is None:
            raise EmailVerificationException('REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS',
                                             error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS)
        if config.SMTP_DEBUG:
            if config.SMTP_OUTPUT == 'console':
                print(email, code)
            return email

        check_tries_count = '{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, mac or request_id)
        r.incr(check_tries_count, 1)
        r.expire(check_tries_count, config.VERIFICATION_REQUEST_TIMEOUT)
        tries_count = r.get(check_tries_count)
        if type(tries_count) == bytes:
            tries_count = tries_count.decode()
        tries_count = int(tries_count)
        if int(tries_count) > config.VERIFICATION_MAX_CHECK_ATTEMPTS:
            raise EmailVerificationException('Too Many Check Attempts',
                                             error_codes.TOO_MANY_CHECK_ATTEMPTS)

        redis_email_code = self._get_code(mac or request_id, r)
        if redis_email_code == code:
            if cleanup_on_success:
                self._clean(email, r)
            return email
        raise EmailVerificationException('Invalid code',
                                         error_codes.INVALID_CODE)

    def _clean(self, contact, _r=None, **kwargs):
        email = contact
        if _r is None:
            _r = getredis()
        request_id = _r.hget(RedisKey.REQUEST_IDS, email)
        _r.delete('{}:{}'.format(RedisKey.SEND_TRY_COUNTS, request_id))
        _r.delete('{}:{}'.format(RedisKey.CHECK_TRY_COUNTS, request_id))
        _r.delete('{}:{}'.format(RedisKey.CODES, request_id))
        _r.delete('{}:{}'.format(RedisKey.REQUEST_IDS, email))

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


email_smtp = EmailSMTPVerification()
