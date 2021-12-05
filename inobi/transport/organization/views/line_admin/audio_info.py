from ... import bp
from flask_cors import cross_origin
from inobi.security import secured
from inobi.transport.organization.utils import organization_required
from inobi.utils.converter import converted
from flask import request
from werkzeug.datastructures import FileStorage
from inobi.exceptions import BaseInobiException
from inobi.transport.configs import AudioConfig, AUDIO_INFO_RESOURCES, TMP_DIRECTORY
from .... import error_codes as ec
from inobi.utils import http_ok, get_md5, wav_converter
import os, string, random
import pathlib
from ...db.models import AudioInfo, AudioInfoFile
from inobi import db


def get_random_string(n):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def safe_filename(filename, lang, directory=AUDIO_INFO_RESOURCES) -> pathlib.Path:
    path = directory
    os.makedirs(path, exist_ok=True)
    folder = pathlib.Path(path) / lang
    os.makedirs(folder.as_posix(), exist_ok=True)
    file_path = folder / filename
    return file_path


def files_serializer(r):
    files = {}
    for lang, file in r.files.items():
        if not isinstance(file, FileStorage):
            raise BaseInobiException('file required', ec.FILE_REQUIRED, 400)
        if file.mimetype not in AudioConfig.MIMETYPE:
            raise BaseInobiException('only wav files', ec.FILE_MUST_BE_WAV, 400)
        if lang not in AudioConfig.Lang.ALL:
            raise BaseInobiException('lang not found', ec.LANG_NOT_FOUND, 400)
        files[lang] = file
    return files


@bp.route('/v1/audio_info', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def audio_info(weight: int, organization, name: str):
    files = files_serializer(request)
    if not files:
        raise BaseInobiException('file required', ec.FILE_REQUIRED, 400)
    if not 0 <= weight <= 10:
        raise BaseInobiException("'weight' must be in 0-10", ec.INVALID_FORMAT, 400)
    info = AudioInfo(organization=organization, name=name, weight=weight)
    db.session.add(info)
    db.session.commit()

    for lang, file in files.items():
        filename = safe_filename('{}{}'.format(info.id, pathlib.Path(file.filename).suffix), lang)
        tmp_filename = safe_filename('{}{}'.format(info.id, pathlib.Path(file.filename).suffix), lang, TMP_DIRECTORY)
        file.save(tmp_filename.as_posix())
        wav_converter(tmp_filename.as_posix(), filename.as_posix())
        os.remove(tmp_filename.as_posix())
        md5 = get_md5(filename.as_posix())
        file = AudioInfoFile(audio_info=info.id, filename=filename.name, language=lang, md5=md5)
        db.session.add(file)
    db.session.commit()
    return http_ok(info.asdict())


@bp.route('/v1/audio_info/<int:id>', methods=['PATCH'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
@converted()
def audio_info_update(id, organization: int, name: str=None, weight: int=None):
    info = AudioInfo.query.filter(AudioInfo.organization == organization, AudioInfo.id == id).first()
    if not info:
        raise BaseInobiException('not found', ec.NOT_FOUND, 404)
    if name:
        info.name = name
    if weight:
        if not 0 <= weight <= 10:
            raise BaseInobiException("'weight' must be in 0-10", ec.INVALID_FORMAT, 400)
        info.weight = weight
    files = files_serializer(request)
    for lang, file in files.items():
        filename = safe_filename('{}{}'.format(info.id, pathlib.Path(file.filename).suffix), lang)
        tmp_filename = safe_filename('{}{}'.format(info.id, pathlib.Path(file.filename).suffix), lang, TMP_DIRECTORY)
        file.save(tmp_filename.as_posix())
        try:
            wav_converter(tmp_filename.as_posix(), filename.as_posix())
        except Exception as e:
            raise BaseInobiException(str(e), 1, 400)
        os.remove(tmp_filename.as_posix())
        md5 = get_md5(filename.as_posix())
        audio_file = AudioInfoFile.query.filter(AudioInfoFile.audio_info == id, AudioInfoFile.language == lang).first()
        if not audio_file:
            audio_file = AudioInfoFile()
        audio_file.audio_info = info.id
        audio_file.filename = filename.name
        audio_file.language = lang
        audio_file.md5 = md5
        # file = AudioInfoFile(audio_info=info.id, filename=filename.name, language=lang, md5=md5)
        db.session.add(audio_file)

    db.session.commit()
    return http_ok(info.asdict())


@bp.route('/v1/audio_info', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
def audio_info_list(organization):
    audios = AudioInfo.query.filter(AudioInfo.organization == organization).all()
    data = [a.asdict() for a in audios]
    return http_ok({"data": data})


@bp.route('/v1/audio_info/<int:id>', methods=['DELETE'])
@cross_origin()
@secured('transport_viewer')
@organization_required(is_table=False)
def audio_info_one(id, organization):
    audio = AudioInfo.query.filter(AudioInfo.organization == organization, AudioInfo.id == id).first()
    if not audio:
        raise BaseInobiException('not found', ec.NOT_FOUND, 404)
    for file in audio.files:
        file.remove()
        db.session.delete(file)
    db.session.delete(audio)
    db.session.commit()
    return http_ok(audio.asdict())

