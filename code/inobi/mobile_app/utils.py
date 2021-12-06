
from os.path import join, isfile

from .config import (
    APP_DB_DIRECTORY,
    DB_NAME_UNFORMATTED,
    DB_VERSION_INDEX,
    DB_ZIP_FILENAME_UNFORMATTED,
    SMTP_LOGIN,
    SMTP_SERVER
)


def formatted_zip_filename(version: int):
    return join(APP_DB_DIRECTORY, DB_ZIP_FILENAME_UNFORMATTED.format(version))


def valid_iranian_national_id(value) -> str:
    if not isinstance(value, str):
        raise ValueError()
    v = value.strip()
    if not len(v) == 10 or not v.isdigit():
        raise ValueError('national_id must 10 digits length string')
    control = int(v[-1])
    s = sum(int(d) * (10-i) for i, d in enumerate(v[:9])) % 11
    if (2 > s == control) or (s >= 2 and control+s == 11):
        return v
    raise ValueError('national_id invalid')


def app_data_index():
    index_filename = _app_index_filename()
    if not isfile(index_filename):
        return None
    with open(index_filename) as f:
        from json import loads
        return loads(f.read())


def dump_app_data_index(index):
    from json import dumps
    index_filename = _app_index_filename()
    with open(index_filename, 'w') as f:
        print(dumps(index, indent=2), file=f, flush=True)


def _app_index_filename():
    return join(APP_DB_DIRECTORY, DB_VERSION_INDEX)


def _app_db_filename(version):
    return join(APP_DB_DIRECTORY, DB_NAME_UNFORMATTED.format(version))


from inobi.utils import send_email as _send_email
import functools as FT


send_email = FT.partial(_send_email,
                        smtp=SMTP_SERVER,
                        username=SMTP_LOGIN[0],
                        password=SMTP_LOGIN[1])
