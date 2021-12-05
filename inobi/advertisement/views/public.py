import re
import time
from flask import render_template, request, abort, send_from_directory, redirect, url_for
from flask_cors import cross_origin

from inobi.security import secured, scope
from inobi.utils import http_err, http_ok, getargs, HTTP_ERR_DATA, device_description_from_user_agent, HTTP_ERR
from inobi.utils.converter import converted, Modifier

from .. import route, error_codes, bp, config
from ..security import check_box_token, Scope
from ..exceptions import InobiException

from ..utils import debug_exception, get_directory, url_for_with_root

from ..db import public as db, devices, chronicles_v2
from ..db.classes import Ad
from ..utils.validators import valid_mac_address, get_key_from_header

tag = "@{}:".format(__name__)


@route('/ad')
@cross_origin()
@secured('advertisement_admin box', verify=check_box_token)
@converted(description_for__platform='One of {}'.format(db.Ad.Platform.POSSIBLE_PLATFORM_DESCRIPTORS))
def get_ad(scopes: list, token_data: dict, lat: float = None, lng: float = None,
           platform: Ad.Platform.platform_fromstr = Ad.Platform.WIFI,
           render: Modifier.BOOL = False, test: Modifier.BOOL = False):

    if 'box' in scopes:
        lat = token_data.get('lat') or lat
        lng = token_data.get('lng') or lng

        try:
            p = Ad.Platform.platform_fromstr(token_data.get('platform'))
        except:
            pass
        else:
            platform = p

    try:
        ad = db.get_random_ad(lat=lat, lng=lng, platform=platform, box_mac=token_data['box_mac'], test=test)

        if ad is None:
            return http_err("No ads enabled", status=400, error_code=1040)

    except InobiException as e:
        return http_err(message=str(e), status=400)
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        return http_err()
    else:
        ad = ad._asdict()

        if not render:
            return http_ok(ad=ad, skip_timer=config.AD_SKIP_TIMER)
        else:
            return render_template('advertisement/ad.html', ad=ad, media_view_name=media.__name__)


@route('/v1/register_view/<ad_id>')
@cross_origin()
@secured(Scope.BOX, verify=check_box_token, token_data_key='jwt_dict')
def register_view(ad_id, jwt_dict):

    view = db.AdView.construct(
        box_mac=jwt_dict.get('box_mac'),
        ad_id=ad_id,
        lat=jwt_dict.get('lat'),
        lng=jwt_dict.get('lng'),
        client_mac=jwt_dict.get('client_mac'),
        user_agent=jwt_dict.get('user_agent')
    )

    if view is None:
        return http_err('View can not be registered', 400)

    try:
        registered_view = db.register_view(view)
        return http_ok(view=registered_view._asdict())
    except InobiException as e:
        debug_exception(tag, e, to_file=True)
        return http_err(message=str(e), status=400)
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        return http_err()


from ..utils.stats import parse_device_from_ua


@route('/v1/register/chronicles')
@cross_origin()
@converted
def register_chronicles(ad_id: str = "", lat: float = None, lng: float = None,
                        events: str = None, redirected: bool = None, test: bool = False):
    if not re.match(r'^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$', ad_id, re.IGNORECASE):
        return HTTP_ERR_DATA(message="`ad_id` parameter is not present.",
                             error_code=error_codes.AD_ID_NOT_PRESENT, status=400)

    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, 'Mac address is not valid')  # raise
    except ValueError as e:
        return HTTP_ERR(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)
    user_agent = get_key_from_header(request, 'User-Agent', device_description_from_user_agent)
    if isinstance(user_agent, str):
        user_agent = user_agent.strip()

    try:
        box_mac = get_key_from_header(request, 'box_mac', valid_mac_address, 'Box MAC is not valid') # raise
    except ValueError as e:
        return HTTP_ERR(message=str(e), error_code=error_codes.BOX_MAC_NOT_VALID, status=400)


    try:
        chronicle = chronicles_v2.register(box_mac, ad_id, lat=lat, lng=lng,
                                           redirected=redirected, client_mac=client_mac,
                                           client_device=user_agent, events=events, test=test)
    except ValueError as e:
        return HTTP_ERR(message=str(e), error_code=error_codes.BOX_MAC_NOT_VALID, status=400)


    return http_ok(chronicle=chronicle.asdict())


@route('/v1/uploads/<filename>')
@cross_origin()
def uploaded_file(filename):
    return redirect(url_for('.'+media.__name__, filename=filename))


@route('/media/<filename>')
@cross_origin()
def media(filename):
    return send_from_directory(get_directory('media'), filename,
                               as_attachment=True)
