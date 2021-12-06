import re
import typing

from inobi.advertisement.utils import Gender
from inobi.utils import device_description_from_user_agent


def valid_iranian_national_id(value) -> str:
    assert isinstance(value, str)
    v = value.strip()
    if len(list(set(v))) in (0, 1):
        raise ValueError('national_id invalid')
    if not len(v) == 10 or not v.isdigit():
        raise ValueError('national_id must 10 digits length string')
    control = int(v[-1])
    s = sum(int(d) * (10-i) for i, d in enumerate(v[:9])) % 11
    if (2 > s == control) or (s >= 2 and control+s == 11):
        return v
    raise ValueError('national_id invalid')


def valid_mac_address(value) -> str:
    assert isinstance(value, str)
    v = value.strip()
    assert len(v) == 17

    if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', value):
        raise ValueError("IP is not valid.")
    if value[-1] == ':' or value[-1] == '-':
        return value[:-1]
    return value


def valid_gender(value) -> typing.Optional[int]:
    if value is None:
        return
    try:
        value = int(value)
    except Exception as e:
        raise ValueError('Gender must be 969 (Male) or 696 (Female)')

    if value not in (Gender.MALE, Gender.FEMALE):
        raise ValueError("Gender is not valid, must be 1 or 2")

    return value


def get_key_from_header(request, key, validator=None, error_message="Data not valid"):
    value = request.headers.get(key)

    if validator:
        try:
            value = validator(value)
        except (AssertionError, ValueError):
            raise ValueError(error_message)
    return value