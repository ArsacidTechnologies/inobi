
from flask import send_from_directory

from inobi.utils.converter import converted

from ... import route

from ...db.box import (
    get_box_internet,
    get_box_update_version,
    log_box_update
    )
from ...cache import getcached, cache, CKeys
from ...utils import debug_exception, get_directory

from ...config import BOX_UPDATE_FILE, ALLOW_INTERNET_OPTIONS


tag = "@{}:".format(__name__)


@route('/box/version', methods=['POST', 'GET'])
def box_update_version():
    box_version = getcached(CKeys.BOX_VERSION)
    if not box_version:
        try:
            box_version = get_box_update_version()
            cache(CKeys.BOX_VERSION, box_version)
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            return '-1'

    return str(box_version)


@route('/box/update', methods=['POST', 'GET'])
@converted
def box_update(id: str = None, prev_ver: int = None, lat: float = None, lon: float = None, lng: float = None):

    lng = lng or lon

    version = getcached(CKeys.BOX_VERSION) or get_box_update_version()

    try:
        _box_update = log_box_update(id, version, prev_version=prev_ver, lat=lat, lng=lng)
        # print(_box_update)
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        pass

    return send_from_directory(get_directory('box_updates'), BOX_UPDATE_FILE), 200


@route('/box/internet', methods=['POST', 'GET'])
def box_internet():
    allow = getcached(CKeys.INTERNET)
    if not allow:
        try:
            allow = get_box_internet()
            cache(CKeys.INTERNET, allow)
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            allow = None

    return '1' if (allow in ALLOW_INTERNET_OPTIONS) else '0'

