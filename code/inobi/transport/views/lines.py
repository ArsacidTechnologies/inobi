from inobi.transport.configs import __url_line, scope, _PREFIX, LINE_DB_DIRECTORY

from inobi.transport import route
from flask import request, send_from_directory, redirect
from ..API.line_api import upload, listdirection, migrate, list_, get_lines, get_line, get_platform_routes
from inobi.utils import http_err, http_ok, getargs
from inobi.security import secured, scope as sscope

from flask_cors import cross_origin


@route(__url_line['upload'], methods=['GET', 'POST'])
@secured(scope['admin'])
def uploadd():

    if request.method == 'POST':
        if 'file' not in request.files:
            return http_err(message='file not sent', status=400)
        file = request.files['file']
        if file.filename == '':
            return http_err(message='No selected file', status=400)
        response = upload(file)
        if response['code'] != 200:
            return http_err(message=response['message'], status=response['code'])
        return redirect('/transport/line/update?jwt={}'.format(uploadd._token))
    return '''
           <!doctype html>
           <title>Upload line database</title>
           <h1>Upload line database</h1>
           <p>upload sqlite3 database file with tables</p>
           <ul>
           <li>stations</li>
           <li>platforms</li>
           <li>routes</li>
           <li>directions</li>
           <li>station_platforms</li>
           <li>station_routes</li>
           <li>route_directions</li>
           <li>direction_platforms</li>
           <li>exclude_routes</li>
           </ul>
           <form method=post enctype=multipart/form-data>
             <p><input type=file name=file>
                <input type=submit value=Upload>
           </form>
           '''


@route(__url_line['migrate'], methods=['GET'])
@secured(scope['admin'])
def choose_to_migtare():
    files = listdirection()
    if files['code'] != 200:
        return http_err(files['message'], status=files['code'])
    collection = ''
    latest = files['data']['latest']
    current = files['data']['current']
    for file in files['data']['files']:

        s = '''<tr><td>{V}</td>
                <td>{file}</td>
                <td><a href="{prefix}{dir}/{file}?jwt={token}">update</a><td>
                <td><a href="{prefix}{download}/{file}?jwt={token}">download</a></td>
                </tr>'''.format(prefix=_PREFIX,
                                dir=__url_line['migrate'],
                                download=__url_line['download'],
                                file=file.filename,
                                V=file.ver,
                                token=choose_to_migtare._token)
        collection += s
    return '''
        <!doctype html>
        <html>
        <head>
        <title>upload</title>
        </head>
        <body>
        <h1>Latest version {latest} </h1>
        <h2>Current version in use {current} </h2>
        <table>
        <tr>
            <th>Version</th>
            <th>Filename</th>
            <th>Update</th>
            <th>Download</th>
        </tr>
        <tr>
            {coll}
        </tr>
        </table>
        </body>
        </html>
    '''.format(coll=collection, latest=latest, current=current)


@route(__url_line['download'] + '/<filename>', methods=['GET'])
@secured(scope['admin'])
def file_download(filename):
    return send_from_directory(LINE_DB_DIRECTORY, filename)


@route(__url_line['migrate'] + '/<filename>', methods=['GET'])
@secured(scope['admin'])
def migrate_handler(filename):
    try:
        file = migrate(filename)
    except Exception as e:
        return http_err(str(e))

    return http_ok(data=dict(data=file))


@route(__url_line['list'], methods=['GET', 'POST'])
@cross_origin()
@secured()
def list_lines(token_data):
    allowed = False
    for role in token_data['scopes']:
        if role in [sscope.Advertisement.VIEWER, sscope.Advertisement.ADMIN, sscope.Advertisement.INOBI, sscope.INOBI,
                    sscope.Transport.ADMIN]:
            allowed = True
    response = list_(exclude=allowed)
    if response['code'] != 200:
        return http_err(status=response['code'])
    return http_ok(data=dict(data=response['data']))


@route(__url_line['line'], methods=['POST', 'GET'])
@cross_origin()
@secured()
def line_handler():
    id_ = getargs(request, 'id')[0]

    if not id_:
        return http_err('id argument is missing', 400)
    data = {
        'id': id_
    }

    response = get_line(data)

    if response['code'] != 200:
        return http_err(message=response['message'], status=response['code'])
    return http_ok(data=dict(data=response['data']))


# @route(__url_line['platforms'], methods=['POST'])
# @secured()
# def platforms_handler():
#     try:
#         data = request.get_json(force=True)
#     except:
#         return http_err('json is not valid', 400)
#     if 'start_point' not in data:
#         return http_err('start_point argument is missing', 400)
#     if 'end_point' not in data:
#         return http_err('end_point argument is missing', 400)
#     if 'lat' not in data['start_point']:
#         return http_err('lat argument in start_point is missing')
#     if 'lng' not in data['start_point']:
#         return http_err('lng argument in start_point is missing')
#     if 'lat' not in data['end_point']:
#         return http_err('lat argument in end_point is missing')
#     if 'lng' not in data['end_point']:
#         return http_err('lng argument in end_point is missing')
#     line = line_controller()
#     platforms = line.get_platforms(data['start_point'], data['end_point'])
#     if platforms['code'] != 200:
#         return http_err(platforms['message'], platforms['code'])
#     return http_ok(data=dict(data=platforms['data']))


@route(__url_line['platform_routes'], methods=['POST', 'GET'])
@secured()
def platform_routes_handler():
    id_ = getargs(request, 'id')[0]
    if not id_:
        return http_err('id argument is missing', 400)

    data = {
        'id': id_
    }
    routes = get_platform_routes(data['id'])

    if routes['code'] != 200:
        return http_err(routes['message'], routes['code'])
    return http_ok(dict(data=routes['data']))
