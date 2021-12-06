
from flask_cors import cross_origin

from .. import bp

from inobi.utils import http_ok, http_err

import os, sys

import flask

from inobi.utils.converter import converted, Modifier


@bp.route('/v1/test')
@cross_origin()
@converted()
def ads_test_v1(l: Modifier.ARRAY_OF(str, int)):

    req = flask.request

    print(l)

    return http_ok(
        l=l,
        headers=dict(req.headers),
        args=req.args

    )


@bp.route('/v2/test/<uuid:ad_id>')
@cross_origin()
@converted
def test_v2(ad_id, limit: int = 10, offset: int = 0):

    ad_id = ad_id.hex

    from ..db.models import Ad

    ad = Ad.query.get(ad_id)

    chronicles = list(ad.chronicles.limit(limit).offset(offset))

    return http_ok(ad=ad.asdict(),
                   page=dict(limit=limit, offset=offset,
                             count=len(chronicles),
                             chronicles_count=ad.chronicles.count(),
                             ),
                   chronicles=[ch.asdict() for ch in chronicles],
                   )


@bp.route('/v3/test')
@cross_origin()
@converted
def test_v3(limit: int = 10, offset: int = 0, **kwargs):

    from ..db import devices

    def kek(kv):
        k, v = kv
        if hasattr(devices.Device, k):
            return getattr(devices.Device, k) == v

    ds = devices.Device.query.filter(*filter(lambda x: x is not None, map(kek, kwargs.items())))\
        .limit(limit)\
        .offset(offset)\
        .all()

    return http_ok(count=len(ds),
                   devices=[d.asdict() for d in ds],
                   )



