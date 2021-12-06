
import typing as T

from flask_cors import cross_origin

from inobi.security import secured, scope

from .. import route

from ..db.ads_v2 import Ad, create_ad, list_ads, fetch_ad, update_ad

from inobi.utils.converter import converted, Modifier

from flask import request

from ..db import ads_v2

from inobi.utils import http_ok, http_err, recursive_dictify

import uuid


@route('/v2/admin/ads/', methods='GET POST'.split())
@cross_origin()
def admin_ads_v2():

    if request.method == 'GET':
        return admin_ads_v2_get()

    if request.method == 'POST':
        return admin_ads_v2_post()


@secured(scope.Advertisement.ADMIN)
@converted
def admin_ads_v2_post(
        duration: float,
        redirect_url: str,
        source: str,
        type: Modifier.COLLECTION(*ads_v2.Ad.TYPES),
        title: str,
        external_source: Modifier.BOOL = False,
        description: str = None,
        lat: float = None, lng: float = None,
        views_max: int = None,
        expiration_date: float = None,
        enabled: Modifier.BOOL = True,
        weight: int = 1,
        platform: ads_v2.Ad.Platform.platform_fromstr = ads_v2.Ad.Platform.ALL,
        radius: ads_v2.Ad.Radius.check_radius = Ad.Radius.DEFAULT,
        transport_filters: Modifier.ARRAY_OF(str, int) = None,
        cities: Modifier.ARRAY_OF(int) = None,
        time_from: ads_v2.Ad.time_modifier = None,
        time_to: ads_v2.Ad.time_modifier = None,
        start_date: float = None,
        device_filters: Modifier.ARRAY_OF(str, int) = None,
        display_type: Modifier.COLLECTION(*Ad.DISPLAY_TYPES) = Ad.DISPLAY_TYPE_FULLSCREEN,
):

    ad = create_ad(type=type,
                   duration=duration,
                   redirect_url=redirect_url,
                   source=source,
                   title=title,
                   external_source=external_source,
                   description=description,
                   lat=lat, lng=lng,
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
                   device_filters=device_filters,
                   display_type=display_type,
                   )

    return http_ok(ad=ad.asdict())


@secured(scope.Advertisement.VIEWER)
@converted
def admin_ads_v2_get():

    return http_ok(ads=recursive_dictify(list_ads()))


@route('/v2/admin/ads/<uuid:ad_id>/', methods='GET PUT PATCH DELETE'.split())
@cross_origin()
def admin_ad_v2(ad_id: uuid.UUID):

    ad_id = str(ad_id)

    if request.method == 'GET':
        return admin_ad_v2_get(id=ad_id)

    if request.method in 'PUT PATCH'.split():
        return admin_ad_v2_update(id=ad_id)

    elif request.method == 'DELETE':
        return admin_ad_v2_delete(id=ad_id)


@secured(scope.Advertisement.VIEWER)
def admin_ad_v2_get(id: str):

    ad = fetch_ad(id=id)
    if not ad:
        return http_err('Not Found', 404)

    return http_ok(ad=ad.asdict())


@secured(scope.Advertisement.ADMIN)
@converted(rest_key='values')
def admin_ad_v2_update(id: str, values: dict):

    ad = fetch_ad(id=id)
    if not ad:
        return http_err('Not Found', 404)

    old_ad = ad.asdict()

    update_ad(ad, values)

    return http_ok(ad=ad.asdict(), old_ad=old_ad)


@secured(scope.Advertisement.ADMIN)
def admin_ad_v2_delete(id: str):

    ad = fetch_ad(id=id)
    if not ad:
        return http_err('Not Found', 404)

    raise NotImplementedError()
