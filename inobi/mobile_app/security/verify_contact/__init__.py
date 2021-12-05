
import functools as FT
import typing as T

from inobi.config import RedisSegments
from inobi.redis import getredis as _getredis, Redis

from ... import error_codes
from ... import config

getredis = FT.partial(_getredis, db=RedisSegments.APPLICATION)      # type: T.Callable[[], Redis]

from inobi.exceptions import BaseInobiException

from random import choice
from string import ascii_letters, digits


def _generate_sequence(chars: str, length: int):
    return ''.join(choice(chars) for _ in range(length))


_generate_request_id = FT.partial(_generate_sequence, chars=ascii_letters+digits, length=32)
_generate_verification_code = FT.partial(_generate_sequence, chars=digits, length=4)


class ContactVerificationException(BaseInobiException):
    pass


Contact = str
RequestId = str


class BaseVerifier:

    def send(self, contact, *args, **kwargs) -> RequestId:
        pass

    def check(self, contact, code, *args, **kwargs) -> Contact:
        pass

    def _clean(self, contact, *args, **kwargs):
        pass

    def status(self, value, status_type, request_id=None):
        pass


# import child module stuff after declaring independent code
from .phone_melipayamak import melipayamak
from .phone_shahkar import Shahkar
from .phone_verifire import verifire
from .phone_nikita import nikita
from .phone_rightel import rightel
from .email_smtp import email_smtp

assert config.PHONE_VERIFIER in ('melipayamak', 'verifire', 'rightel', 'nikita')
assert config.EMAIL_VERIFIER in ('email_smtp', )

phone_verifier = globals()[config.PHONE_VERIFIER]      # type: BaseVerifier
shahkar_verifier = Shahkar("", "")
email_verifier = globals()[config.EMAIL_VERIFIER]      # type: BaseVerifier


############################
## BACKWARD COMPATIBILITY ##
############################
# deprecated. use verifier instances

from ...db import contact_verification as db
from .phone_verifire import VerificationMethod, Language

send_phone_verification = phone_verifier.send
clean_phone_verification = phone_verifier._clean
get_phone_status = phone_verifier.status


def check_phone(*args, **kwargs) -> db.VerifiedContact:
    phone = phone_verifier.check(*args, **kwargs)
    return db.insert_verified_contact(phone, 'phone')


ads_send_phone = phone_verifier.send

def ads_check_phone(*args, mac=None, **kwargs) -> RequestId:
    return phone_verifier.check(*args, mac=mac, **kwargs)


send_email_verification = email_verifier.send
clean_email_verification = email_verifier._clean
get_email_status = email_verifier.status


def check_email(*args, **kwargs) -> db.VerifiedContact:
    email = email_verifier.check(*args, **kwargs)
    return db.insert_verified_contact(email, 'email')


register_shahkar = shahkar_verifier.register
check_shahkar = shahkar_verifier.check
close_shahkar = shahkar_verifier.close

error_codes = error_codes
VERIFICATION_REQUEST_TIMEOUT = config.VERIFICATION_REQUEST_TIMEOUT