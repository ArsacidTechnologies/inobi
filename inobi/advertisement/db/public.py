
import typing as T

import psycopg2
from .classes import Ad, AdView, Chronicle, AppAdView
from . import ads_v2

from inobi.config import SQL_CONNECTION

from ..utils import log_to_file


tag = "@{}:".format(__name__)


def get_random_ad(lat: float = None, lng: float = None,
                  platform: int = Ad.Platform.platform_fromstr('all'),
                  box_mac: str = None,
                  allow_weight=True,
                  test=False) -> T.Optional[Ad]:

    with psycopg2.connect(SQL_CONNECTION) as conn:

        cursor = conn.cursor()

        sql = '''
update ads a
    set requests = a.requests + %s
    from (
        select a.* from (
            select a.* from ads a
                inner join (select %s::varchar as mac) box
                    on true
                left join transports t
                    on t.device_id = box.mac
                left join routes r
                    on r.id = t.line_id
                left join transport_organization_transports tot
                    on tot.transport = t.id
                left join transport_organizations "to"
                    on "to".id = tot.organization
                left join cities c
                    on c.id = "to".city
                left join advertisement_devices adev
                    on adev.device_id = box.mac
                left join (
                    with recursive r as (
                        select id, group_id 
                            from advertisement_devices 
                            where group_id is not null
                        union 
                        select r.id, parent_group_id
                            from r
                            inner join advertisement_groups ag
                                on r.group_id = ag.id
                            where parent_group_id is not null
                    ) 
                        select 
                                dp.id, 
                                array_agg(dp.group_id) as groups, 
                                array_agg(format('g%%s', dp.group_id)) as _fgroups, 
                                array_agg(format('!g%%s', dp.group_id)) as _fngroups 
                            from r dp 
                            group by dp.id
                ) adevp
                    on adevp.id = adev.id
                    
                where a.enabled and (a.platform & %s) > 0
                and display_type = %s
                and (a.views_max is null or a.views < a.views_max)
                and (a.start_date is null or extract(epoch from now()) >= a.start_date)
                and (a.expiration_date is null or extract(epoch from now()) < a.expiration_date) 
                and (
                    a.transport_filters is null 
                    or r.id is null 
                    or r.type is null 
                    or (
                        (array[r.type, r.id, 'all', format('to%%s', "to".id)]::varchar[] && (a.transport_filters))
                        and not (array[format('!%%s', r.type), format('!%%s', r.id), format('!to%%s', "to".id)]::varchar[] && a.transport_filters)
                    )
                )
                and (
                    a.cities is null
                    or c.id is null
                    or (a.cities && array[c.id]::int[])
                )
                and (
                    case 
                        when a.time_to is null and a.time_from is null then
                            true
                        when a.time_to is not null and a.time_from is not null then
                            current_timestamp::time between a.time_from and a.time_to
                        when a.time_to is null then
                            current_timestamp::time between a.time_from and '00:00:00'
                        when a.time_from is null then
                            current_timestamp::time between '00:00:00' and a.time_to
                        else
                            -- should never come here... right??..
                            true
                    end                     
                )
                and (
                    a.device_filters is null
                    or adev.id is null
                    or (
                        adev.id is not null
                        and (array[format('d%%s', adev.id), 'all']::varchar[] && (a.device_filters))
                        and not (array[format('!d%%s', adev.id)]::varchar[] && a.device_filters)
                    )
                    and (
                        adevp.id is not null
                        and ((adevp._fgroups::varchar[] || 'all'::varchar)::varchar[] && (a.device_filters))
                        and not (adevp._fngroups::varchar[] && a.device_filters)
                    )
                )
                    
        ) a
            inner join (
                select id, calculate_distance(%s, %s, lat, lng) as dist from ads
            ) d 
                on d.id = a.id
            where d.dist < radius 
                or lat is null 
                or lng is null 
                or radius is null
            order by d.dist, weighted_random({weight}) desc
            limit 1
    ) b
    where a.id = b.id
    returning {return_}
'''.format(weight='weight' if allow_weight else 1,
           return_=Ad.select_fields('a'))

        cursor.execute(sql, [
            (1 if not test else 0),
            box_mac,
            platform,
            ads_v2.Ad.DISPLAY_TYPE_FULLSCREEN,
            lat,
            lng,
        ])

        row = cursor.fetchone()

        if row is None:
            log_to_file(tag, 'WARNING:', 'NO ADS ENABLED. NOTHING TO SHOW CLIENTS')
            return None

        ad = Ad._make(row)

        return ad


def register_view(view: AdView) -> AdView:

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        sql = 'insert into ad_views values ({insert}) returning {return_}'.format(insert=', '.join('%s' for _ in view),
                                                                                  return_=AdView.select_fields())

        cursor.execute(sql, view)

        inserted_view = AdView._make(cursor.fetchone())

        conn.commit()

        return inserted_view


def register_client_chronicles(chronicle: Chronicle, test: bool = False) -> Chronicle:

    if test:
        return chronicle

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        sql = 'update ads set views = views + 1 where id = %s returning *'
        cursor.execute(sql, (chronicle.ad_id, ))

        assert len(list(cursor)) == 1

        sql = '''   
insert into chronicles(client_mac, time, device, box_mac, ad_id, lat, lng, redirected, events) 
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
    returning {return_}
'''.format(return_=Chronicle.select_fields())

        cursor.execute(sql, chronicle.as_db_row)

        inserted = Chronicle.make_from_query(cursor.fetchone())

        return inserted


def register_app_view(view: AppAdView, test: bool = False) -> AppAdView:

    if test:
        return view

    with psycopg2.connect(SQL_CONNECTION) as conn:

        cursor = conn.cursor()

        sql = 'insert into app_ad_view as inserted values ({insert}) returning {return_}'.format(insert=', '.join('%s' for _ in view),
                                                                                                 return_=AppAdView.select_fields('inserted'))

        cursor.execute(sql, view.as_db_row)

        row = cursor.fetchone()
        conn.commit()

        return AppAdView.make_from_query(row)


