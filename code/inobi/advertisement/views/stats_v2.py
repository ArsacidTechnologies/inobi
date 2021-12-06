
import typing as T
from flask_cors import cross_origin

from .. import route

from inobi.security import secured, scope
from inobi.utils.converter import converted, Modifier

from inobi.utils import http_err, http_ok


from flask import url_for


from ..exceptions import AdvertisementBaseException
from .. import error_codes

from ..db import stats_v2
from ..db.stats import StatsType


class AdvertisementStatsException(AdvertisementBaseException):
    pass


def ads_modifier(x) -> T.List[str]:
    if isinstance(x, str):
        return x.split()
    if isinstance(x, list) and all([isinstance(a, str) for a in x]):
        return x

    raise Exception('Ads Parameter Must Be Union[str, list]')


@route('/v1/admin/stats/users/uniqueness/')
@cross_origin()
@secured([scope.Advertisement.VIEWER])
@converted
def advertisement_uniqueness_stats_v1(start: Modifier.DATETIME = None,
                                      end: Modifier.DATETIME = None,
                                      total_to: Modifier.DATETIME = None):

    stats = stats_v2.user_uniqueness_v1(start, end, total_to)

    return http_ok(stats=stats)


@route('/v2/admin/stats')
@cross_origin()
@secured([scope.Advertisement.VIEWER])
@converted(description_of__ads='Ads Must Be One of [str, list]')
def advertisement_stats_v2(ads: ads_modifier,
                           start: float, end: float,
                           with_file: Modifier.BOOL = True):

    from ..db import stats_v2 as db

    try:
        stats = db.stats_v1(ads, start, end)

    except Exception as e:
        raise e
        return http_err()
    else:

        return http_ok(stats=stats, request=dict(ads=ads, start=start, end=end))

        # d = dict(stats=stats)
        # if with_file:
        #     from datetime import date
        #     fname = '{main_name}({start}-{end}).report.xlsx'.format(
        #         main_name=','.join(ad.split('-')[0] for ad in ads),
        #         start=date.fromtimestamp(interval.get(KEY_START, start)),
        #         end=date.fromtimestamp(interval.get(KEY_END, end))
        #     )
        #     filename = generatereport(stats, filename=fname)
        #     d['stats']['file'] = url_for('uploaded_temp_file', filename=filename)
        # return HTTP_OK(data=d)


@route('/v1/admin/stats/transports/')
@cross_origin()
@secured([scope.Advertisement.VIEWER])
@converted
def advertisement_transport_stats_v1(start: Modifier.datetime, end: Modifier.datetime,
                                     cities: Modifier.ARRAY_OF(int) = None,
                                     organizations: Modifier.ARRAY_OF(int) = None,
                                     min_hour: int = 5, max_hour: int = 21):

    start, end = sorted([start, end])

    stats = stats_v2.transport_v2(start, end, cities, organizations, min_hour, max_hour)

    return http_ok(count=len(stats['stats']),
                   dates=[d.strftime('%Y-%m-%d') for d in stats['dates']],
                   hour_stats=stats['hour_stats'],
                   no_views=list(stats['no_views_transports'].values()),
                   stats=list(stats['stats'].values()))


def pagination_options(res, total_count, limit, offset, endpoint: T.Union[str, T.Callable], **url_for_kwargs) -> dict:

    if callable(endpoint):
        endpoint = endpoint.__name__

    pagination = dict(count=len(res), total_count=total_count, params=dict(prev=None, next=None), url=dict(prev=None, next=None))

    if offset + limit < total_count:
        pagination['params']['next'] = next_params = dict(**url_for_kwargs, limit=limit, offset=offset + limit)
        pagination['url']['next'] = url_for('.'+endpoint, **next_params, _external=True)

    if offset != 0:
        pagination['params']['prev'] = prev_params = dict(**url_for_kwargs, limit=min(limit, offset), offset=max(0, offset - limit))
        pagination['url']['prev'] = url_for('.'+endpoint, **prev_params, _external=True)

    return pagination


@route('/v1/admin/stats/users/views/')
@cross_origin()
@secured([scope.Advertisement.VIEWER])
@converted()
def advertisement_user_views_stats_v1(start: Modifier.datetime, end: Modifier.datetime, limit: int = 10, offset: int = 0,
                                      cities: Modifier.ARRAY_OF(int) = None, organizations: Modifier.ARRAY_OF(int) = None,
                                      stats_type: StatsType = StatsType.TRANSPORT,
                                      ):

    start, end = sorted((start, end))

    users, total_count = stats_v2.user_views_v2(start, end, cities, organizations,
                                                limit=limit, offset=offset, stats_type=stats_type)

    return http_ok(pagination=pagination_options(users, total_count,
                                                 limit=limit, offset=offset,
                                                 endpoint=advertisement_user_views_stats_v1,
                                                 start=start.isoformat(), end=end.isoformat(),
                                                 stats_type=stats_type.value,
                                                 ),
                   stats=[u._asdict() for u in users],
                   )


@route('/v1/admin/stats/users/registrations/')
@cross_origin()
@secured([scope.Advertisement.VIEWER])
@converted()
def advertisement_user_registration_stats_v1(phone: str = None,
                                             registered_start: Modifier.datetime = None, registered_end: Modifier.datetime = None,
                                             cities: Modifier.ARRAY_OF(int) = None, organizations: Modifier.ARRAY_OF(int) = None,
                                             limit: int = 10, offset: int = 0,
                                             stats_type: StatsType = StatsType.TRANSPORT,
                                             ):

    if not (phone or (registered_end and registered_start)):
        raise AdvertisementStatsException('Filters must be specified', error_codes.NO_FILTERS)

    request_args = {}

    if cities is not None:
        request_args['cities'] = cities
    if organizations is not None:
        request_args[organizations] = organizations

    if phone:
        request_args['phone'] = phone

    if registered_start and registered_end:
        request_args.update(registered_start=registered_start.isoformat(),
                            registered_end=registered_end.isoformat())

    request_args['stats_type'] = stats_type.value

    stats, total_count = stats_v2.user_registrations_v2(phone=phone, registered_start=registered_start,
                                                        registered_end=registered_end,
                                                        cities=cities, organizations=organizations,
                                                        limit=limit, offset=offset,
                                                        stats_type=stats_type,
                                                        )

    return http_ok(pagination=pagination_options(stats, total_count,
                                                 limit=limit, offset=offset,
                                                 endpoint=advertisement_user_registration_stats_v1,
                                                 **request_args,
                                                 ),
                   stats=stats,
                   )
