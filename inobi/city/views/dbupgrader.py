
import time
import typing as T
import functools as FT

import json

from flask_cors import cross_origin

from .. import bp, bfs
from inobi.utils.converter import converted, Modifier
from inobi.utils import http_err, http_ok

from inobi.security import secured, scope

from flask import request

import os
import signal

from .. import config, error_codes, db

import uuid

from inobi.exceptions import BaseInobiException

import re

import multiprocessing

from inobi.redis import getredis as _getredis
from inobi.config import RedisSegments


getredis = FT.partial(_getredis, db=RedisSegments.APPLICATION)


STATUS_RE = re.compile(r'^(?P<name>[a-fA-F0-9\-:]+)\.c(?P<city>\d+)\.to(?P<organization>\d*)\.u(?P<user>\d+)\.db(\.(?P<stage>\w+))?')

from inobi import add_prerun_hook


def clean_working_processes():
    print('TODO: cleanup failed BFS extraction processes')
    pass

add_prerun_hook(clean_working_processes)


def _get_process_info(name) -> T.Optional[dict]:
    """Return process info if exists"""

    r = getredis()
    key = config.UPGRADE_PROCESS_REDIS_KEY_TEMPLATE.format(name=name)
    val = r.get(key)
    if val is not None:
        return json.loads(val.decode())


def _set_process_info(name, value) -> T.Optional[dict]:
    """Save process info, return previous if exists"""

    r = getredis()
    key = config.UPGRADE_PROCESS_REDIS_KEY_TEMPLATE.format(name=name)

    prev = r.get(key)
    if prev is not None:
        prev = json.loads(prev.decode())

    if value is None:
        r.delete(key)
    else:
        r.set(key, json.dumps(value, ensure_ascii=False))

    return prev


def get_status(city_id, to_id=None, user_id=None, process_name=None) -> T.Optional[T.Union[list, dict]]:

    ls = os.listdir(config.RESOURCES_CITIES_UPGRADER)

    out = []

    for i in ls:
        fp = os.path.join(config.RESOURCES_CITIES_UPGRADER, i)
        res = STATUS_RE.match(i)
        if res:
            gd = res.groupdict()
            if gd['city'] == str(city_id):
                f_info = os.stat(fp)
                gd['file'] = dict(
                    modified=f_info.st_mtime,
                    accessed=f_info.st_atime,
                    size=f_info.st_size,
                )
                gd['process'] = _get_process_info(gd['name'])
                gd['_fn'] = i
                gd['_fp'] = fp
                gd['stage'] = gd['stage'] or config.CityUpgradeStage.DONE.value
                out.append(gd)
        else:
            print(res, i)

    if process_name:
        for p in out:
            if p['name'] == process_name:
                return p
        else:
            return None

    return out


def _start_bfs_extraction_process(db_path: str, city_id: int, process_name: str):
    # todo: log to redis progress of process

    init_db_path = db_path

    processing_db_path = init_db_path.replace(config.CityUpgradeStage.INIT.withdot,
                                         config.CityUpgradeStage.PROCESSING.withdot)

    succeeded_db_path = processing_db_path.replace(config.CityUpgradeStage.PROCESSING.withdot, '')

    try:
        import sqlite3

        # init
        with sqlite3.connect(db_path) as conn:
            db._dump_city(conn, city_id)

        # mv {fp}.init {fp}.processing
        os.rename(db_path, processing_db_path)

        # hard work here
        with sqlite3.connect(processing_db_path) as conn:
            bfs._extract_bfs(conn)

        # commit
        os.rename(processing_db_path, succeeded_db_path)

    except (KeyboardInterrupt, EOFError, SystemExit) as e:

        for i in [init_db_path, processing_db_path, succeeded_db_path]:
            try:
                os.unlink(i)
            except FileNotFoundError:
                pass

        raise e

    finally:

        _set_process_info(process_name, None)


def start_upgrade_process(city_id, to_id=None, user_id=None) -> dict:

    process_name = str(uuid.uuid4())
    stage = config.CityUpgradeStage.INIT

    fp = config.CITY_UPGRADE_TEMPLATE.format(name=process_name,
                                             city=city_id, organization=to_id or '',
                                             user=user_id,
                                             stage=stage.withdot)
    # do the actual process starting
    process = multiprocessing.Process(target=_start_bfs_extraction_process,
                                      args=(fp, city_id, process_name))
    process.daemon = True
    process.start()

    process_info = dict(
        pid=process.pid,
        start_time=time.time(),
    )

    _set_process_info(process_name, value=process_info)

    return dict(
        process=_get_process_info(process_name),
        _fn=os.path.split(fp)[-1],
        name=process_name,
        city=city_id,
        organization=to_id,
        user=user_id,
        stage=stage.value
    )


def apply_city_db(city_id: int, db_name: str):
    status = get_status(city_id, process_name=db_name)
    assert status is not None
    assert status['city'] == str(city_id)
    assert status['stage'] == config.CityUpgradeStage.DONE.value
    db.apply_direction_links(status['_fp'], city_id)


@bp.route('/v1/cities/<int:city_id>/upgrader/', methods='POST GET'.split())
@cross_origin()
@secured([scope.Transport.ADMIN, ])
@converted
def cities_upgrader_v1(token_data: dict, scopes: set, city_id: int):

    user_id = token_data['user']['id']

    to_id = None
    if scope.Transport.ADMIN in scopes:
        to = token_data['transport_organization']
        to_id = to['id']
        city_id_from_token = to['city']['id']
        if city_id_from_token != city_id:
            raise BaseInobiException('You have no access to status of this city',
                                     code=error_codes.ACCESS_DENIED, http_code=403)
        city_id = city_id_from_token

    if request.method == 'POST':
        status = start_upgrade_process(city_id, to_id=to_id, user_id=user_id)
        return http_ok(process=status)

    return http_ok(processes=get_status(city_id, to_id=to_id, user_id=user_id))


@bp.route('/v1/cities/<int:city_id>/upgrader/<db_name>/', methods='POST GET DELETE'.split())
@cross_origin()
@secured([scope.Transport.ADMIN, ])
@converted
def cities_upgrader_process_v1(token_data: dict, scopes: set,
                               city_id, db_name,
                               apply: Modifier.BOOL = True):

    user_id = token_data['user']['id']

    p = get_status(city_id, process_name=db_name)
    if p is None:
        return http_err('Not Found', 404, error_code=error_codes.PROCESS_NOT_FOUND, process_name=db_name)

    if request.method == 'POST':
        if apply:
            apply_city_db(city_id, db_name)
            return http_ok(process=p, applied=True)

    elif request.method == 'DELETE':
        if p['process']:
            os.kill(p['process']['pid'], signal.SIGTERM)
        os.unlink(p['_fp'])

    return http_ok(process=p)

