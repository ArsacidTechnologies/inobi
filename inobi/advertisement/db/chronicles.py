
import typing as T

from collections import namedtuple
from json import loads, dumps

import psycopg2

from . import SQL_CONNECTION
from . import InobiException
from . import is_valid_uuid, purge_uuid, DbKey, REQUEST_NULLABLES
from . import debug_exception
from ..utils.stats import parse_device_from_ua


REQUEST_REQUIREMENTS = [
    DbKey.AD_ID, DbKey.CLIENT_MAC, DbKey.TIME,
    DbKey.USER_AGENT, DbKey.BOX_MAC, DbKey.LAT,
    DbKey.LNG, DbKey.CHRONICLES
]


tag = '@Database.Chronicles:'


from .classes import Chronicle


def get_chronicles(offset=0, limit='none', date_from=None, date_to=None, ad_id=None) -> T.Tuple[T.List, T.Tuple[float, float]]:

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
            ad_id_sql = 'ad_id IN {}'.format( str(ad_id).replace('[', '(').replace(']', ')') )
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
select {fields} from (
    select *, row_number() over (order by time) as row 
        from {table}
        where time > %s and time <= %s {ids_filter}
) a {slice_filter}
'''.format(fields=', '.join(f for f in Chronicle._fields),
           table='chronicles',
           ids_filter=ad_id_sql if ad_id else '',
           slice_filter='where row >= %s and row <= %s' if limited else '',
           )


            # sql = (" SELECT CONVERT([varchar](max), [ad_id]) AS [ad_id], [client_mac], "
            #        "    [time], [device], [box_mac], [lat], [lng], [redirected], [events] FROM ( "
            #        "        SELECT [ad_id], [client_mac], [time], [device], "
            #        "           [box_mac], [lat], [lng], [redirected], [events], ROW_NUMBER() "
            #        "            OVER (ORDER BY [time]) AS [row] "
            #        "            FROM [{}] "
            #        "            WHERE time > ? AND time <= ? {} "
            #        ") a {} "
            #        " ORDER BY [time] DESC ").\
            #     format('chronicles', 'AND {}'.format(ad_id_sql) if ad_id else '', 'WHERE [row] >= ? AND [row] <= ?' if limited else '')

            params = [date_from, date_to]
            if limited:
                params.extend([range_from, range_to])

            cursor.execute(sql, params)

            chronicles = [Chronicle.make_from_query(row)._asdict() for row in cursor]

            return chronicles, (date_from, date_to)
        finally:
            if cursor is not None:
                cursor.close()
    finally:
        if connection is not None:
            connection.close()
