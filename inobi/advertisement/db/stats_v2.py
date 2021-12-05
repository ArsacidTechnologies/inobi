

from datetime import datetime

import typing as T
import itertools as IT
import functools as FT
import collections as C

import psycopg2

from inobi import config


from . import InobiException
from .classes import Ad

from .stats import StatsType


def stats_v1(ad_ids: T.List[str], start: float, end: float) -> T.Dict:

    if end < start:
        raise InobiException('Start Parameter Must Be Lesser Than End Parameter')

    with psycopg2.connect(config.SQL_CONNECTION) as conn:

        ads = _stats_ads(conn, ad_ids)

        if len(ads) == 0:
            raise InobiException('No Ads Found With Selected Ads ({})'.format(', '.join(ai for ai in ad_ids)))

        min_created = min(ads, key=lambda a: a.created).created

        if min_created > start:
            start = min_created

        start_dt = datetime.fromtimestamp(start)
        end_dt = datetime.fromtimestamp(end)

        hourly_views = _stats_hourly_views(conn, ad_ids, start_dt, end_dt)

        return [hv._asdict() for hv in hourly_views]


def _stats_ads(conn, ad_ids) -> T.List[Ad]:
    with conn.cursor() as cursor:
        sql = '''
    select * from ads where id in ({})
    '''.format(', '.join('%s' for _ in ad_ids))
        cursor.execute(sql, ad_ids)
        return list(map(Ad._make, cursor))


HourlyView = C.namedtuple('HourlyView', 'hour average total')


def _stats_hourly_views(conn,
                        ad_ids, start: datetime, end: datetime,
                        group_hour_up_to=6, group_hour_up_from=21) -> T.List[HourlyView]:
    with conn.cursor() as cursor:
        sql = '''
select cast(h as int), count(*)/cast(%s as float) as avg_views, count(*) as total from (
    select 
        case 
            when h <= {group_hour_up_to} 
                then {group_hour_up_to} 
            when h >= {group_hour_up_from} 
                then {group_hour_up_from} 
            else h 
        end as h 
        from (
            select  
                extract(hour from to_timestamp(time)) as h
            from chronicles
                where /*
                    client_mac is not null
                    and client_mac != '<incomplete>'
                    and */
                    time between 1521350109.609229 and 1521786457
                    and ad_id in ({ad_ids})
        ) _ii
) _i
    group by h
    order by h
'''.format(ad_ids=', '.join('%s' for _ in ad_ids),
           group_hour_up_to=group_hour_up_to,
           group_hour_up_from=group_hour_up_from)
        cursor.execute(sql, ((end-start).days, *ad_ids))
        return list(map(HourlyView._make, cursor))


from inobi import db
from inobi.transport.DataBase.models import Transport, Route
from inobi.transport.organization.db.models import TransportOrganization, transport_organization_routes
from inobi.city.models import City


from .models import User, UserLogin, UserDevice, Chronicle

from sqlalchemy import func, alias, cast, case


def user_uniqueness_v1(start, end, total_to):

    session = db.session

    q = session.query(Chronicle.client_mac).group_by(Chronicle.client_mac)

    if total_to or start or end:
        total_uniques = q.filter(Chronicle.time <= (total_to or end or start).timestamp()).count()
    else:
        total_uniques = q.count()

    stats = dict(total_uniques=total_uniques)

    if start and end:
        stats['uniques'] = q.filter(Chronicle.time.between(start.timestamp(), end.timestamp())).count()

    return stats


def transport_v2(start, end, cities=None, organizations=None, min_hour=5, max_hour=21):
    session = db.session

    t = alias(Transport, 't')
    ch = alias(Chronicle, 'ch')
    r = alias(Route, 'r')

    tor = alias(transport_organization_routes, 'tor')
    to = alias(TransportOrganization, 'to')
    c = alias(City, 'c')

    dt = cast(func.to_timestamp(ch.c.time), db.Date).label('dt')

    sub = session.query(func.min(t.c.id).label('id'), dt, func.count(ch.c.time).label('views')) \
        .select_from(t).outerjoin(ch, ch.c.box_mac == t.c.device_id) \
        .filter(ch.c.time.between(func.extract('epoch', start), func.extract('epoch', end))) \
        .group_by(ch.c.box_mac, 'dt') \
        .subquery('v')

    date = sub.c.dt.label('date')
    views = sub.c.views

    q = session.query(
        t.c.id, t.c.name, t.c.device_id,
        r.c.id.label('route_id'),
        r.c.name.label('route_name'),
        c.c.id.label('city_id'), c.c.name.label('city_name'),
        to.c.id.label('transport_organization_id'), to.c.name.label('transport_organization_name'),
        date, views
    ).select_from(t).outerjoin(sub, sub.c.id == t.c.id) \
        .outerjoin(r, r.c.id == t.c.line_id) \
        .outerjoin(tor, tor.c.line == r.c.id) \
        .outerjoin(to, to.c.id == tor.c.organization) \
        .outerjoin(c, c.c.id == to.c.city) \
        .order_by(date, views.desc())

    hours_q = session.query(Chronicle.box_mac, func.to_timestamp(Chronicle.time).label('ts')) \
        .select_from(Chronicle).filter(Chronicle.time.between(func.extract('epoch', start), func.extract('epoch', end)))

    hours_transport_joined = False

    def with_cities_joined(q):
        nonlocal hours_transport_joined
        if hours_transport_joined:
            return q
        hours_transport_joined = True
        return q \
            .outerjoin(t, t.c.device_id == Chronicle.box_mac) \
            .outerjoin(tor, tor.c.line == t.c.line_id) \
            .outerjoin(to, to.c.id == tor.c.organization) \
            .outerjoin(c, c.c.id == to.c.city)

    with_organizations_joined = with_cities_joined

    if cities is not None:
        q = q.filter(c.c.id.in_(cities))
        hours_q = with_cities_joined(hours_q).filter(c.c.id.is_(None) | c.c.id.in_(cities))

    if organizations is not None:
        q = q.filter(to.c.id.in_(organizations))
        hours_q = with_organizations_joined(hours_q).filter(to.c.id.is_(None) | to.c.id.in_(organizations))

    hours_q_sub = hours_q.subquery('q')

    hours_q_sub = session.query(
        hours_q_sub.c.box_mac,
        cast(func.extract('hour', hours_q_sub.c.ts), db.Integer).label('hour'),
        cast(hours_q_sub.c.ts, db.Date).label('date')
    ).select_from(hours_q_sub).subquery('q')

    hour_column = hours_q_sub.c.hour

    hours_q_sub = session.query(
        hours_q_sub.c.box_mac,
        case([
            (hour_column < min_hour, min_hour),
            (hour_column > max_hour, max_hour)
        ], else_=hour_column).label('hour'),
        hours_q_sub.c.date
    ).select_from(hours_q_sub).subquery('q')

    hours_q_sub = session.query(
        hours_q_sub.c.hour,
        hours_q_sub.c.date,
        func.count(hours_q_sub.c.box_mac.distinct()).label('transports'),
        func.count().label('views'),
    ).select_from(hours_q_sub).group_by(hours_q_sub.c.hour, hours_q_sub.c.date).subquery('q')

    days_column = cast(func.count(hours_q_sub.c.date.distinct()), db.Float).label('days')

    hours_q = session.query(
        hours_q_sub.c.hour,
        cast(func.avg(hours_q_sub.c.transports), db.Float).label('transports'),
        (cast(func.sum(hours_q_sub.c.views), db.Float) / days_column).label('views'),
        cast(days_column, db.Integer).label('days'),
    ).group_by(hours_q_sub.c.hour).order_by(hours_q_sub.c.hour)

    hours_stats = []
    for r in hours_q:
        hours_stats.append(r._asdict())

    dates = set()

    # todo: add distinct in sql
    # stats = []
    # no_views_transports = []
    stats = dict()
    no_views_transports = dict()

    keys = None
    for row in q:
        if not keys:
            keys = row.keys()

        row = row._asdict()

        date = row['date']
        if date is not None:
            dates.add(date)
            row['date'] = date.strftime('%Y-%m-%d')

        if date is None:
            no_views_transports[(row['id'], row['date'])] = row
            # no_views_transports.append(row)
        else:
            stats[(row['id'], row['date'])] = row
            # stats.append(row)

    return dict(stats=stats, hour_stats=hours_stats, dates=sorted(dates), no_views_transports=no_views_transports)


def user_views_v2(start, end, cities=None, organizations=None,
                  limit=10, offset=0, stats_type: StatsType = StatsType.TRANSPORT,
                  ):

    session = db.session

    stats_type_filter = Chronicle.ads_device_id.is_(None) if stats_type is StatsType.TRANSPORT else Chronicle.ads_device_id.isnot(None)

    ch = session.query(
        Chronicle.client_mac,
        func.count(Chronicle.client_mac).label('views'),
        func.min(Chronicle.time).label('first_view_time'),
        func.max(Chronicle.time).label('last_view_time'),
    ).select_from(Chronicle) \
        .outerjoin(Transport, Transport.device_id == Chronicle.box_mac) \
        .outerjoin(transport_organization_routes, transport_organization_routes.c.line == Transport.line_id) \
        .outerjoin(TransportOrganization, TransportOrganization.id == transport_organization_routes.c.organization) \
        .outerjoin(City, City.id == TransportOrganization.city) \
        .filter(func.to_timestamp(Chronicle.time).between(start, end), stats_type_filter) \
        .group_by(Chronicle.client_mac)

    if cities is not None:
        ch = ch.filter(City.id.in_(cities))
    if organizations is not None:
        ch = ch.filter(TransportOrganization.id.in_(organizations))

    ch = ch.subquery('ch')

    q = session.query(
        User.id,
        User.phone,
        func.extract('epoch', User.registered).label('registered'),
        cast(func.sum(ch.c.views), db.Integer).label('views'),
        func.count(UserDevice.id).label('devices'),
        func.min(ch.c.first_view_time).label('first_view'),
        func.max(ch.c.last_view_time).label('last_view'),
    ).select_from(User) \
        .join(UserDevice) \
        .join(ch, ch.c.client_mac == UserDevice.mac) \
        .group_by(User.id) \
        .order_by(db.text('views desc'), db.text('last_view'))

    return q.limit(limit).offset(offset).all(), q.count()


def user_registrations_v2(phone=None, registered_start=None, registered_end=None,
                          cities=None, organizations=None,
                          limit=10, offset=0,
                          stats_type: StatsType = StatsType.TRANSPORT,
                          ) -> T.Tuple[T.List[dict], int]:

    session = db.session

    stats_type_filter = Chronicle.ads_device_id.is_(None) if stats_type is StatsType.TRANSPORT else Chronicle.ads_device_id.isnot(None)

    logins_by_user_sub = session.query(func.min(UserLogin.id).label('id')).select_from(UserLogin).group_by(
        UserLogin.user_id).subquery('q')

    l = session.query(UserLogin).join(logins_by_user_sub, logins_by_user_sub.c.id == UserLogin.id).subquery('l')

    u = alias(User, 'u')
    d = alias(UserDevice, 'd')

    chronicles_by_client_mac_sub = session.query(func.min(Chronicle.id).label('id')) \
        .select_from(Chronicle) \
        .group_by(Chronicle.client_mac) \
        .subquery('q')

    ch = session.query(Chronicle) \
        .join(chronicles_by_client_mac_sub, chronicles_by_client_mac_sub.c.id == Chronicle.id) \
        .filter(stats_type_filter) \
        .subquery('ch')

    t = alias(Transport, 't')
    r = alias(Route, 'r')

    tor = alias(transport_organization_routes, 'tor')
    to = alias(TransportOrganization, 'to')
    c = alias(City, 'c')

    q = session.query(u.c.id, u.c.phone, u.c.registered,
                      l.c.time.label('login_time'),
                      d.c.id.label('device_id'), d.c.mac, d.c.description,
                      ch.c.id.label('v_id'), ch.c.ad_id, ch.c.redirected, ch.c.lat, ch.c.lng,
                      t.c.id.label('t_id'), t.c.name.label('t_name'),
                      r.c.id.label('line_id'), r.c.name.label('line_name'),
                      c.c.id.label('city_id'), c.c.name.label('city_name')
                      ) \
        .select_from(u) \
        .join(l, l.c.user_id == u.c.id) \
        .join(d, l.c.device_id == d.c.id) \
        .outerjoin(ch, ch.c.client_mac == d.c.mac) \
        .outerjoin(t, t.c.device_id == ch.c.box_mac) \
        .outerjoin(r, r.c.id == t.c.line_id) \
        .outerjoin(tor, tor.c.line == t.c.line_id) \
        .outerjoin(to, to.c.id == tor.c.organization) \
        .outerjoin(c, c.c.id == to.c.city)

    request_args = {}

    if cities is not None:
        q = q.filter(c.c.id.in_(cities))
        request_args['cities'] = cities
    if organizations is not None:
        q = q.filter(to.c.id.in_(organizations))
        request_args[organizations] = organizations

    if phone:
        q = q.filter(u.c.phone.like('%{}%'.format(phone)))
        request_args['phone'] = phone

    if registered_start and registered_end:
        q = q.filter(u.c.registered.between(registered_start, registered_end))
        request_args.update(registered_start=registered_start.isoformat(),
                            registered_end=registered_end.isoformat())

    def _datetime_as_unix(d):
        return {
            k: v.timestamp() if isinstance(v, datetime) else v
            for k, v in d.items()
        }

    def map_user(row):
        d = _datetime_as_unix(row._asdict())

        d['device'] = dict(
            id=d.pop('device_id'),
            mac=d.pop('mac'),
            description=d.pop('description'),
        )

        t_info = {
            k: d.pop(k)
            for k in 't_id t_name line_id line_name'.split()
        }

        view = {
            k: d.pop(k)
            for k in 'v_id ad_id redirected lat lng'.split()
        }

        # city = {
        #     k: d.pop(k)
        #     for k in ('c_id', 'c_name')
        # }

        if t_info['t_id'] is None:
            t_info = None
        view['transport'] = t_info

        if view['ad_id'] is None:
            view = None

        # if city['c_id'] is None:
        #     city = None
        # view['city'] = city

        d['view'] = view

        return d

    res = list(map(map_user, q.limit(limit).offset(offset)))

    return res, q.count()
