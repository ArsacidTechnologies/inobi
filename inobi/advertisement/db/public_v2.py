

import typing as T
from datetime import time

from sqlalchemy import func, case, Time
from sqlalchemy.orm import joinedload, load_only

from inobi import db
from .models import Ad, View, Viewer, Chronicle
from .. import error_codes
from ..exceptions import AdvertisementException
from ..utils import get_today_epochs


def get_random_ad(lat: float = None, lng: float = None,
                  platform: int = Ad.Platform.platform_fromstr('all'),
                  display_type: str = Ad.DISPLAY_TYPE_FULLSCREEN,
                  allow_weight=True,
                  test=False,
                  only_unvisited: bool = False,
                  client_mac: str = None) -> T.Optional[T.Tuple[Ad, str]]:

    # todo: add transport_filters, device_filters and city_filters
    chronicles = []
    if only_unvisited:
        chronicles = Chronicle.query\
                .filter(client_mac=client_mac)\
                .filter(Chronicle.time.between(*get_today_epochs()))\
                .options(load_only("ad_id")).all()

    q = Ad.query\
        .filter(Ad.enabled)\
        .filter(Ad.views_max.is_(None) | (Ad.views < Ad.views_max))\
        .filter(Ad.start_date.is_(None) | (func.extract('epoch', func.now()) >= Ad.start_date))\
        .filter(Ad.expiration_date.is_(None) | (func.extract('epoch', func.now()) < Ad.expiration_date))\
        .filter(case([
            (
                Ad.time_from.is_(None) & Ad.time_to.is_(None),
                True
            ), (
                Ad.time_to.isnot(None) & Ad.time_from.isnot(None),
                func.now().cast(Time).between(Ad.time_to, Ad.time_from)
            ), (
                Ad.time_to.is_(None),
                func.now().cast(Time).between(Ad.time_from, time(0, 0, 0))
            ), (
                Ad.time_from.is_(None),
                func.now().cast(Time).between(time(0, 0, 0), Ad.time_to)
            )
            ],
            else_=True
        ))\
        .order_by(func.weighted_random(Ad.weight if allow_weight else 1)) \
        .filter(Ad.platform.op('&')(platform) != 0) \
        .filter(Ad.display_type == display_type)

    if lat is not None and lng is not None:
        q = q.filter(Ad.lat.is_(None) | Ad.lng.is_(None) | Ad.radius.is_(None)
                     | (func.calculate_distance(lat, lng, Ad.lat, Ad.lng) < Ad.radius))
    last_query = q

    if only_unvisited:
        for chronicle in chronicles:
            q.filter(id != chronicle.ad_id)

    ad = q.first()
    if not ad:
        last_ad = last_query.first()
        if not last_ad:
            return
        ad = last_ad

    if test:
        ad.requests += 1

    view = View(platform=platform, lat=lat, lng=lng)
    # ad_view reocrd will be appended here
    ad.ad_views.append(view)

    db.session.add(ad)
    db.session.commit()

    return ad, view.key


import datetime

from .devices import find_device


def register_view(view_key: str,
                  viewer_device_id: str,
                  is_redirected: bool,
                  events: T.List[dict] = None,
                  viewer_device_description: str = None,
                  platform: int = Ad.Platform.platform_fromstr('all'),
                  provider_id: str = None,
                  lat: float = None,
                  lng: float = None,
                  view_time: datetime.datetime = None,
                  test: bool = False,
                  ) -> T.Optional[View]:

    view: View = View.query.filter(View.key == view_key)\
        .options(joinedload(View.ad)).first()
    if not view:
        return None

    if view.time is not None:
        raise AdvertisementException('View already registered', code=error_codes.VIEW_ALREADY_REGISTERED)

    view.time = view_time if view_time is not None else datetime.datetime.now()

    if not view.is_possible:
        raise AdvertisementException('View registration too quickly', code=error_codes.VIEW_REGISTRATION_TOO_QUICKLY)

    ads_device_id = None
    ads_group_id = None

    if provider_id:

        device = find_device(device_id=provider_id)

        if device:
            ads_device_id = device.id
            ads_group_id = device.group_id

            lat, lng = device.lat, device.lng

            group = None

            while lat is None or lng is None:
                if group is None:
                    group = device.group
                else:
                    group = group.parent_group
                if group is None:
                    lat, lng = 0, 0
                    break
                else:
                    lat, lng = group.lat, group.lng

    viewer = Viewer.query.filter(Viewer.device_id == viewer_device_id).first()
    if not viewer:
        viewer = Viewer(device_id=viewer_device_id,
                        device_description=viewer_device_description)

    if viewer_device_description is not None \
            and (viewer.device_description is None or viewer.device_description != viewer_device_description):
        viewer.device_description = viewer_device_description

    view.viewer = viewer
    view.provider_id = provider_id
    view.ads_device_id = ads_device_id
    view.ads_group_id = ads_group_id
    view.is_redirected = is_redirected
    view.lat, view.lng = lat, lng
    view._events = events
    view.time = view_time
    view.platform = platform

    if test:
        return view

    view.ad.views += 1

    db.session.add(view)
    db.session.commit()

    return view
