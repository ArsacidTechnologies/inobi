
from flask import send_from_directory

from inobi.utils.converter import converted

from .. import bp

from .. import db

from inobi.advertisement.cache import getcached, cache
from inobi.advertisement.utils import debug_exception, get_directory

from .. import config

CKeys = config.CKeys


tag = "@{}:".format(__name__)


route = bp.route


@route('/version', methods=['POST', 'GET'])
def box_update_version():
    key = CKeys.VERSION
    box_version = getcached(key)
    if not box_version:
        try:
            box_version = db.get_box_setting(key)
            cache(key, box_version)
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            return '-1'

    return str(box_version)


@route('/update', methods=['POST', 'GET'])
@converted
def box_update(id: str = None, previous_version: int = None,
               lat: float = None, lon: float = None, lng: float = None,
               user: str = None, region: str = None,
               network_interface: str = None
               ):
    lng = lng or lon

    key = CKeys.VERSION
    version = getcached(key) or db.get_box_setting(key)

    if id:
        _box_update = db.log_box_update(id, version, prev_version=previous_version, lat=lat, lng=lng)

    return send_from_directory(config.BOX_UPDATES_DIRECTORY, config.BOX_UPDATE_FILE), 200


@route('/internet', methods=['POST', 'GET'])
def box_internet():
    key = CKeys.INTERNET
    allow = getcached(key)
    if not allow:
        try:
            allow = db.get_box_setting(key)
            cache(key, allow)
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            allow = None

    return '1' if (allow in config.ALLOW_INTERNET_OPTIONS) else '0'

