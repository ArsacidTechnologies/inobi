
from .. import bp

from flask import request

import json

from inobi.utils.converter import converted, Modifier


@bp.route('/v1/test')
@converted
def test(kek=None, mek=None, rest=None, **kwargs):

    d = dict(
        kek=kek,
        mek=mek,
        rest=rest,
        kwargs=kwargs
    )

    return json.dumps(d), 200
