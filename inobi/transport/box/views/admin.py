
from .. import bp

from flask import request, url_for, render_template

from inobi.security import secured, scope

from inobi.advertisement.cache import getcached, cache
from inobi.advertisement.utils import debug_exception, get_directory

from inobi.utils import http_err, http_ok, getargs

from inobi.utils.converter import converted, Modifier

from inobi.advertisement.utils import debug_exception, get_directory, get_files_list, url_for_with_root

from .. import db

from inobi.advertisement.security import check_box_token, Scope

from .. import config

tag = '@Box_views:'


# IMPORTED VIEWS

from .public import box_internet, box_update, box_update_version
from . import test


import functools as FT

route = FT.partial(bp.route, methods=('POST', 'GET'))
CKeys = config.CKeys


@route('/v1/admin/updates')
@secured(scope.Transport.INOBI)
def admin_box_updates_list():
    updates = [bu._asdict() for bu in db.box_updates_list()]
    return http_ok(updates=updates, count=len(updates))


@route('/v1/admin/internet')
@secured(scope.Transport.INOBI)
@converted(verbose=False)
def admin_box_internet(token, allow: Modifier.BOOL = False, get: Modifier.BOOL = False):

    if get:
        return box_internet()

    key = CKeys.INTERNET

    if request.method == 'POST':
        try:
            result = db.set_box_setting(key, str(allow).lower())
            cache(key, None)
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
        checked="checked" if db.get_box_setting(key) == 'true' else '',
        jwt=token
    )


@route('/v1/admin/version')
@secured(scope.Transport.INOBI)
@converted
def admin_box_update_version(get: Modifier.BOOL = False):

    if get:
        return box_update_version()

    key = CKeys.VERSION

    if request.method == 'POST':
        version, = getargs(request, 'version')

        if version is None:
            return http_err(message="'version' Argument Must Present", status=403)

        version = db.set_box_setting(key, version)
        cache(key, None)
        return http_ok(**version)

    return '''
<form method="post">
    <label>Version: 
        <input name="version" type="text" value="{}"></input>
    </label>
    <input type=submit value=Update>
</form>
'''.format(box_update_version())


@route('/v1/admin/update')
@secured(scope.Transport.INOBI)
@converted
def admin_box_update(token, get: Modifier.BOOL = False):

    if get:
        return box_update()

    from os.path import join

    if request.method == 'POST':
        if 'file' not in request.files:
            return http_err(message='No file part', status=403)
        file = request.files['file']
        if file.filename == '':
            return http_err(message='No selected file', status=403)
        if file:
            file.save(join(config.BOX_UPDATES_DIRECTORY, config.BOX_UPDATE_FILE))

            key = CKeys.VERSION

            apply = 'apply' in request.form
            version = db.get_box_setting(key, typed_to=int) or 0
            if apply:
                new_version = version + 1
                v = db.set_box_setting(key, new_version)
                version = new_version
                cache(key, None)

            return http_ok(
                file=url_for('.'+box_update.__name__, _external=True),
                applied=apply, version=version
            )
    script = None
    try:
        with open(join(config.BOX_UPDATES_DIRECTORY, config.BOX_UPDATE_FILE)) as f:
            script = f.read()
    except:
        pass
    return render_template('transport/box/admin/upload_update.html', 
        jwt=token, 
        script=script
    )
