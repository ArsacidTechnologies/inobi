

import typing as T

from flask import send_from_directory

from .. import bp, config as city_config, db, error_codes

import os

from inobi.security import secured, scope

from inobi.utils import http_ok, http_err
from inobi.utils.converter import converted, Modifier

from inobi import config
from inobi.redis import getredis as _getredis, Redis

from flask_cors import cross_origin


getredis = lambda: _getredis(config.RedisSegments.APPLICATION)  # type: T.Callable[[], Redis]


class RedisKey:
    CITY_DB_VERSION = 'cities:database:version'


def get_version_for_city(city_id: int) -> T.Optional[int]:
    # redis = getredis()      # type: Redis
    # redis_value = redis.hget(RedisKey.CITY_DB_VERSION, city_id)
    # if redis_value:
    #     return int(redis_value)
    city = db.City.get_by_id(city_id)
    if city is None:
        return None
    # redis.hset(RedisKey.CITY_DB_VERSION, city_id, city.db_version)
    return city.db_version


def _generate_new_version(db_filepath, city_id: int, data_version: int):

    d, f = os.path.split(db_filepath)

    temp_db_filepath = os.path.join(d, 'v{}.db'.format(data_version))

    os.makedirs(d, exist_ok=True)

    db.dump_city(db_path=temp_db_filepath, city_id=city_id)

    import zipfile
    zf = zipfile.ZipFile(db_filepath, mode='w')
    zf.write(temp_db_filepath, city_config.DB_FILENAME_IN_ARCHIVE, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()

    os.unlink(temp_db_filepath)


@bp.route('/v1/cities', defaults=dict(city_id=None))
@bp.route('/v1/cities/<int:city_id>', methods=('GET', ))
@cross_origin()
def cities_resful_v1(city_id):
    return cities(city_id)


@bp.route('/v1/city')
@converted
def cities_api_v1(id: int):
    return cities(id)


def cities(city_id: int = None):
    if city_id is not None:
        city = db.City.get_by_id(city_id)

        if city is None:
            return http_err('Not Found', 404, error_code=error_codes.CITY_NOT_FOUND)
        return http_ok(city=city._asdict())

    return http_ok(cities=db.City.getall().itemsasdict())


@bp.route('/v1/cities/<int:city_id>/data/version', methods=('GET', ))
@secured([scope.Application.PUBLIC, *scope.Transport.BOXES_V2])
def cities_db_version_restful_v1(city_id, ):
    return city_data_version(city_id)


@bp.route('/v1/city_data_version', methods=('GET', ))
@secured([scope.Application.PUBLIC, *scope.Transport.BOXES_V2])
@converted
def cities_db_version_api_v1(id: int):
    return city_data_version(id)


def city_data_version(city_id):
    version = get_version_for_city(city_id)
    if version is None:
        return http_err('Not Found', 404, error_code=error_codes.CITY_NOT_FOUND)

    return http_ok(version=version)


@bp.route('/v1/cities/<int:city_id>/data/<int:data_version>')
@secured([scope.Application.PUBLIC, *scope.Transport.BOXES_V2])
def cities_db_data_restful_v1(city_id, data_version):
    return cities_data(city_id, data_version)


@bp.route('/v1/city_data')
@secured([scope.Application.PUBLIC, *scope.Transport.BOXES_V2])
@converted
def cities_db_data_api_v1(city: int, version: int):
    return cities_data(city, version)


def cities_data(city_id, data_version):
    db_filepath = city_config.CITY_DB_TEMPLATE.format(city_id=city_id, data_version=data_version)
    d, f = os.path.split(db_filepath)

    response = lambda: send_from_directory(
        directory=d,
        filename=f,
        as_attachment=True,
        attachment_filename='inobi_c{}_v{}.zip'.format(city_id, data_version)
    )

    if os.path.isfile(db_filepath):
        return response()

    city = db.City.get_by_id(city_id)
    if city is None:
        return http_err('City Not Found', 404, error_code=error_codes.CITY_NOT_FOUND)
    if city.db_version != data_version:
        return http_err('No Data Found (Wrong version: {})'.format(data_version), 404,
                        error_code=error_codes.DATABASE_FOR_CITY_NOT_FOUND)

    _generate_new_version(db_filepath, city_id, data_version)

    return response()
