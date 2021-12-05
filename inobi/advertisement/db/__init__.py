
import psycopg2 as pyodbc
import psycopg2 as pypyodbc

import psycopg2

from inobi.config import SQL_CONNECTION

from ..exceptions import InobiAdsException as InobiException
from ..utils import debug_exception, log_to_file, purge_uuid, is_valid_uuid
from .classes import Ad


tag = '@Database:'


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

AD_TYPES = ["banner", "video", "iframe"]

__listable_tables__ = {
    'views': 'ad_view',
    'requests': 'request',
    'chronicles': 'chronicles',
}


REQUEST_REQUIREMENTS = [DbKey.AD_ID, DbKey.CLIENT_MAC, DbKey.TIME, DbKey.USER_AGENT, DbKey.BOX_MAC, DbKey.LAT, DbKey.LON]
REQUEST_NULLABLES = [DbKey.CLIENT_MAC, DbKey.USER_AGENT, DbKey.LAT, DbKey.LON]


def log_request(**kwargs):

    values = []
    for key in REQUEST_REQUIREMENTS:
        if key not in kwargs and key not in REQUEST_NULLABLES:
            raise InobiException('Could not log request. ({}) is Missing'.format(key))
        else:
            values.append(kwargs.get(key, None))

    connection = pyodbc.connect(SQL_CONNECTION)
    try:
        cursor = connection.cursor()
        try:
            sql = ('INSERT INTO [request] ('
                   '[ad_id], [client_mac], [time], [user_agent], [box_mac], [lat], [lon]'
                   ') VALUES (CONVERT(uniqueidentifier, ?), ?, ?, ?, ?, ?, ?)')

            cursor.execute(sql, values)

            cursor.commit()
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            print(tag, 'error inserting:', e)
        finally:
            if cursor is not None:
                cursor.close()
    except Exception as e:
        debug_exception(tag, e, to_file=True)
        print(tag, 'error opening connection:', e)
    finally:
        if connection is not None:
            connection.close()
