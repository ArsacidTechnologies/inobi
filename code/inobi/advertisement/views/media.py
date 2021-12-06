
import os
import shutil
import subprocess
import typing as T

from flask import request, send_from_directory, url_for
from flask_cors import cross_origin

from inobi.security import secured, scope
from inobi.utils import http_err, http_ok
from inobi.utils.converter import converted, Modifier
from .. import route
from ..config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..security import Scope
from ..utils import get_directory, get_files_list, allowed_file, allowed_thumbnail, thumbnail_name, url_for_with_root

tag = '@Views.Media:'


@route('/v1/admin/upload_file', methods=['POST', 'GET'])
@cross_origin()
@secured(Scope.ADS_ADMIN)
def admin_upload_file(token):

    if request.method == 'POST':
        if 'file' not in request.files or 'thumbnail' not in request.files:
            return http_err(message='No file or thumbnail part', status=400)

        file = request.files['file']
        thumbnail = request.files['thumbnail']

        if file.filename == '' or thumbnail.filename == '':
            return http_err(message='No selected file or thumbnail', status=400)

        if not allowed_file(file.filename) or not allowed_thumbnail(thumbnail.filename):
            return http_err(message='Such file is not allowed', status=400)
        if file and thumbnail:
            from uuid import uuid4
            from os.path import join
            name = str(uuid4())
            filename = name + '.' + file.filename.rsplit('.', 1)[1].lower()
            file.save(join(get_directory('temp'), filename))
            thumbnail.save(join(get_directory('thumbnail_temp'), name + '.thumb'))
            return http_ok(
                uploaded_file_url=url_for_with_root('.'+uploaded_temp_file.__name__, filename=filename),
                uploaded_file_thumbnail_url=url_for_with_root('.'+uploaded_thumbnail_file.__name__, filename=filename, in_temp='true'),
                filename=filename
            )
    return '''
<form method=post enctype=multipart/form-data>
  <p><label>File: <input type=file name=file></label>
  <p><label>Thumbnail: <input type=file name=thumbnail></label>
  <input type=hidden name=jwt value="{jwt}" />
  <p><input type=submit value=Upload>
</form>
'''.format(jwt=token)


@route('/v1/uploads/temp/<filename>')
@cross_origin()
@secured(Scope.ADS_ADMIN)
def uploaded_temp_file(filename):
    return send_from_directory(get_directory('temp'), filename)


@route('/v1/uploads/thumbnail/<filename>')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def uploaded_thumbnail_file(filename, in_temp: Modifier.BOOL = False):

    folder = get_directory('thumbnail_temp' if in_temp else 'thumbnail_media')

    filename = thumbnail_name(filename)
    return send_from_directory(folder, filename)


@route('/v1/admin/upload_external', methods=['POST', 'GET'])
@cross_origin()
@secured([scope.Transport.INOBI, scope.Advertisement.ADMIN, ])
def admin_upload_external_file(token):
    if request.method == 'POST':
        if 'file' not in request.files:
            return http_err(message='No file part', status=403)
        file = request.files['file']
        if file.filename == '':
            return http_err(message='No selected file', status=403)
        if file:
            from uuid import uuid4
            from os.path import join
            filename = str(uuid4())
            file.save(join(get_directory('external'), filename))
            return http_ok(
                uploaded_file_url=url_for_with_root('.'+uploaded_external_file.__name__, filename=filename),
                filename=filename
            )
    return '''
    <form method=post enctype="multipart/form-data">
      <p><label>File: <input type=file name=file></label>
      <p><input type=submit value=Upload>
      <input type=hidden name=jwt value="{}" />
    </form>
    '''.format(token)


# PUBLIC
@route('/v1/uploads/external/<filename>')
@cross_origin()
def uploaded_external_file(filename):
    return send_from_directory(get_directory('external'), filename)


# Just handy directories listing API
@route('/v1/admin/list_uploads/<directory>')
@cross_origin()
@secured(Scope.ADS_ADMIN)
def admin_list_uploads(directory):
    files = get_files_list(directory)
    return http_ok(files=files)


def thumbnail_size_modifier(x) -> T.Tuple[int, int]:
    if isinstance(x, str) and 'x' in x:
        w, h = x.split('x')
        return int(w), int(h)
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return tuple(map(int, x))
    if isinstance(x, dict) and 'width' in x and 'height' in x:
        return int(x['width']), int(x['height'])
    raise Exception('Not Understood')


@route('/v2/admin/upload_file', methods=['POST', 'GET'])
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted(description_for__thumbnail_size="Size of Thumbnail ('240x240', [240, 240], {width: 240, height: 240})")
def admin_upload_file_v2(token, thumbnail_frame_at: float = 3.0, thumbnail_size: thumbnail_size_modifier = (240, 240)):

    if request.method == 'POST':

        if 'file' not in request.files:
            return http_err(message='No file', status=400)

        file = request.files['file']

        if file.filename == '':
            return http_err(message='No selected file', status=400)

        if not allowed_file(file.filename):
            return http_err(message='Such file is not allowed', status=400)

        if file:
            from uuid import uuid4
            from os.path import join
            name = str(uuid4())

            f_ext = os.path.splitext(file.filename)[-1][1:].lower()

            filename = name + '.' + f_ext
            source_filename = join(get_directory('temp'), filename)
            file.save(source_filename)

            thumbnail_filename = join(get_directory('thumbnail_temp'), name + '.thumb')

            if f_ext in VIDEO_EXTENSIONS:
                # ffmpeg -ss 2 -i vid.mp4 -vframes 1 -f image2 out.jpg -y
                cmd = ['ffmpeg', '-ss', str(thumbnail_frame_at), '-i', source_filename, '-vframes', '1', '-f', 'image2', thumbnail_filename, '-y']
                retcode = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if retcode == 0:
                    from PIL import Image
                    im = Image.open(thumbnail_filename)
                    im.thumbnail(thumbnail_size)
                    im.save(thumbnail_filename, 'jpeg')
                else:
                    os.unlink(source_filename)
                    return http_err('Thumbnail failed', 500)
            elif f_ext in IMAGE_EXTENSIONS:
                shutil.copyfile(source_filename, thumbnail_filename)

                from PIL import Image
                im = Image.open(thumbnail_filename)
                im.thumbnail(thumbnail_size)
                im.save(thumbnail_filename, 'png')

            uploaded = dict(
                filename=filename,
                url=url_for('.'+uploaded_temp_file.__name__, filename=filename, _external=True),
                thumbnail_url=url_for('.'+uploaded_thumbnail_file.__name__, filename=filename, in_temp='true', _external=True),
            )

            return http_ok(
                uploaded=uploaded
            )

    return '''
<form method=post enctype=multipart/form-data>
  <p><label>File: <input type=file name=file></label>
  <input type=hidden name=jwt value="{jwt}" />
  <p><input type=submit value=Upload>
</form>
'''.format(jwt=token)


@route('/v1/admin/delete_upload')
@cross_origin()
@secured(Scope.ADS_ADMIN)
@converted
def advertisement_admin_delete_upload(filename: str):

    fname, fext = os.path.splitext(filename)

    d = get_directory('temp')
    dt = get_directory('thumbnail_temp')

    media_deleted = thumbnail_deleted = False
    try:
        os.remove(os.path.join(d, filename))
    except FileNotFoundError:
        # return http_err('Filename Not Found', 404)
        pass
    else:
        media_deleted = True

    try:
        os.remove(os.path.join(dt, fname + '.thumb'))
    except FileNotFoundError:
        # return http_err('Thumbnail Not Found', 404)
        pass
    else:
        thumbnail_deleted = True

    if not any([media_deleted, thumbnail_deleted]):
        return http_err('Filename Not Found', 404)

    return http_ok(filename=filename,
                   media_deleted=media_deleted,
                   thumbnail_deleted=thumbnail_deleted,
                   )
