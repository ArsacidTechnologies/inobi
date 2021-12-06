
import datetime
import typing as T
import uuid
from functools import partial

from flask import render_template as _render_template, request
from flask_cors import cross_origin

from inobi.security import secured, scope
from inobi.utils import http_ok, http_err
from inobi.utils.converter import Modifier, converted
from .public import media
from .. import route, error_codes, config
from ..db.public_v2 import get_random_ad, register_view, Ad
from ..utils.validators import valid_mac_address, get_key_from_header

render_template = partial(_render_template, media_view_name=media.__name__)


tag = "@{}:".format(__name__)


@route('/v1/ads/random', methods='GET'.split())
@cross_origin()
@converted(description_for__platform='One of {}'.format(Ad.Platform.POSSIBLE_PLATFORM_DESCRIPTORS))
def get_ad_for_app(lat: float = None, lng: float = None,
                   platform: Ad.Platform.platform_fromstr = Ad.Platform.ALL,
                   render: Modifier.BOOL = False, test: Modifier.BOOL = False,
                   display_type: Modifier.COLLECTION(*Ad.DISPLAY_TYPES) = Ad.DISPLAY_TYPE_FULLSCREEN,
                   only_unvisited: bool = False):

    client_mac = None
    if only_unvisited:
        try:
            client_mac = get_key_from_header(request, 'device_id', valid_mac_address)
        except ValueError as e:
            return http_err(message="Client mac is not valid", error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)
        if (client_mac is None) and (client_mac == "") and (not isinstance(client_mac, str)):
            return http_err(message="Client mac is not valid", error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    res = get_random_ad(lat=lat, lng=lng, platform=platform, test=test,
                        display_type=display_type, only_unvisited=only_unvisited,
                        client_mac=client_mac)
    if not res:
        return http_err('No ads enabled', 404)

    ad, view_token = res

    ad = ad.asdict()

    if render:
        return render_template('advertisement/ad.html', ad=ad)

    # view_token is only used by android, to register views by `/v1/views/` API
    # when box is working with this response, no need to view_token
    # box register views as chronicles by `/v1/register/chronicles/<ad_id>` API
    return http_ok(view_token=view_token, ad=ad, skip_timer=config.AD_SKIP_TIMER)


def verify_view_token(token: str, base64=False) -> T.Optional[dict]:
    try:
        uuid.UUID(token)
    except ValueError:
        return

    return dict(scopes=[scope.Advertisement.AD_VIEWER], token=token)


@route('/v1/views/', methods='POST'.split())
@cross_origin()
@secured([scope.Advertisement.ADMIN, scope.Advertisement.AD_VIEWER],
         token_key='view_token', verify=verify_view_token)
@converted
def register_ad_view_v1(view_token,
                        device_id: str,
                        is_redirected: bool,
                        provider_id: str = None,
                        events: Modifier.ARRAY_OF(dict) = None,
                        device_description: str = None,
                        platform: Ad.Platform.platform_fromstr = Ad.Platform.ALL,
                        lat: float = None,
                        lng: float = None,
                        view_time: datetime.datetime.fromtimestamp = None,
                        test: Modifier.BOOL = False,
                        ):

    view = register_view(view_token,
                         viewer_device_id=device_id,
                         is_redirected=is_redirected,
                         events=events,
                         viewer_device_description=device_description,
                         platform=platform,
                         provider_id=provider_id,
                         lat=lat,
                         lng=lng,
                         view_time=view_time,
                         test=test,
                         )
    if not view:
        return http_err('View not Found', 404)

    return http_ok(view=view.asdict())
