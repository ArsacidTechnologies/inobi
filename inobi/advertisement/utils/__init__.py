
import functools as FT
import os
from datetime import datetime, date
from os.path import isfile, join
from time import strftime

from flask import url_for as _url_for

from ..config import DIRECTORIES
from ..config import IMAGE_EXTENSIONS, ALLOWED_EXTENSIONS

tag = "@Utils:"


url_for_with_root = FT.partial(_url_for, _external=True)


def allowed_file(filename):
    return os.path.splitext(filename)[-1][1:].lower() in ALLOWED_EXTENSIONS


def allowed_thumbnail(filename):
    return os.path.splitext(filename)[-1][1:].lower() in IMAGE_EXTENSIONS


def is_valid_uuid(uuid):
    from uuid import UUID
    try:
        uuid = UUID(uuid)
    except:
        return False
    else:
        return str(uuid)


def get_directory(key):
    return DIRECTORIES.get(key)


def _movefile(filename, fromdir, todir):
    from shutil import move
    from os.path import join

    try:
        move(join(fromdir, filename), join(todir, filename))
    except Exception as e:
        debug_exception(tag, e)
        return False
    return True


def _movesource(filename, prep: bool):
    fromdir, todir = get_directory('temp'), get_directory('media')
    fromthumb, tothumb = get_directory('thumbnail_temp'), get_directory('thumbnail_media')

    if not prep:
        fromdir, todir = todir, fromdir
        fromthumb, tothumb = tothumb, fromthumb

    _movefile(thumbnail_name(filename), fromthumb, tothumb)
    return _movefile(filename, fromdir, todir)


def prepare_source(filename):
    return _movesource(filename, prep=True)


def remove_source(filename):
    return _movesource(filename, prep=False)


def media_exists(filename, in_temp=False):
    if not isinstance(filename, str):
        return False
    directory = get_directory('temp' if in_temp else 'media')
    return isfile(join(directory, filename))


def split_filename(filename):
    dot_i = filename.rfind('.')
    if dot_i in (-1, 0):
        return filename, ''
    return filename[:dot_i], filename[dot_i + 1:]


def thumbnail_name(filename):
    return split_filename(filename)[0] + '.thumb'


def get_files_list(dir_key):
    path = get_directory(dir_key)
    if not path:
        return None

    from os import listdir
    return [node for node in listdir(path) if isfile(join(path, node))]


from ..exceptions import InobiException, InobiAdsException, BaseInobiException


def debug_exception(tag, e, to_file=True):
    if not isinstance(e, (InobiAdsException, InobiException, BaseInobiException)):
        raise e
    if to_file:
        log_to_file(tag, e, e.__class__)
    print(tag, e, e.__class__)


def log_to_file(*args):
    file = open('advertisement.log', 'a')
    print(strftime('%X %x'), *args, file=file, flush=True)
    file.close()


def purge_uuid(uuid):
    if not uuid:
        return None
    if not isinstance(uuid, str):
        uuid = str(uuid)
    uuid = uuid.lower()
    quote = '\''
    quotes_count = uuid.count(quote)
    if quotes_count == 2:
        return uuid[uuid.index(quote) + 1:uuid.rindex(quote)]
    return uuid


def humanize_time(ts):
    return str(datetime.fromtimestamp(ts))


def get_today_epochs() -> tuple:
    td = date.today()
    td_min_time = datetime.min.time()
    td_max_time = datetime.max.time()
    td_min, td_max = datetime.combine(td, td_min_time), datetime.combine(td, td_max_time)
    return get_epoch(td_min), get_epoch(td_max)


def get_epoch(dt: datetime):
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000.0


class Gender:
    MALE = 1
    FEMALE = 2
