from flask import request, url_for
from flask_cors import cross_origin

from inobi.security import secured
from inobi.utils import http_ok, http_err, getargs

from .. import route
from ..security import Scope
from ..exceptions import InobiException
from ..utils import debug_exception

from ..utils.stats import generatereport
from ..db.stats import ad_stats, KEY_START, KEY_END, StatsType

from inobi.utils.converter import converted, Modifier

import typing as T


tag = '@Views.Stats:'


@route('/v1/admin/stats', methods=['GET', 'POST'])
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def stats_v1(ads: Modifier.UNION(str, list),
             interval: dict = None,
             start: float = None,
             end: float = None,
             with_file: Modifier.BOOL = True,
             magic: dict = None,
             falsify: int = None,
             force: Modifier.BOOL = False,
             user_retention_group_above: int = 5,
             stats_type: StatsType = StatsType.TRANSPORT,
             ):

    if not isinstance(interval, dict):
        try:
            start = float(start)
        except (ValueError, TypeError):
            start = None
        try:
            end = float(end)
        except (ValueError, TypeError):
            end = None

        interval = {
            KEY_START: start,
            KEY_END: end,
        }

    if isinstance(ads, str) and ads.lower() != 'all':
        if ',' in ads:
            ads = ads.split(',')
        else:
            ads = [ads, ]

    try:
        stats = ad_stats(ads, interval, stats_type=stats_type,
                         falsify=bool(falsify), falsify_factor=falsify,
                         with_magic=bool(magic), magic_props=magic,
                         user_retention_group_above=user_retention_group_above,
                         force=force,
                         )
    except InobiException as e:
        return http_err(str(e), 400)
    except ZeroDivisionError:
        return http_err('No Statistics for Ad In Chosen Interval', 404)
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        return http_err()
    else:
        d = dict(stats=stats)
        if with_file:
            import uuid
            fname = '{}.report.xlsx'.format(uuid.uuid4())
            filename = generatereport(stats, filename=fname)
            d['stats']['file'] = url_for('.uploaded_temp_file', filename=filename)
        return http_ok(data=d)

