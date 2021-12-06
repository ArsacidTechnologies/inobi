################
# AD STATS API #
################
from time import time as timestamp
from collections import Counter

import psycopg2

from . import SQL_CONNECTION

from ..exceptions import InobiException
from ..utils import debug_exception, is_valid_uuid, humanize_time
from ..utils.stats import getdays, KEY_START, KEY_END, KEY_TOTAL, KEY_UNKNOWN
from .classes import Ad, Chronicle

import enum

tag = '@Database.Stats:'

INTERVAL_ONE_MONTH = 30 * 24 * 60 * 60

KEY_STANDARDIZE = 'standardize'

ANDROID = 'android'
IPHONE = 'iphone os'
IPAD = 'ipad; cpu os'

JOIN_IOSES = True

DTYPE_LABELS = {
    ANDROID: 'Android',
    IPHONE: 'iPhone' if not JOIN_IOSES else 'iOS',
    IPAD: 'iPad',
}

DEV_TYPES_DELIMITERS_PACK = ((ANDROID, ';', '.'), (IPHONE, ' ', '_'), (IPAD, ' ', '_'))


class StatsType(enum.Enum):
    ADVERTISEMENT = 'advertisement'
    TRANSPORT = 'transport'


def count_device(device, bundle):
    if device is None:
        return
    lowered = device.lower()
    dev = version = KEY_UNKNOWN
    for dtype, delimiter, v_delimiter in DEV_TYPES_DELIMITERS_PACK:
        if dtype in lowered:
            _i = lowered.index(dtype) + len(dtype) + 1
            dev = dtype
            if JOIN_IOSES and dtype is IPAD:
                dev = IPHONE
            _version = lowered[_i:lowered.find(delimiter, _i, _i + 9)]
            if v_delimiter in _version:
                version = _version
            break

    if dev not in bundle:
        bundle[dev] = {}

    if version not in bundle[dev]:
        bundle[dev][version] = 1
    else:
        bundle[dev][version] += 1


def summarize_devices(bundle):
    summary = {
        KEY_UNKNOWN: {}
    }
    for dtype, _, version_delimiter in DEV_TYPES_DELIMITERS_PACK:
        if JOIN_IOSES and dtype is IPAD:
            break
        dtsum = {}
        if dtype in bundle:
            total = 0
            for ver, count in bundle[dtype].items():
                total += count
                minor_v = ver[:ver.find(version_delimiter)] if ver != KEY_UNKNOWN else ver
                if minor_v not in dtsum:
                    dtsum[minor_v] = count
                else:
                    dtsum[minor_v] += count
            dtsum[KEY_TOTAL] = total

            for version, count in dtsum.items():
                if version == KEY_TOTAL:
                    continue
                _ratio = (count / total) * 100
                # dtsum[version] = {
                #     'num': count,
                #     'ratio': round(_ratio, 3)
                # }
                dtsum[version] = '{} ({:.1f}%)'.format(count, _ratio)

        summary[DTYPE_LABELS.get(dtype, dtype)] = dtsum

    if KEY_UNKNOWN in bundle:
        summary[KEY_UNKNOWN][KEY_TOTAL] = bundle[KEY_UNKNOWN][KEY_UNKNOWN]

    s = sum([t.get(KEY_TOTAL, 0) for t in summary.values()])
    for dtype, _stats in summary.items():
        total = _stats.get(KEY_TOTAL, 0)
        _ratio = (total / s) * 100
        summary[dtype][KEY_TOTAL] = {
            'count': total,
            'ratio': round(_ratio, 3)
        }
        # summary[dtype][KEY_TOTAL] = '{} ({:.3f}%)'.format(total, _ratio)

    return {
        'raw': bundle,
        'summary': summary
    }


def count_clientmac(mac, cmacs):
    if mac in cmacs:
        cmacs[mac] += 1
    else:
        cmacs[mac] = 1


def summarize_views(cmacs, group_above=5, **kwargs):
    counts = list(cmacs.values())
    total = sum(counts)
    uniques = len(counts)

    view_counts = {
        vc: counts.count(vc)
        for vc in set(counts)
    }

    _vc = {}

    aboves = []
    _ratio_above = 0
    for count, nums in view_counts.items():
        _ratio = (nums / uniques) * 100
        # view_counts[count] = {
        #     'nums': nums,
        #     'ratio': round(_ratio, 3)
        # }
        if count < group_above:
            _vc[str(count)] = '{} ({:.1f}%)'.format(nums, _ratio)
        else:
            aboves.append(count)
            _ratio_above += _ratio

    _vc['{}+'.format(group_above)] = '{} ({:.1f}%)'.format(
        sum(view_counts.pop(count) for count in aboves),
        _ratio_above
    )

    uv_ratio = uniques / total
    vpd = kwargs['day_average']

    return {
        'general': _vc,
        KEY_TOTAL: total,
        'uniques': uniques,
        'uniques_per_day': round(uv_ratio * vpd, 3),
        'uniques_per_week': round(uv_ratio * vpd * 7, 3),
    }


def count_viewtime(dt, times_bundle):
    date = dt.date()
    if date not in times_bundle:
        times_bundle[date] = {}

    hour = dt.hour
    if hour not in times_bundle[date]:
        times_bundle[date][hour] = 1
    else:
        times_bundle[date][hour] += 1


def summarize_viewtimes(times_bundle):
    daily_summary = {}
    monthly_summary = {}

    days = 0

    for date, _hours in times_bundle.items():
        days += 1

        days_sum = 0
        for hour, views in _hours.items():
            days_sum += views
            # hour = str(hour)

            if hour < 6:
                hour = 6
            if hour > 21:
                hour = 21

            if hour not in daily_summary:
                daily_summary[hour] = views
            else:
                daily_summary[hour] += views

        monthly_summary[str(date)] = days_sum

    daily_average = 0
    for hour, views in daily_summary.items():
        average = round(views / days, 3)
        daily_average += average
        daily_summary[hour] = average

    daily_average = round(daily_average, 3)

    return dict(daily=daily_summary, in_interval=monthly_summary), \
           dict(days=days, views_per_day=daily_average, views_per_week=daily_average * 7)


def count_transport(transport, bundle):
    if transport not in bundle:
        bundle[transport] = 1
    else:
        bundle[transport] += 1


def summarize_transport(transports):
    tlen = len(transports)
    views = sum(transports.values())
    return dict(
        # raw=transports,
        total={
            'views': views,
            'transports': tlen,
            'average': round(views / tlen, 3),
        }
    )


FETCH_ROWS_COUNT = 200
FETCH_BY_ONE = False
INTERVAL_MAX_DAYS = 90


def ad_stats(ads, interval=None, stats_type: StatsType = StatsType.TRANSPORT, **kwargs):
    from datetime import datetime

    if not ads:
        raise InobiException('Ads Parameter Must Present And Be Correct (not null, not empty list, etc.)')

    all = False
    if isinstance(ads, str) and ads.lower() == 'all':
        all = True
    elif not isinstance(ads, list):
        try:
            ads = list(ads)
        except:
            raise InobiException('Incorrect Ads Parameter ({}). Must be a List or \'ALL\''.format(ads))

    now = timestamp()
    start = now - INTERVAL_ONE_MONTH
    if not isinstance(interval, dict):
        interval = {
            KEY_START: start,
            KEY_END: now,
        }

    if not interval.get(KEY_END):
        raise InobiException("Incorrect Interval Parameter('{}' is absent)".format(KEY_END))

    if not interval.get(KEY_START):
        raise InobiException("Incorrect Interval Parameter('{}' is absent)".format(KEY_START))

    if interval.get(KEY_STANDARDIZE, True):
        interval[KEY_START] = datetime.fromtimestamp(interval[KEY_START]). \
            replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        interval[KEY_END] = datetime.fromtimestamp(interval[KEY_END]). \
            replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    if not all:
        for i, ad in enumerate(ads):
            vuuid = is_valid_uuid(ad)
            if not vuuid:
                raise InobiException("Incorrect Ad Id ('{}')".format(ad))
            else:
                ads[i] = vuuid

    falsify = kwargs.get('falsify', False)
    falsify_factor = kwargs.get('falsify_factor', 1)
    with_magic = kwargs.get('with_magic', False)
    magic_props = kwargs.get('magic_props', None)

    user_retention_group_above = kwargs.get('user_retention_group_above', 10)

    if with_magic:
        try:
            magic_props = {
                int(k): v
                for k, v in magic_props.items()
            }
        except Exception as e:
            raise InobiException('Magic Properties Incorrect ({})'.format(e))

    connection = psycopg2.connect(SQL_CONNECTION)
    try:

        cursor = connection.cursor()
        try:
            stats = {}
            devices = {}
            cmacs = {}
            time_bundle = {}
            transports = {}
            _redirect = Counter()

            sql_params = ', '.join(['%s' for _ in ads])

            if all:
                sql = 'SELECT {select} FROM ads'.format(select=Ad.select_fields(),
                                                        )
                cursor.execute(sql)
            else:
                sql = 'SELECT {select} FROM ads WHERE id in ({ads})'.format(select=Ad.select_fields(),
                                                                            ads=sql_params,
                                                                            )
                cursor.execute(sql, ads)

            ad_rows = cursor.fetchall()
            _ad_infos = []
            for _ad in ad_rows:
                _ad_infos.append(Ad._make(_ad))

            _created = min([ad.created for ad in _ad_infos])
            if _created > interval[KEY_START]:
                interval[KEY_START] = _created

            _interval = dict(interval)

            from datetime import datetime
            days = getdays(interval)
            if kwargs.get('force') and days > INTERVAL_MAX_DAYS:
                raise InobiException('Interval Too Large (actual:{}, max:{}. Use \'force\' parameter)'. \
                                     format(days, INTERVAL_MAX_DAYS)
                                     )
            _interval.update({
                KEY_START + '(human)': humanize_time(_interval[KEY_START]),
                KEY_END + '(human)': humanize_time(_interval[KEY_END]),
                'days': days,
                'weeks': round(days / 7, ndigits=2),
            })

            found = [(dict(**ad._asdict()), ad.getid()) for ad in _ad_infos]
            for ad, _id in found:
                ad['id'] = _id

            stats['request'] = {
                'interval': _interval,
                'requested': ads,
                'found': [ad for ad, _ in found],
            }

            if not all:
                sql = '''
                    select {select} from chronicles 
                    where ad_id in ({ads}) and time >= {start} and time <= {end}
                    and ads_device_id is {stats_type_not} null
                '''.format(select=Chronicle.select_fields(),
                           ads=sql_params,
                           stats_type_not='' if stats_type is StatsType.TRANSPORT else 'not',
                           **interval)
            else:
                sql = '''
                    select {select} from chronicles
                    where time >= {start} and time <= {end}
                    and ads_device_id is {stats_type_not} null
                '''.format(select=Chronicle.select_fields(),
                           stats_type_not='' if stats_type is StatsType.TRANSPORT else 'not',
                           **interval)

            _sql_start = timestamp()
            if all:
                cursor.execute(sql)
            else:
                cursor.execute(sql, ads)

            def _count_row(row, falsify, falsify_factor, with_magic, magic_props):
                chronicle = Chronicle._make(row)

                if with_magic:
                    falsify = True
                    falsify_factor = 1
                    for factor, interval in magic_props.items():
                        _istart, _iend = interval
                        if _istart < chronicle.time <= _iend:
                            falsify_factor = factor
                            break

                for _i in range(falsify_factor if falsify else 1):
                    count_transport(chronicle.box_mac, transports)
                    count_device(chronicle.device, devices)
                    count_viewtime(datetime.fromtimestamp(chronicle.time), time_bundle)
                    count_clientmac(chronicle.client_mac if not falsify else '{}{}'.format(chronicle.client_mac, _i),
                                    cmacs)

            if FETCH_BY_ONE:
                row = cursor.fetchone()
                while row:
                    _count_row(row, falsify, falsify_factor, with_magic, magic_props)
                    row = cursor.fetchone()
            else:
                rows = cursor.fetchmany(FETCH_ROWS_COUNT)
                while rows:
                    for row in rows:
                        _count_row(row, falsify, falsify_factor, with_magic, magic_props)
                    rows = cursor.fetchmany(FETCH_ROWS_COUNT)

            # REDIRECT STATS

            if all:
                sql = '''
                    select redirected from chronicles 
                    where time >= {start} and time <= {end}
                    and ads_device_id is {stats_type_not} null
                '''.format(
                    stats_type_not='' if stats_type is StatsType.TRANSPORT else 'not',
                    **interval
                )
            else:
                sql = '''
                    select redirected from chronicles 
                    where ad_id IN ({ads}) and time >= {start} and time <= {end}
                    and ads_device_id is {stats_type_not} null
                '''.format(
                    ads=sql_params,
                    stats_type_not='' if stats_type is StatsType.TRANSPORT else 'not',
                    **interval
                )

            if all:
                cursor.execute(sql)
            else:
                cursor.execute(sql, ads)

            if FETCH_BY_ONE:
                row = cursor.fetchone()
                while row:
                    _redirect[row[0]] += 1
                    row = cursor.fetchone()
            else:
                rows = cursor.fetchmany(FETCH_ROWS_COUNT)
                while rows:
                    for row in rows:
                        _redirect[row[0]] += 1
                    rows = cursor.fetchmany(FETCH_ROWS_COUNT)

            rsum = sum(_redirect.values())
            redirect = {
                'count': rsum,
                'ratio': round(100 * (_redirect[True] / rsum), 3),
                'raw': _redirect,
            }

            _sql_end = timestamp()

            timeaverage_sum = summarize_viewtimes(time_bundle)
            d_average = timeaverage_sum[-1]['views_per_day']

            stats.update({
                'uniqueness': summarize_views(cmacs, day_average=d_average, group_above=user_retention_group_above),
                'devices': summarize_devices(devices),
                'time_average': timeaverage_sum,
                'transport': summarize_transport(transports),
                'redirect': redirect,

                'timings': {
                    'sql_fetch': _sql_end - _sql_start,
                    'analize_time': timestamp() - _sql_end,
                }
            })

            return stats
        finally:
            if cursor is not None:
                cursor.close()
    finally:
        if connection is not None:
            connection.close()


def test():
    from json import dumps, loads
    from datetime import datetime

    now = timestamp()
    dt = datetime.fromtimestamp(now).replace(month=5, day=11, hour=0, minute=0, second=0, microsecond=0)
    ads = [
        [
            'MegaCom',
            (1491760800.0, 1494439200.0),
            '7e0ae70a-1947-4b8f-a641-1b852f813ee3',
            'a2bdd2cf-9ada-4247-8f05-44ccff2dd95d',
        ],
        [
            'Optima',
            (1492452000, 1495130400),
            '2f7abdec-c16f-45c3-91dc-849476f2685f',
            'c2c4c6f3-e8fd-4535-93cb-e8c2c1a209d2',
        ],
        [
            'O!',
            (1490682929, 1492660962.7854202),
            '117acf79-3a86-4032-8647-da46df9fbacf',
            'b6bce739-012e-4b96-b3d5-b76f9be9a556',
        ],
        [
            'TEZ',
            (1491760800.0, 1494439200.0),
            '2443e2d1-6a7f-4345-91c6-cd4e28a639c8',
            '399b8513-72db-4895-b18c-cdcbdf31abb4',
            '0640dc36-60bb-4f71-8147-d272243347ae',
        ]
    ]
    end = dt.replace(month=dt.month - 1).timestamp()

    dt = datetime.fromtimestamp(1492452000.493491)
    end = 1495130400.493491

    target = None
    magicality_target = None

    magic_props = {}

    _interval = {
        KEY_STANDARDIZE: False,
        KEY_START: dt.timestamp(),
        KEY_END: end,
    }

    def get_interval():
        return {
            k: v
            for k, v in _interval.items()
        }

    ALL = True
    GROUPED = True

    from ..utils.stats import generatereport

    # for GROUPED, ALL in [(False, False), (True, False)]:
    for GROUPED, ALL in [(False, True)]:
        if ALL:
            date = datetime.fromtimestamp(1495205492)
            interval = {
                'start': date.replace(month=date.month - 1).timestamp(),
                'end': date.timestamp()
            }
            stats = dumps(ad_stats('ALL', interval=interval), indent=2, sort_keys=True)
            f = open(
                '/home/dev/Desktop/stats/ALL({0.year}-{0.month:02d}-{0.day:02d}).txt'.format(date),
                mode='w',
                newline='\r\n'
            )
            f.write(stats)
            f.flush()
            f.close()
            print('{0.year}-{0.month:02d}'.format(date), 'ALL', 'finished')
        else:
            __stats_request_props = dict(
                # interval=get_interval(),
                with_magic=bool(magicality_target),
                magic_props=magic_props
            )
            if GROUPED:
                for _ads in ads:
                    name, times, *__ads = _ads
                    interval = dict(start=times[0], end=times[1])
                    if target and _ads[0] != target:
                        continue
                    _stats = ad_stats(__ads, interval=interval, **__stats_request_props)
                    stats = dumps(_stats, indent=2, sort_keys=True)
                    fname = 'GROUPED.{}'.format(dumps(name))
                    fpath = '/home/dev/Desktop/stats/{}'.format(fname)
                    f = open(
                        fpath + '.txt',
                        mode='w',
                        newline='\r\n'
                    )
                    f.write(stats)
                    f.flush()
                    f.close()
                    print(
                        '\tReport generated to file:',
                        generatereport(_stats, filepath='{}.xlsx'.format(fpath))
                    )
                    print(_ads[0], 'finished')
            else:
                for _ads in ads:
                    if target and _ads[0] != target:
                        continue
                    name, times, *__ads = _ads
                    interval = dict(start=times[0], end=times[1])
                    for ad in __ads:
                        _stats = ad_stats([ad, ], interval, **__stats_request_props)
                        stats = dumps(_stats, indent=2, sort_keys=True)
                        fname = '{}({})'.format(_stats['request']['found'][0]['title'], ad)
                        fpath = '/home/dev/Desktop/stats/{}'.format(fname)
                        f = open(
                            fpath + '.txt',
                            mode='w',
                            newline='\r\n'
                        )
                        f.write(stats)
                        f.flush()
                        f.close()
                        print(
                            '\tReport generated to file:',
                            generatereport(_stats, filepath='{}.xlsx'.format(fpath))
                        )
                        print(fname, ad, 'finished')


def test2():
    props = {
        "ads": [
            "8201e486-6cc5-4048-9e7f-9482b7893124",
            "0640dc36-60bb-4f71-8147-d272243347ae",
            "2443e2d1-6a7f-4345-91c6-cd4e28a639c8"
        ],
        "interval": {
            "start": 1493696180.325,
            "end": 1496288180.325
        }
    }
    stats = ad_stats(**props)
    print(stats)
