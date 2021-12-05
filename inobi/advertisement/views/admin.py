
import time

import typing as T

from flask import request, render_template, url_for, redirect
from flask_cors import cross_origin

from inobi.security import secured, sign, scope
from inobi.utils import http_ok, http_err, getargs

from .. import route
from ..exceptions import InobiException

from ..utils import debug_exception

from ..db import admin as db, Ad
from ..db.chronicles import get_chronicles

from ..security import Scope, check_admin_key

from inobi.utils.converter import converted, Modifier


tag = '@Views.Admin:'


@route('/admin')
@cross_origin()
def advertisement_index():
    return redirect(url_for('static', filename='advertisement/index.html'))


@route('/v1/admin/list/<table>')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def admin_get_list(table: str, date_from: float = None, date_to: float = None, ad_id: T.Union[str, list] = None, limit: T.Union[str, int] = 'none'):

    table = table.lower()

    # REMOVE THIS WHEN get_list implemented
    if table not in ('chronicles', ):
        return http_err('Not Found', 404)

    if ad_id and ',' in ad_id:
        ad_id = ad_id.split(',')

    if date_from is None:
        date_from = time.time()

    params = dict(
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        ad_id=ad_id
    )

    try:
        chronicles, (date_from, date_to) = get_chronicles(**params)
    except InobiException as e:
        return http_err(str(e), 400)
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        return http_err()
    else:
        return http_ok({
            table: chronicles,
            "_count": len(chronicles),
            "date_from": date_from,
            "date_to": date_to
        })


@route('/v1/admin/create')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted(description_for__type='One of {}'.format(set(Ad.TYPES)))
def admin_create(duration: float, redirect_url: str, source: str, type: Modifier.COLLECTION(*Ad.TYPES),
                 title: str, external_source: Modifier.BOOL = False,
                 description: str = None, lat: float = None, lng: float = None,
                 views_max: int = None, expiration_date: float = None, enabled: Modifier.BOOL = True,
                 weight: int = 1, platform: Ad.Platform.platform_fromstr = Ad.Platform.ALL,
                 radius: Ad.Radius.check_radius = Ad.Radius.DEFAULT,
                 transport_filters: Modifier.ARRAY_OF(str, int) = None,
                 cities: Modifier.ARRAY_OF(int) = None, time_from: Ad.time_modifier = None,
                 time_to: Ad.time_modifier = None,
                 start_date: float = None,
                 ):
    # kostyl: on some captive clients redirect_url still concatenated with 'http://' prefix
    # so redirect_urls on client looks like 'http://http://inobi.mobi' which is not valid
    if redirect_url.startswith('http://') or redirect_url.startswith('https://'):
        redirect_url = redirect_url.replace('http://', '').replace('https://', '')

    try:
        ad = Ad.create(
            type=type,
            duration=duration,
            redirect_url=redirect_url,
            source=source,
            title=title,
            external_source=external_source,
            description=description,
            lat=lat,
            lng=lng,
            views_max=views_max,
            expiration_date=expiration_date,
            enabled=enabled,
            weight=weight,
            platform=platform,
            radius=radius,
            transport_filters=transport_filters,
            cities=cities,
            time_from=time_from,
            time_to=time_to,
            start_date=start_date,
        )
    except InobiException as e:
        return http_err(str(e), 400)

    try:
        created_ad = db.create_ad(ad)
    except Exception as e:
        raise e
        debug_exception(tag, e, to_file=True)
        return http_err()
    else:
        return http_ok(ad_id=created_ad.id, created_ad=created_ad._asdict())


@route('/v1/admin/update')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def admin_update(cities: Modifier.ARRAY_OF(int) = None,
                 time_from: Ad.time_modifier = None,
                 time_to: Ad.time_modifier = None):
    json = request.get_json(force=True, silent=True)

    # kostyl: on some captive clients redirect_url still concatenated with 'http://' prefix
    # so redirect_urls on client looks like 'http://http://inobi.mobi' which is not valid

    if 'redirect_url' in json:
        redirect_url = json['redirect_url']

        if redirect_url.startswith('http://') or redirect_url.startswith('https://'):
            redirect_url = redirect_url.replace('http://', '').replace('https://', '')

        json['redirect_url'] = redirect_url

    if 'city' in json:
        json['cities'] = cities
    if 'time_to' in json:
        json['time_to'] = time_to
    if 'time_from' in json:
        json['time_from'] = time_from

    if 'transport_filters' in json and json['transport_filters'] is not None:
        tf = json['transport_filters']
        if not isinstance(tf, list):
            return http_err("'transport_filters' Parameter Must Be Array Type", 400)
        if not tf:
            return http_err("'transport_filters' Parameter Should Not Be Empty", 400)
        if all(isinstance(f, str) and f.startswith('!') for f in tf):
            return http_err(
                "'transport_filters' Parameter Should Contain At Least One Including Filter",
                400,
                "Hint: use {} instead".format([*tf, 'all'])
            )
        if not isinstance(tf, list) or set(type(i) for i in tf).difference((int, str)):
            return http_err("'transport_filters' Parameter Must Be List of Integers Or Strings", 400)
        json['transport_filters'] = list(map(str, tf))
    try:
        new_ad, old_ad = db.update_ad(json)
        _id = json['id']
    except InobiException as e:
        return http_err(str(e), 400)
    except Exception as e:
        raise e
        debug_exception(tag, e, to_file=True) 
        return http_err()
    else:
        return http_ok(updated_ad=new_ad._asdict(), old_ad=old_ad._asdict(), ad_id=_id)


@route('/v1/admin/disable')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def admin_disable_ad(ad_id: str, delete: Modifier.BOOL = False):

    try:
        disabled_ad = db.disable_ad(ad_id, delete=delete)
    except InobiException as e:
        return http_err(str(e), 400)
    except Exception as e:
        debug_exception(tag, e, to_file=True) 
        return http_err()
    else:
        return http_ok(disabled_ad=disabled_ad._asdict(), deleted=delete)


@route('/v1/admin/ads')
@cross_origin()
@secured('advertisement_viewer')
@converted
def admin_get_ads_list(ad_id: str = 'all'):

    try:
        ads = db.get_ads_list(ad_id=ad_id)
    except InobiException as e:
        return http_err(str(e), 400)
    except Exception as e:
        debug_exception(tag, e, to_file=True) 
        return http_err()
    else:
        return http_ok(ads=[ad._asdict() for ad in ads])


@route('/v1/admin/random_ad', methods=('GET', ))
@cross_origin()
@secured([scope.Advertisement.INOBI, ])
@converted
def admin_get_random_ad_v1(**kwargs):

    from ..db import public as db

    ad = db.get_random_ad(**kwargs)

    return http_ok(ad=ad and ad._asdict())


# ADMIN LOGIN
@route('/v1/admin/login', methods=['GET', 'POST'])
@cross_origin()
def admin_login():
    if request.method == 'POST':
        (admin_key, ) = getargs(request, 'admin_key')
        if check_admin_key(admin_key):
            token = sign(dict(), scopes=Scope.ADS_ADMIN, expires_after=None)
            return http_ok(jwt=token)
        else:
            return http_err(message='Unauthorized', status=401)
    return '''
   <form method="post">
      <p><label>Admin key: <input type="password" name=admin_key></label>
      <p><input type=submit value=Login>
   </form>
   '''


@route('/v1/admin/check_token', methods=['GET', 'POST'])
@cross_origin()
@secured(Scope.ADS_ADMIN, token_data_key='jwt_data')
def check_token_v1(jwt_data):
    return http_ok(token_data=jwt_data)
