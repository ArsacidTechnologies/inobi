
from flask_cors import cross_origin

from flask import url_for, send_from_directory

from .. import route

from ..config import APP_USER_PICTURES_DIRECTORY


@route('/v1/user/picture/<picture>')
@cross_origin()
def app_user_picture_v1(picture):
    return send_from_directory(directory=APP_USER_PICTURES_DIRECTORY,
                               filename=picture,
                               as_attachment=True,
                               attachment_filename=picture)
