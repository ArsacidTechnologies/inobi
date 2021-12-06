from flask import request, url_for

from ... import route
from inobi.security import secured
from ...exceptions import InobiException

from ...cache import CKeys, cache

from inobi.utils import http_err, http_ok, getargs

from inobi.utils.converter import converted, Modifier

from ...utils import debug_exception, get_directory, get_files_list, url_for_with_root

from ...db.box import (
    get_box_update_version,
    set_box_update_version,
    get_box_internet,
    set_box_internet,
    get_box_setting,
    set_box_setting,
    box_updates_list
    )

from ...security import check_box_token, Scope

from ...config import BOX_UPDATE_FILE

tag = '@Box_views:'


# IMPORTED VIEWS

from .public import box_internet, box_update, box_update_version
from . import test


@route('/v1/admin/box/updates')
@secured(Scope.ADS_ADMIN)
def admin_box_updates_list():
    try:
        updates = [bu._asdict() for bu in box_updates_list()]
        return http_ok(updates=updates, count=len(updates))
    except InobiException as e:
        debug_exception(tag, e)
        return http_err(message=str(e), status=400)
    except:
        return http_err()


@route('/v1/admin/box/internet')
@secured(Scope.ADS_ADMIN)
@converted(verbose=False)
def admin_box_internet(token, allow: Modifier.BOOL = False, get: Modifier.BOOL = False):

    if get:
        return box_internet()

    if request.method == 'POST':
        try:
            result = set_box_internet(value=str(allow).lower())
            cache(CKeys.INTERNET, None)
            return http_ok(result=result)
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            return http_err()

    return '''
<form method="post">
    <label>Allow internet: 
        <input name="allow" type="checkbox" {checked}></input>
    </label>
    <input name="jwt" type="hidden" value="{jwt}"/>
    <input type=submit value="Apply">
</form>
'''.format(
        checked="checked" if get_box_internet() == 'true' else '',
        jwt=token
    )


@route('/v1/admin/box/version')
@secured(Scope.ADS_ADMIN)
@converted
def admin_box_update_version(get: Modifier.BOOL = False):

    if get:
        return box_update_version()

    if request.method == 'POST':
        version, = getargs(request, 'version')
        
        if version is None:
            return http_err(message="'version' Argument Must Present", status=403)
        try:
            version = set_box_update_version(version)
            cache(CKeys.BOX_VERSION, None)
            return http_ok(dict(previous_version=version.get('previous'), current_version=version.get('current')))
        except Exception as e:
            debug_exception(tag, e, to_file=True)
            if isinstance(e, InobiException):
                return http_err(message=str(e), status=403)
            else:
                return http_err()

    return '''
<form method="post">
    <label>Version: 
        <input name="version" type="text" value="{}"></input>
    </label>
    <input type=submit value=Update>
</form>
'''.format(box_update_version())


@route('/v1/admin/box/upload_update')
@secured(Scope.ADS_ADMIN)
@converted
def admin_box_update(token, get: Modifier.BOOL = False):

    if get:
        return box_update()

    if request.method == 'POST':
        if 'file' not in request.files:
            return http_err(message='No file part', status=403)
        file = request.files['file']
        if file.filename == '':
            return http_err(message='No selected file', status=403)
        if file:
            from os.path import join
            file.save(join(get_directory('box_updates'), BOX_UPDATE_FILE))

            apply = 'apply' in request.form
            if apply:
                version = int(get_box_update_version())
                v = set_box_update_version(version+1)
                cache(CKeys.BOX_VERSION, None)

            return http_ok(
                file=url_for_with_root('.'+box_update.__name__),
                applied=apply
            )
    return '''
<form method=post enctype=multipart/form-data>
  <p><input type=file name=file>
  <label><input type=checkbox name=apply checked>Apply update</label>
  <input type="hidden" value="{jwt}" name="jwt" />
  <input type=submit value=Upload>
</form>
    '''.format(
        jwt=token
    )
