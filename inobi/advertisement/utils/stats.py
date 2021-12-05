from uuid import UUID

from datetime import datetime
from collections import namedtuple

from . import purge_uuid
from ..exceptions import InobiException


tag = '@Utils.Stats:'


KEY_TOTAL = 'total'
KEY_START = 'start'
KEY_END = 'end'
KEY_UNKNOWN = 'unknown'

INOBI_DAY_START_HOUR = 6
INOBI_DAY_END_HOUR = 21

INTERVAL_HOUR = 60*60
INTERVAL_DAY = 24*INTERVAL_HOUR
INTERVAL_INOBI_DAY = (INOBI_DAY_END_HOUR - INOBI_DAY_START_HOUR) * INTERVAL_HOUR


from inobi.utils import device_description_from_user_agent as parse_device_from_ua


def getday(ts, atop=True):
    d = datetime.fromtimestamp(ts)
    dstart = d.replace(hour=INOBI_DAY_START_HOUR, minute=0, second=0, microsecond=0)
    if ts < dstart.timestamp():
        return 0, d
    dend = dstart.replace(hour=INOBI_DAY_END_HOUR)
    dets = dend.timestamp()
    if ts > dets:
        return 1, d

    return (dets-ts if atop else ts-dets)/INTERVAL_INOBI_DAY, d


def getdays(interval):

    start = interval[KEY_START]
    end = interval[KEY_END]

    if start >= end:
        raise InobiException("'start' Must Be Lower Than 'end' In 'interval' Parameter")

    ds, sdt = getday(start, atop=True)
    de, edt = getday(end, atop=False)

    if sdt.date() == edt.date():
        return ds

    return round((edt-sdt).total_seconds()/INTERVAL_DAY, ndigits=2)


def debug(d):
    from json import dumps
    print(dumps(d, indent=2, sort_keys=True))


def humanizedictkey(key):
    if '_' in key:
        words = key.split('_')
    else:
        words = [key,]

    return ' '.join([str(word).capitalize() for word in words])


def intify(s, default=None, try_hard=False):
    try:
        return int(s)
    except:
        if try_hard:
            out = ''.join([c for c in s if c in '0123456789'])
            return int(out) if len(out) > 0 else (s if default is None else default)
        return s if default is None else default


def appendtosheet(sheet, row, title=None, paste_empties=1):
    if isinstance(paste_empties, int):
        for _ in range(paste_empties):
            sheet.append(())
    sheet.append(row)


class Style:

    NORMAL = 'normal'
    TITLE = 'header'
    SUBTITLE = 'subheader'
    ANNOTATION = 'annotation'
    TABLE_HEADER = 'table_header'

    from openpyxl.styles import NamedStyle, Font

    _styles = {
        NORMAL: NamedStyle(name=NORMAL, font=Font(name='Helvetica')),
        TITLE: NamedStyle(name=TITLE, font=Font(name='Helvetica', bold=True, size=13)),
        SUBTITLE: NamedStyle(name=SUBTITLE, font=Font(name='Helvetica', size=11, bold=True)),
        ANNOTATION: NamedStyle(name=ANNOTATION, font=Font(name='Helvetica', size=10, bold=True, italic=True)),
        TABLE_HEADER: NamedStyle(name=TABLE_HEADER, font=Font(name='Helvetica', size=10, bold=True))
    }

    @staticmethod
    def init_workbook(wb):
        for name, style in Style._styles.items():
            wb.add_named_style(style)


def generatereport(stats, filename='report.xlsx', **kwargs):
    from openpyxl import Workbook
    from openpyxl.cell import Cell
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.utils import coordinate_from_string
    from os.path import join
    from . import get_directory
    from datetime import datetime as datetime, date

    wb = Workbook()
    _sheet = wb.active

    Style.init_workbook(wb)

    filepath = kwargs.get('filepath', join(get_directory('temp'), filename))

    _original_append = _sheet.append
    def _styled_append(iterable, style=Style.NORMAL):
        if not style:
            return _styled_append(iterable=iterable, style=Style.NORMAL)
        cells = []
        for val in iterable:
            cell = Cell(worksheet=_sheet, value=val)
            cell.style = style
            if isinstance(val, str) and val[-1] == '%':
                try:
                    cell.value = cell._cast_percentage(val)
                    cell.number_format = '0.0%'
                except:
                    pass
            if isinstance(val, (datetime, date)):
                cell.value = cell._cast_datetime(val)
            cells.append(cell)
        _original_append(cells)
        return cells
    _sheet.append = _styled_append
    append = _sheet.append

    # AD INFO
    append(())
    append(())
    append(('Report for ads:',), style=Style.TITLE)
    append(('Title', 'Description', 'Created', 'Redirect to', 'Media Type', 'Duration'), style=Style.TABLE_HEADER)
    for ad in stats['request']['found']:
        append([ad['title'], ad.get('description', '-'), datetime.fromtimestamp(ad['created']), ad['redirect_url'], ad['type'], ad['duration']])

    # AVERAGES
    averages, total = stats['time_average']
    interval_views = averages['in_interval']
    days = total['days']
    # _start = _end = None

    append(())
    append(())
    append(('Views',), style=Style.TITLE)
    append(('Date', 'Views'), style=Style.TABLE_HEADER)
    for i, (_date, counts) in enumerate(sorted(interval_views.items(), key=lambda x: intify(x[0]))):
        cells = append((datetime.strptime(_date, '%Y-%m-%d').date(), counts))
    #     if i == 0:
    #         cell = cells[0]
    #         _start = (cell.column, cell.row)
    #     if i == len(interval_views)-1:
    #         cell = cells[-1]
    #         _end = (cell.column, cell.row)
    # ref = Reference(
    #     worksheet=_sheet,
    #     range_string='{}!{}{}:{}{}'.format(_sheet.title, *_start, *_end)
    # )
    # print(ref)
    # chart = BarChart()
    # chart.add_data(ref, from_rows=True, titles_from_data=True)
    # _sheet.add_chart(chart, 'D{}'.format(_start[1]))

    append(())
    append(('Days:', days), style=Style.ANNOTATION)
    append(('Total:', stats['uniqueness']['total']), style=Style.ANNOTATION)
    append(('Average per week:', total['views_per_week']), style=Style.ANNOTATION)
    append(('Average per day:', total['views_per_day']), style=Style.ANNOTATION)

    # daily
    append(())
    append(('Daily',), style=Style.SUBTITLE)
    append(('Hour', 'Views'), style=Style.TABLE_HEADER)
    for hour, counts in sorted(averages['daily'].items(), key=lambda x: intify(x[0])):
        append((int(hour), counts))

    # uniqueness
    uniqueness = stats['uniqueness']

    append(())
    append(('Uniques',), style=Style.SUBTITLE)
    append(('Number of views', 'Count', '%'), style=Style.TABLE_HEADER)
    for num_of_views, user_count in sorted(stats['uniqueness']['general'].items(), key=lambda x: intify(x[0], try_hard=True)):
        count, ratio = user_count.split()
        append((num_of_views, int(count), ratio[1:-1]))

    append(())
    append(('Total:', uniqueness['uniques']), style=Style.ANNOTATION)
    append(('Uniques per week:', uniqueness['uniques_per_week']), style=Style.ANNOTATION)
    append(('Uniques per day:', uniqueness['uniques_per_day']), style=Style.ANNOTATION)

    # DEVICES
    devices = stats['devices']['summary']

    append(())
    append(())
    append(('Devices',), style=Style.TITLE)
    for dtype, dstats in sorted(devices.items()):
        total = dstats[KEY_TOTAL]
        append(())
        append((dtype,), style=Style.TABLE_HEADER)
        if len(dstats) > 1:  # other stats goes here
            for version, counts in sorted(dstats.items(), key=lambda x: intify(x[0], 999)):
                if version == KEY_TOTAL:
                    continue
                count, ratio = counts.split()
                append(('{}{}'.format(version, '.x' if version != KEY_UNKNOWN else ''), int(count), ratio[1:-1]))
        append(('Total:', total['count']), style=Style.ANNOTATION)
        append(('% of all views:', '{}%'.format(total['ratio'])), style=Style.ANNOTATION)

    dims = _sheet.column_dimensions
    dims['A'].width = 15
    dims['B'].width = 20
    dims['C'].width = 17.5
    dims['D'].width = 13
    dims['E'].width = dims['F'].width = 10

    wb.save(filepath)

    return filename if 'filepath' not in kwargs else filepath


def test_generatereport():
    from json import loads, dumps
    f = open('/home/dev/Desktop/stats/test.stats')
    json = f.read()
    testdata = loads(json)
    f.close()

    # print(dumps(testdata['devices'], sort_keys=True, indent=2))

    fname = generatereport(testdata)

    from . import get_directory

    print('Done. Filename: {0}, directory: {1}'.format(fname, get_directory('temp')))
