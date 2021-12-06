
import typing as T


from inobi import db
from .models import Ad


import datetime
from ..exceptions import AdvertisementException as InobiException

from .. import utils

import builtins


def create_ad(type: str,
              duration: float,
              redirect_url: str,
              source: str,
              title: str,
              external_source: bool = False,
              description: str = None,
              lat: float = None, lng: float = None,
              views_max: int = None,
              expiration_date: float = None,
              enabled: bool = True,
              weight: int = 1,
              platform: int = Ad.Platform.ALL,
              radius: float = Ad.Radius.DEFAULT,
              transport_filters: list = None,
              cities: list = None,
              time_from: datetime.time = None,
              time_to: datetime.time = None,
              start_date: float = None,
              device_filters: list = None,
              display_type: str = Ad.DISPLAY_TYPE_FULLSCREEN,
              ) -> Ad:

    if redirect_url.startswith('http://') or redirect_url.startswith('https://'):
        redirect_url = redirect_url.replace('http://', '').replace('https://', '')

    geo_count = [lat, lng].count(None)
    if geo_count == 2:
        pass
    elif geo_count != 0:
        raise InobiException("'lat' And 'lng' Parameters Must Come Alongside Each Other")

    Ad.Radius.check_radius(radius)

    if type not in Ad.TYPES:
        raise InobiException("'type' Parameter must be one of {}".format(set(Ad.TYPES)))

    if not (0 < weight < 11):
        raise InobiException('Weight Parameter Must Be Integer Type And Be In Range [1:10]')

    if transport_filters is not None:
        if not transport_filters:
            raise InobiException("'transport_filters' Parameter Should Not Be Empty")
        if set(builtins.type(i) for i in transport_filters).difference({str, int}):
            raise InobiException("'transport_filters' Parameter Must Be An Array of String Or Integer Values")

        transport_filters = list(map(str, transport_filters))

    if device_filters is not None:
        if not device_filters:
            raise InobiException("'device_filters' Parameter Should Not Be Empty")
        if set(builtins.type(i) for i in device_filters).difference({str, int}):
            raise InobiException("'device_filters' Parameter Must Be An Array of String Or Integer Values")

        device_filters = list(map(str, device_filters))

    ad = Ad(
        type=type,
        duration=duration,
        redirect_url=redirect_url,
        weight=weight,
        source=source,
        enabled=enabled,
        title=title,
        description=description,
        lat=lat,
        lng=lng,
        views_max=views_max,
        expiration_date=expiration_date,
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

    ad.external_source = external_source

    ad.prepare_source()

    db.session.add(ad)
    db.session.commit()

    return ad


def list_ads() -> T.List[Ad]:
    return db.session.query(Ad).order_by(Ad.created.desc()).all()


def fetch_ad(id: str) -> T.Optional[Ad]:
    return db.session.query(Ad).filter(Ad.id == id).first()


def update_ad(ad: Ad, values: dict):

    geo_count = [values.get('lat'), values.get('lng')].count(None)
    if geo_count == 2:
        pass
    elif geo_count != 0:
        raise InobiException("'lat' And 'lng' Parameters Must Come Alongside Each Other")

    old_ad_source = ad.source
    old_ad_external_source = ad.external_source

    updated = ad.update(values, updated=datetime.datetime.now().timestamp())

    if not updated:
        raise InobiException('Nothing To Update')

    clean_media = False
    if 'source' in values:
        if ad.external_source:
            clean_media = True
        else:

            if utils.media_exists(ad.source):
                pass
            elif utils.media_exists(ad.source, in_temp=True):
                ad.prepare_source()
                clean_media = True
            else:
                raise InobiException('Source file does not exists in Uploads')

    db.Session.object_session(ad).commit()

    if clean_media and not old_ad_external_source:
        if not utils.remove_source(old_ad_source):
            raise Exception('ERROR: Removing source from media to temp folder failed, ad_id: {}, source: {}'.format(ad.id, old_ad_source))
