import os
from inobi.transport import route, exceptions, error_codes as ec
from flask import send_from_directory, render_template, url_for, request
from inobi.utils import get_md5, http_err, http_ok, wav_converter
from inobi.security import secured
from inobi.utils.converter import converted
from urllib3.util import parse_url
import re
from inobi.transport.configs import LINE_DB_DIRECTORY, AUDIO_RESOURCES, AUDIO_INFO_RESOURCES, AudioConfig, TMP_DIRECTORY
import sqlite3
import json
from inobi.transport.organization.db.models import AudioInfo
from inobi.transport.DataBase.models import Route
from pathlib import Path

md5_hash = 'md5_hash'


def get_file_with_md5(path: Path):
    md5_path = path / AudioConfig.MD5_HASH_FILE
    if not md5_path.exists():
        direction_files = {
            title.name: get_md5(path.joinpath(title).as_posix())
            for title in path.iterdir() if title.suffix == AudioConfig.FORMAT_
        }
        with open(md5_path.as_posix(), 'w') as f:
            json.dump(direction_files, f, indent=2)
    else:
        with open(md5_path.as_posix(), 'r') as f:
            direction_files = json.load(f)
    return direction_files


@route('/v2/audio/sync')
@converted()
@secured()
def audio_v2_sync(route_id: int):
    db_route = Route.query.get(route_id)
    if not db_route:
        raise exceptions.TransportException('not found', ec.NOT_FOUND, 404)
    platforms = []
    for direction in db_route.directions:
        for platform in direction.platforms:
            platforms.append((platform.id, direction.id))
    final_files = {}
    for lang in AudioConfig.Lang.ALL:
        final_files[lang] = []
        lang_path = Path(AUDIO_RESOURCES) / lang
        if not lang_path.exists():
            continue
        lang_files = get_file_with_md5(lang_path)
        direction_files = {}
        for id, dir_id in platforms:
            if dir_id not in direction_files:
                direction_files[dir_id] = {}
                dir_path = lang_path.joinpath(str(dir_id))
                if dir_path.exists():
                    direction_files[dir_id] = get_file_with_md5(dir_path)

            # current = "{}_{}{}".format(id, AudioConfig.Type.CURRENT, AudioConfig.FORMAT_)
            # next = "{}_{}{}".format(id, AudioConfig.Type.NEXT, AudioConfig.FORMAT_)
            #
            # if current in direction_files[dir_id]:
            #     final_files[lang]["{}/{}".format(dir_id, current)] = direction_files[dir_id][current]
            # elif current in lang_files:
            #     final_files[lang][current] = lang_files[current]
            #
            # if next in direction_files[dir_id]:
            #     final_files[lang]["{}/{}".format(dir_id, next)] = direction_files[dir_id][next]
            # elif next in lang_files:
            #     final_files[lang][next] = lang_files[next]

            current = "{}_{}{}".format(id, AudioConfig.Type.CURRENT, AudioConfig.FORMAT_)
            current_md5 = None
            next = "{}_{}{}".format(id, AudioConfig.Type.NEXT, AudioConfig.FORMAT_)
            next_md5 = None

            if current in direction_files[dir_id]:
                current_md5 = direction_files[dir_id][current]
                current = "{}/{}".format(dir_id, current)
            elif current in lang_files:
                current_md5 = lang_files[current]

            if next in direction_files[dir_id]:
                next_md5 = direction_files[dir_id][next]
                next = "{}/{}".format(dir_id, next)
            elif next in lang_files:
                next_md5 = lang_files[next]
            download_url = '/transport/audio/{}/'.format(lang)
            if current_md5:
                final_files[lang].append({
                    "id": id,
                    "download": download_url + current,
                    "type": AudioConfig.Type.CURRENT,
                    "md5": current_md5
                })
            if next_md5:
                final_files[lang].append({
                    "id": id,
                    "download": download_url + next,
                    "type": AudioConfig.Type.NEXT,
                    "md5": next_md5
                })

    return http_ok(final_files)


@route('/file/audio_info/<path:path>',  methods=['GET'])
def audio_info_resources(path):
    return send_from_directory(AUDIO_INFO_RESOURCES, path)


@route('/audio_info', methods=['GET'])
@converted()
def audio_info_list():
    audios = AudioInfo.query.all()
    data = [
        audio.asdict()
        for audio in audios
    ]
    return http_ok({'data': data})


@route('/audio/<path:path>',  methods=['GET'])
def audio_resources(path):
    return send_from_directory(AUDIO_RESOURCES, path)


@route('/audio/<folder>/<file>', methods=['DELETE'])
def audio_resources_delete(folder, file):
    directory = os.path.join(AUDIO_RESOURCES, folder)
    file = os.path.join(directory, file)
    if not os.path.exists(file):
        return http_err('not found', 404)
    os.remove(file)

    md5_hash_file = os.path.join(directory, md5_hash)
    if os.path.exists(md5_hash_file):
        os.remove(md5_hash_file)
    return http_ok()


@route('/audio', methods=['POST'])
def audio_resources_save():
    lang = request.values.get('lang')
    if not lang:
        return http_err('lang is missing', 400)
    _type = request.values.get('type')
    if not _type:
        return http_err('type is missing', 400)
    url = request.values.get('url')
    if not url:
        return http_err('url is missing', 400)

    platform_id = get_platform(url)
    if not isinstance(platform_id, int):
        return platform_id
    folder = Path(AUDIO_RESOURCES) / lang
    if not folder.exists():
        os.makedirs(folder.as_posix(), exist_ok=True)
    final_destination = folder / "{}_{}.wav".format(platform_id, _type)
    tmp_destination = Path(TMP_DIRECTORY) / "{}_{}.wav".format(platform_id, _type)
    with open(tmp_destination.as_posix(), 'wb') as f:
        f.write(request.data)
    try:
        wav_converter(tmp_destination.as_posix(), final_destination.as_posix())
    except Exception as e:
        return http_err('invalid file {}'.format(e), 400)
    os.remove(tmp_destination.as_posix())
    md5_hash_file = folder / md5_hash
    if md5_hash_file.exists():
        os.remove(md5_hash_file.as_posix())
    return http_ok()


@route('/audio/<folder>/sync')
@converted()
def audio_sync(folder, direction: str = None):
    source_dir = os.path.join(AUDIO_RESOURCES, folder)
    if not os.path.isdir(source_dir):
        return http_err('{} is not folder'.format(folder), 400)
    if not os.path.exists(source_dir):
        return http_err('folder not found', 404)
    direction_files = {}
    if direction:
        direction_dir = os.path.join(source_dir, direction)
        if os.path.exists(direction_dir) and os.path.isdir(direction_dir):
            direction_md5_file = os.path.join(direction_dir, md5_hash)
            if not os.path.exists(direction_md5_file):
                direction_files = {
                    title: get_md5(os.path.join(direction_dir, title))
                    for title in os.listdir(direction_dir) if os.path.isfile(os.path.join(direction_dir, title))
                }
                with open(direction_md5_file, 'w') as f:
                    json.dump(direction_files, f)
            else:
                with open(direction_md5_file, 'r') as f:
                    direction_files = json.load(f)
    md5_hash_file = os.path.join(source_dir, md5_hash)
    if not os.path.exists(md5_hash_file):
        files = {
            title: get_md5(os.path.join(source_dir, title))
            for title in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, title))
        }
        with open(md5_hash_file, 'w') as f:
            json.dump(files, f)
    else:
        with open(md5_hash_file, 'r') as f:
            files = json.load(f)
    final = {**files, **direction_files}
    return http_ok(data=dict(data=final))


@route('/audio')
def audio_template():
    return render_template('transport/audio.html')


@route('/v2/audio')
def audio_v2_audio():
    return render_template('transport/audios/index.html')


@route('/audio/files')
@converted()
def audio_files(url: str):
    platform_id = get_platform(url)
    if not isinstance(platform_id, int):
        return platform_id
    data = {}
    for lang in os.listdir(AUDIO_RESOURCES):
        data[lang] = {
            "current": None,
            "next": None
        }
        for title in os.listdir(os.path.join(AUDIO_RESOURCES, lang)):
            if not title.startswith("{}_".format(platform_id)):
                continue
            if title.endswith('next.wav'):
                data[lang]['next'] = url_for('Transport.audio_resources', folder=lang, file=title, _external=True)
            if title.endswith('current.wav'):
                data[lang]['current'] = url_for('Transport.audio_resources', folder=lang, file=title, _external=True)
    return http_ok(data=dict(data=data))


def get_platform(url):
    url_data = parse_url(url)
    if url_data.host != '2gis.kg':
        return http_err('2gis.kg only', 400)
    platform = re.search('\/platform\/\d+', url_data.path).group()
    if not platform.startswith('/platform/'):
        return http_err('no platform specified')
    platform = platform[len('/platform/'):]
    versions_file_path = os.path.join(LINE_DB_DIRECTORY, 'ver.index')
    if not os.path.exists(versions_file_path) and not os.path.isfile(versions_file_path):
        return http_err('LINES NOT SET, GO TO ADMIN AND SAY')
    with open(versions_file_path, 'r') as f:
        versions = json.load(f)
    db_path = os.path.join(LINE_DB_DIRECTORY, versions['files'][versions['current']])
    with sqlite3.connect(db_path) as conn:
        sql = '''
                select p.id from platforms p
                inner join ids
                on ids.id = p.id
                where ids.gis_id = ?
            '''
        cursor = conn.cursor()
        cursor.execute(sql, (platform,))
        platform_id = cursor.fetchone()
        if not platform_id:
            return http_err('unknown platform', 400)
        platform_id, *_ = platform_id
    return platform_id
