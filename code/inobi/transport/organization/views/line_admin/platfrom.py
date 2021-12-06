from inobi.transport.organization import bp
from inobi.utils.converter import converted
from inobi.utils import http_ok, wav_converter
from inobi.security import secured
from flask_cors import cross_origin
from inobi.transport.organization.db.line_admin import platform as db
from inobi.transport.organization.utils import organization_required
from werkzeug.datastructures import FileStorage
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec
from inobi.transport.configs import AudioConfig, AUDIO_RESOURCES, TMP_DIRECTORY
import os
from inobi.transport.DataBase.models import Platforms, Directions
from flask import request
from pathlib import Path


@bp.route('/v1/platforms', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted
def platforms_post(organization, lat: float, lng: float, station_id: int):
    platform = db.create(lat=lat, lng=lng, organization=organization, station_id=station_id)
    return http_ok(platform)


def bounds(value):
    """Bounds object: {"lat": [123, 124], "lng": [321, 322]}"""
    if not isinstance(value, dict):
        raise ValueError('must be dictionary')
    if 'lat' not in value or 'lng' not in value:
        raise ValueError('lat/lng parameters must present')
    for k in ('lat', 'lng'):
        b = value[k]
        if not isinstance(b, list) or len(b) != 2 or len([c for c in b if isinstance(c, (int, float))]) != 2:
            raise ValueError('{} must be array containing tuple of coordinates (int, float)')
    return value


@bp.route('/v1/platforms/<int:id>', methods=['GET'])
@cross_origin()
@secured()
@organization_required(is_table=False)
def platforms_get(organization, id):
    platform = db.get(id, organization)
    return http_ok(platform)


@bp.route('/v1/platforms/<int:id>', methods=['PUT'])
@cross_origin()
@secured()
@organization_required(is_table=False)
@converted()
def platforms_patch(organization, lat: float, lng: float, id):
    platform = db.update(id, lat, lng, organization)
    return http_ok(platform)


@bp.route('/v1/platforms/<int:id>', methods=['DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
def platforms_delete(organization, id):
    platform = db.delete(id, organization)
    platform['audio'] = {}
    for lang in AudioConfig.Lang.ALL:
        platform['audio'][lang] = {}
        lang_path = os.path.join(AUDIO_RESOURCES, lang)
        for type in AudioConfig.Type.ALL:
            platform['audio'][lang][type] = None
            filename = "{}_{}.{}".format(platform['id'], type, AudioConfig.FORMAT)
            if os.path.exists(os.path.join(lang_path, filename)):
                platform['audio'][lang][type] = filename
                os.remove(os.path.join(lang_path, filename))

    for direction in platform['directions']:
        direction['audio'] = {}
        for lang in AudioConfig.Lang.ALL:
            direction['audio'][lang] = {}
            lang_path = os.path.join(AUDIO_RESOURCES, lang)
            dir_path = os.path.join(lang_path, str(direction['id']))
            for type in AudioConfig.Type.ALL:
                direction['audio'][lang][type] = None
                filename = "{}_{}.{}".format(platform['id'], type, AudioConfig.FORMAT)
                if os.path.exists(os.path.join(dir_path, filename)):
                    direction['audio'][lang][type] = filename
                    os.remove(os.path.join(dir_path, filename))
    return http_ok(platform)


import typing as T
Degree = T.Union[int, float]


@bp.route('/v1/platforms', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@organization_required()
@converted()
def platforms_get_list(organization, free: bool=False,
                       min_lat: float = None,
                       min_lng: float = None,
                       max_lat: float = None,
                       max_lng: float = None):
    bounds = None
    if None not in [min_lat, min_lng, max_lat, max_lng]:
        bounds = dict(lat=[min_lat, max_lat], lng=[min_lng, max_lng])
    platforms = db.list_(organization, free=free, bounds=bounds)
    return http_ok(dict(data=platforms, bounds=bounds))


@bp.route('/v1/platforms/<int:id>/audios', methods=['POST', 'DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def platform_audios(id, lang: str, type: str, direction: int = None):
    delete = request.method == 'DELETE'
    if not delete:
        file = request.files.get('file')
        if not isinstance(file, FileStorage):
            raise BaseInobiException('file required', ec.FILE_REQUIRED, 400)
        if file.mimetype not in AudioConfig.MIMETYPE:
            raise BaseInobiException('only wav files', ec.FILE_MUST_BE_WAV, 400)
    if lang not in AudioConfig.Lang.ALL:
        raise BaseInobiException('lang not found', ec.LANG_NOT_FOUND, 400)
    if type not in AudioConfig.Type.ALL:
        raise BaseInobiException('type not found', ec.TYPE_NOT_FOUND, 400)

    # platform = Platforms(id=1, lat=0, lng=0)
    platform = Platforms.query.filter(Platforms.id == id).first()
    if not platform:
        raise BaseInobiException('platform not found', ec.PLATFORM_NOT_FOUND, 404)
    resource = os.path.join(AUDIO_RESOURCES, lang)
    if not os.path.exists(resource):
        os.mkdir(resource)
    if direction:
        direction = Directions.query.filter(Directions.id == direction).first()
        if not direction:
            raise BaseInobiException('direction not found', ec.DIRECTION_NOT_FOUND, 404)
        folder = os.path.join(resource, str(direction.id))
        if not os.path.exists(folder):
            os.mkdir(folder)
    else:
        folder = resource
    filename = Path(folder) / "{}_{}.{}".format(platform.id, type, AudioConfig.FORMAT)
    if filename.exists():
        os.remove(filename.as_posix())
    if not delete:
        tmp_file = Path(TMP_DIRECTORY) / filename.name
        file.save(tmp_file.as_posix())
        try:
            wav_converter(tmp_file.as_posix(), filename.as_posix())
        except Exception as e:
            raise BaseInobiException(str(e), 1, 400)
        os.remove(tmp_file.as_posix())
    md5_hash_file = os.path.join(folder, AudioConfig.MD5_HASH_FILE)
    if os.path.exists(md5_hash_file):
        os.remove(md5_hash_file)
    platform = platform.as_dict(full=True)
    return http_ok(platform)



#
# platform_id = get_platform(url)
# if not isinstance(platform_id, int):
#     return platform_id
#
# filename = "{}_{}.wav".format(platform_id, _type)
# folder = os.path.join(AUDIO_RESOURCES, lang)
# if not os.path.exists(folder):
#     os.mkdir(folder)
# filename = os.path.join(folder, filename)
# with open(filename, 'wb') as f:
#     f.write(request.data)
# md5_hash_file = os.path.join(folder, md5_hash)
# if os.path.exists(md5_hash_file):
#     os.remove(md5_hash_file)
# return http_ok()