
import time
import typing as T

import psycopg2

from inobi.config import SQL_CONNECTION

from ..exceptions import InobiAdsException as InobiException
from ..utils import debug_exception, log_to_file, purge_uuid, is_valid_uuid
from .classes import Ad


tag = "@{}:".format(__name__)


class DbKey:

    CLIENT_MAC = 'client_mac'
    USER_AGENT = 'user_agent'
    TIME = 'time'
    BOX_MAC = 'box_mac'
    AD_ID = 'ad_id'
    LAT = 'lat'
    LON = 'lon'
    CREATED = 'created'
    TYPE = 'type'
    ID = 'id'
    DURATION = 'duration'
    REDIRECT_URL = 'redirect_url'
    SOURCE = 'source'
    WEIGHT = 'weight'
    VIEWS = 'views'
    TITLE = 'title'
    DESCRIPTION = 'description'
    ENABLED = 'enabled'
    VIEWS_MAX = 'views_max'
    EXPIRATION_DATE = 'expiration_date'
    REQUESTS = 'requests'

    PREV_VERSION = 'previous_version'
    VERSION = 'version'

    LNG = 'lng'

    DEVICE = 'device'
    REDIRECTED = 'redirected'
    EVENTS = 'events'
    CHRONICLES = 'chronicles'


_ad_indexes = {
    DbKey.ID: 0,
    DbKey.TYPE: 1,
    DbKey.DURATION: 2,
    DbKey.REDIRECT_URL: 3,
    DbKey.WEIGHT: 4,
    DbKey.VIEWS: 5,
    DbKey.SOURCE: 6,
    DbKey.CREATED: 7,
    DbKey.ENABLED: 8,
    DbKey.TITLE: 9,
    DbKey.DESCRIPTION: 10,
    DbKey.LAT: 11,
    DbKey.LON: 12,
    DbKey.VIEWS_MAX: 13,
    DbKey.EXPIRATION_DATE: 14,
    DbKey.REQUESTS: 15
}


def ad_key_index(key):
    return _ad_indexes[key]


__ad_keys__ = [
    DbKey.TYPE,
    DbKey.DURATION,
    DbKey.REDIRECT_URL,
    DbKey.WEIGHT,
    DbKey.VIEWS,
    DbKey.SOURCE,
    DbKey.TITLE,
    DbKey.DESCRIPTION,
    DbKey.CREATED,
    DbKey.LAT,
    DbKey.LON,
    DbKey.ENABLED,
    DbKey.VIEWS_MAX,
    DbKey.EXPIRATION_DATE,
    DbKey.REQUESTS
]

AD_TYPES = frozenset(("banner", "video", "iframe"))

__listable_tables__ = {
    'views': 'ad_view',
    'requests': 'request',
    'chronicles': 'chronicles',
}


REQUEST_REQUIREMENTS = [DbKey.AD_ID, DbKey.CLIENT_MAC, DbKey.TIME, DbKey.USER_AGENT, DbKey.BOX_MAC, DbKey.LAT, DbKey.LON]
REQUEST_NULLABLES = [DbKey.CLIENT_MAC, DbKey.USER_AGENT, DbKey.LAT, DbKey.LON]


def get_list(table_key='views', offset=0, limit='none', date_from=None, date_to=None, ad_id=None):

    if not isinstance(table_key, str):
        table_key = str(table_key)
    table_key = table_key.lower()

    table = __listable_tables__.get(table_key)
    if table is None:
        raise InobiException('No List With Such Key. (Available: {})'.format(', '.join(__listable_tables__.keys())))

    if not isinstance(date_from, (int, float)):
        try:
            date_from = float(date_from)
        except:
            raise InobiException("Parameter 'date_from' Must be a Number")

    if ad_id:
        if isinstance(ad_id, str):
            ad_id = is_valid_uuid(ad_id)
            if not ad_id: raise InobiException('Ad Identifier Is Invalid. ({})'.format(ad_id))
            ad_id_sql = "ad_id = '{}'".format(ad_id)
        elif isinstance(ad_id, list):
            # ad_id = [valid_uuid(id) for id in ad_id]  # list(map(lambda x: valid_uuid(x), ad_id))
            for index, id in enumerate(ad_id):
                _id = is_valid_uuid(id)
                if not _id: raise InobiException('Ad Identifier Is Invalid. ({})'.format(id))
                else: ad_id[index] = _id
            ad_id_sql = 'ad_id IN {}'.format(str(ad_id).replace('[', '(').replace(']', ')'))
        else:
            raise InobiException('Unknown Ad Identifier Type')

    if not isinstance(date_to, (int, float)):
        try:
            date_to = float(date_to)
        except:
            # print('\t', tag, "'date_to' is not present. Fetching results for date_from date...")
            from time import gmtime
            from calendar import timegm
            date_list = list(gmtime(date_from))
            date_list[3] = 0
            date_list[4] = 0
            date_list[5] = 0
            date_from = timegm(tuple(date_list))

            date_list[2] = date_list[2] + 1
            date_list[7] = date_list[7] + 1

            date_to = timegm(tuple(date_list))

    if date_to < date_from:
        date_to, date_from = date_from, date_to

    if str(limit).lower() == 'none':
        limited = False
    else:
        try:
            limit = int(limit)
            range_from = offset
            range_to = range_from + limit
            limited = True
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            limited = False

    connection = psycopg2.connect(SQL_CONNECTION)
    try:
        cursor = connection.cursor()
        try:

            sql = '''
select * from ads '''

            sql = (" SELECT CONVERT([varchar](max), [ad_id]) AS [ad_id], [client_mac], [time], [user_agent], [box_mac], [lat], [lon] FROM ( "
                   "  SELECT [ad_id], [client_mac], [time], [user_agent], [box_mac], [lat], [lon], ROW_NUMBER() "
                   "         OVER (ORDER BY [time]) AS [row] "
                   "  FROM [{}] "
                   "  WHERE time > ? AND time <= ? {} "
                   ") a {} "
                   " ORDER BY [time] DESC ").\
                format(table, 'AND {}'.format(ad_id_sql) if ad_id else '', 'WHERE [row] >= ? AND [row] <= ?' if limited else '')

            # sql_all = ('SELECT CONVERT([varchar](max), [ad_id]) AS [ad_id], [ip], [time], [user_agent], [box_mac], [lat], [lon] '
            #            'FROM [request]')

            params = [date_from, date_to]
            if limited:
                params.extend([range_from, range_to])

            cursor.execute(sql, params)

            items = list()

            row = cursor.fetchone()
            while row:
                request = {}
                for (index, key) in enumerate(REQUEST_REQUIREMENTS):
                    if index == 0:
                        request[key] = purge_uuid(row[index])
                    else:
                        request[key] = row[index]

                items.append(request)
                row = cursor.fetchone()

            items.date_from = date_from
            items.date_to = date_to

            return items
        except Exception as e:
            debug_exception(tag, e)
            pass
        finally:
            if cursor is not None:
                cursor.close()
    except Exception as e:
        debug_exception(tag, e)
    finally:
        if connection is not None:
            connection.close()


def create_ad(ad: Ad) -> Ad:

    ad.prepare_source()

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        sql = '''
insert into ads (
    type, duration, redirect_url, source, created, enabled, title, 
    weight, description, lat, lng, views_max, expiration_date, platform,
    radius, transport_filters, cities, time_from, time_to, start_date
) 
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    returning {return_}
'''.format(return_=Ad.select_fields())

        cursor.execute(sql, (
            ad.type, ad.duration, ad.redirect_url, ad.source, ad.created, ad.enabled, ad.title,
            ad.weight, ad.description, ad.lat, ad.lng, ad.views_max, ad.expiration_date,
            ad.platform, ad.radius, ad.transport_filters, ad.cities, ad.time_from, ad.time_to,
            ad.start_date,
            )
        )

        row = cursor.fetchone()

        ad = Ad._make(row)

        return ad


def update_ad(ad_info) -> T.Tuple[Ad, Ad]:

    if not isinstance(ad_info, dict):
        raise InobiException('Ad Information Forbidden')

    _id = ad_info.get('id')
    if not is_valid_uuid(_id):
        raise InobiException('Ad identifier is not Present or Incorrect')

    if DbKey.TYPE in ad_info and ad_info[DbKey.TYPE] not in ['banner', 'video']:
        raise InobiException('Type parameter is Forbidden')

    if DbKey.WEIGHT in ad_info and not (0 < int(ad_info[DbKey.WEIGHT]) < 11):
        raise InobiException('Weight parameter must be in [0:10] range')

    source = ad_info.get(DbKey.SOURCE)
    from ..utils import media_exists
    clean_media = False
    if source:
        if ad_info.get('external_source', None):
            ad_info['source'] = '!'+source
            clean_media = True
        else:
            if media_exists(source):
                pass
            elif media_exists(source, in_temp=True):
                from ..utils import prepare_source
                if not prepare_source(source):
                    raise(tag, 'Could not prepare source: {}'.format(source))
                else:
                    clean_media = True
            else:
                raise InobiException('Source file does not exists in Uploads')

    platform = ad_info.get('platform')
    if platform:
        ad_info['platform'] = Ad.Platform.platform_fromstr(platform)

    if 'radius' in ad_info:
        ad_info['radius'] = Ad.Radius.check_radius(ad_info['radius'])

    geo_count = [ad_info.get('lat'), ad_info.get('lng')].count(None)
    if geo_count == 2:
        pass
    elif geo_count != 0:
        raise InobiException("'lat' And 'lng' Parameters Must Come Alongside Each Other")

    allowed_keys = [
        DbKey.TYPE,
        DbKey.DURATION,
        DbKey.REDIRECT_URL,
        DbKey.LAT,
        DbKey.LNG,
        DbKey.SOURCE,
        DbKey.WEIGHT,
        DbKey.TITLE,
        DbKey.DESCRIPTION,
        DbKey.ENABLED,
        DbKey.VIEWS_MAX,
        DbKey.EXPIRATION_DATE,
        'platform',
        'radius',
        'transport_filters',
        'cities',
        'time_from',
        'time_to',
        'start_date',
    ]

    update_keys = []
    for key in allowed_keys:
        if key in ad_info:
            update_keys.append(key)

    if len(update_keys) == 0:
        raise InobiException('Nothing To Update')

    with psycopg2.connect(SQL_CONNECTION) as conn:
        cursor = conn.cursor()

        update_values = [ad_info[key] for key in update_keys]

        set_string = ', '.join(['{} = %s'.format(key) for key in update_keys])

        sql = '''
update ads a 
    set {set}
    from ads b
    where a.id = b.id and a.id = %s
    returning {return_a}, {return_b}
'''.format(set=set_string,
           return_a=Ad.select_fields('a'),
           return_b=Ad.select_fields('b'),
           )

        update_values.append(_id)
        cursor.execute(sql, update_values)

        row = cursor.fetchone()

        if row is None:
            raise InobiException('Ad with identifier({}) does not exits or have been removed earlier'.format(_id))

        fl = len(Ad._fields)

        new_ad = Ad._make(row[:fl])
        old_ad = Ad._make(row[fl:])

        if clean_media and not old_ad.source.startswith('!'):
            from ..utils import remove_source
            if not remove_source(old_ad.source):
                log_to_file(tag,
                            'ERROR:',
                            'Removing source from media to temp folder failed. Ad_id: {}, Source: {}.'
                            .format(_id, old_ad.source)
                            )

        return new_ad, old_ad


def get_ads_list(ad_id='all') -> T.List[Ad]:

    valid_uuid = is_valid_uuid(ad_id)
    is_all_required = not valid_uuid

    with psycopg2.connect(SQL_CONNECTION) as conn:

        cursor = conn.cursor()

        if is_all_required:
            sql = 'select {select} from ads order by created desc'.format(select=Ad.select_fields())
            cursor.execute(sql)
        else:
            sql = 'select {select} from ads where id = %s'.format(select=Ad.select_fields())
            cursor.execute(sql, (ad_id, ))

        rows = [Ad._make(row) for row in cursor]

        if not is_all_required and len(rows) == 0:
            raise InobiException('Ad with identifier({}) does not exits or have been removed earlier'.format(ad_id))

        return rows


def disable_ad(ad_id: str, delete=False) -> Ad:

    ad_id = str(ad_id)

    if not is_valid_uuid(ad_id):
        raise InobiException('Ad Identifier Forbidden or Incorrect')

    with psycopg2.connect(SQL_CONNECTION) as conn:

        cursor = conn.cursor()

        if delete:
            sql = 'delete from ads where id = %s returning {return_}'.format(return_=Ad.select_fields())

            cursor.execute(sql, (ad_id, ))

        else:

            sql = 'update ads set enabled = false where id = %s returning {return_}'.format(return_=Ad.select_fields())

            cursor.execute(sql, (ad_id, ))

        row = cursor.fetchone()

        if row is None:
            raise InobiException('Ad with identifier({}) does not exist or already have been removed earlier'.format(ad_id))

        ad = Ad._make(row)

        if delete:
            from ..utils import remove_source
            if not remove_source(ad.source):
                log_to_file(tag,
                            'ERROR:',
                            'Removing source from media to temp folder failed. Ad_id: {}, Source: {}.'
                            .format(ad_id, ad.source)
                            )

        return ad
