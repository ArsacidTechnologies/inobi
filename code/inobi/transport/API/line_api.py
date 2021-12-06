from inobi.config import SQL_CONNECTION
from inobi.transport.DataBase.line_db import get_list_routes, get_route, get_platform_routes as get_platform_routes_db, \
    get_list_routes_with_excluded
from werkzeug.utils import secure_filename
from inobi.transport.configs import LINE_DB_DIRECTORY
from os.path import join
from ..DataBase.migrate import migrate as update
from ..DataBase.DB import verify_sqlite
import os
from pathlib import Path
import json
from collections import namedtuple





def upload(file):
    filename = secure_filename(file.filename)
    exist = False
    try:
        file_index = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'r')
        versions = json.loads(file_index.read())
        exist = True
    except:
        file_index = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'w')
        versions = dict(latest=0, files={}, current='')

    if exist:
        file_index.close()
        file_index = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'w')
    ver = versions['latest']
    filename = '{}_{}'.format(ver + 1, filename)

    db_path = join(LINE_DB_DIRECTORY, filename)
    file.save(db_path)
    response = verify_sqlite(db_path)
    if response['code'] != 200:
        os.remove(db_path)
        return response

    versions['files'][ver + 1] = filename
    versions['latest'] = ver + 1

    file_index.write(json.dumps(versions))
    file_index.close()
    return response

def migrate(filename):
    db_path = join(LINE_DB_DIRECTORY, filename)
    if not Path(db_path).is_file():
        return dict(code=400, message="{} does not exist".format(filename))
    file_index = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'r')
    versions = json.loads(file_index.read())
    file_index.close()
    file_index = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'w')
    versions['current'] = filename.split('_')[0]
    file_index.write(json.dumps(versions))

    res = update(db_path)
    file_index.close()


    return res

def listdirection():
    sqlite_db = namedtuple('sqlite_db', 'ver, filename, dir')
    try:
        file = open('{}/ver.index'.format(LINE_DB_DIRECTORY), 'r')
    except:
        return dict(code=404, message='no file')
    versions = json.loads(file.read())
    file.close()
    l = []
    if isinstance(versions, dict):
        for ver, file in versions['files'].items():
            l.append(sqlite_db(ver, file, LINE_DB_DIRECTORY))
    l.sort(reverse=True, key=lambda x: x.ver)

    return dict(code=200, data=dict(files=l, latest=versions['latest'], current=versions['current']))

def list_(exclude=False):
    if exclude:
        response = get_list_routes_with_excluded()
    else:
        response = get_list_routes()
    if response['code'] != 200:
        return response

    return response

def get_line(data):
    id = data['id']
    response = get_route(id)
    if response['code'] != 200:
        return response

    return response

def get_lines(data):
    lines = []
    for id in data['id']:
        line = get_route(id)
        if line['code'] != 200:
            return line
        lines.append(line['data'])
    return dict(code=200, data=lines, message='OK')

# def get_platforms(self, startPoint, endPoint):
#     locations = []
#     locations.append(startPoint['lat'])
#     locations.append(startPoint['lng'])
#     locations.append(endPoint['lat'])
#     locations.append(endPoint['lng'])
#     platforms = lineDB.get_platforms_on_scale(tuple(locations))
#     if platforms['code'] != 200:
#         if platforms['code'] == 404:
#             platforms['message'] = 'platforms do not found'
#         return platforms
#
#     return platforms

def get_platform_routes(platform_id):
    routes = get_platform_routes_db(platform_id)

    return routes

