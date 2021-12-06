from flask import abort, request, url_for, send_from_directory

from inobi.security import secured
from inobi.utils import getargs, http_ok, http_err
from inobi.utils.converter import converted

from .. import route

from ..config import DB_TEMP_FILENAME, DB_FILENAME_IN_ARCHIVE, DIRECTIONS_BFS_DB_PATH
from ..utils import app_data_index, dump_app_data_index, APP_DB_DIRECTORY, DB_ZIP_FILENAME_UNFORMATTED

import zipfile, os, shutil

tag = "@{}:".format(__name__)


@route('/v1/version')
@secured('application')
def app_version_v1():
    index = app_data_index()
    if not index:
        return abort(404)

    return http_ok({'version': index['current']})


@route('/v1/data')
@secured('application')
@converted
def app_data_v1(version: int = None):

    index = app_data_index()
    if index is None:
        return abort(404)

    current = index['current']
    if version is None:
        version = current

    version = str(version)

    if version not in index['index']:
        return abort(404)

    fname = index['index'][version]

    return send_from_directory(
        directory=APP_DB_DIRECTORY,
        filename=fname,
        as_attachment=True,
        attachment_filename=fname
    )


@route('/v1/admin/version')
@secured('application_admin')
def admin_app_version_v1():

    (version,) = getargs(request, 'set')

    if not version:
        return abort(404)

    if isinstance(version, str) and not str(version).isdigit():
        return http_err('Version Parameter Misunderstood', 404)

    version = int(version)

    index = app_data_index()
    if not index:
        return http_err('Index Not Initalized')

    if str(version) not in index['index']:
        return http_err('No Such Version In Index. Should upload it first')

    index['current'] = version
    dump_app_data_index(index)

    return http_ok()


@route('/v1/admin/upload/<int:version>')
@secured('application_admin')
def app_admin_upload_v1(version):

    update_current, \
    force_rewrite, \
    update_web_search = getargs(
        request,
        'update_current',       # if true sets current app db version to uploaded
        'force_rewrite',        # if true and file already exists, will rewrite db
        'update_web_search',    # if true updates web search database source
    )

    update_current = True if update_current and update_current.lower() in ('true', 'ok', 'on', 'yes') else False
    force_rewrite = True if force_rewrite and force_rewrite.lower() in ('true', 'ok', 'on', 'yes') else False
    update_web_search = True if update_web_search and update_web_search.lower() in ('true', 'ok', 'on', 'yes') else False

    if request.method == 'POST':
        if 'database' not in request.files:
            return http_err(message='No database attached', status=400)

        file = request.files['database']

        if file.filename == '':
            return http_err(message='No selected database file', status=400)

        file_ext = file.filename.rsplit('.', 1)[-1].lower()

        if file_ext not in ('db', 'sqlite', 'sqlite3'):
            return http_err(message='Such file is not allowed', status=400)

        if file:
            from os.path import join, isfile

            version = str(version)
            filename = DB_ZIP_FILENAME_UNFORMATTED.format(version)
            zip_path = join(APP_DB_DIRECTORY, filename)

            index = app_data_index()
            if index is None:
                index = dict(current=version, index=dict())

            if not force_rewrite and index['index'].get(version) == filename and isfile(zip_path):
                return http_err(
                    message='File Already Exists For Version (version: {})'.format(version),
                    status=400)

            version = int(version)

            if update_current:
                index['current'] = version

            # saving to tmp file
            tmp_fname = join(APP_DB_DIRECTORY, DB_TEMP_FILENAME)
            file.save(tmp_fname)

            if update_web_search:
                shutil.copyfile(tmp_fname, DIRECTIONS_BFS_DB_PATH)

            # creating zip and adding tmp file to it
            zf = zipfile.ZipFile(zip_path, mode='w')
            zf.write(tmp_fname, DB_FILENAME_IN_ARCHIVE, compress_type=zipfile.ZIP_DEFLATED)
            zf.close()

            os.unlink(tmp_fname)

            index['index'][version] = filename

            dump_app_data_index(index)

            return http_ok(dict(resource=url_for(app_data_v1.__name__, version=version)))

    return '''
        <form style="font-size:1rem;" action="{}" method=post enctype=multipart/form-data>
          <p><label>Database: <input type=file name=database></label></p>
          <p><label style="font-size: 2rem; color: red;">Force rewrite: <input type=checkbox name=force_rewrite></label></p>
          <p><label>Update current version: <input checked type=checkbox name=update_current></label></p>
          <p><label>Update web search: <input type=checkbox checked name=update_web_search></label></p>
          <input type=hidden name=token value="{}" />
          <p><input type=submit value=Upload></p>
        </form>
        '''.format(url_for(app_admin_upload_v1.__name__, version=version), app_admin_upload_v1._token)
