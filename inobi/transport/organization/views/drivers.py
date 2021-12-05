
from flask_cors import cross_origin
from flask import request, abort

from inobi.security import secured
from inobi.utils import http_err, http_ok

from ...organization import bp

from inobi.utils.converter import converted, Modifier

import typing as T

from ... import error_codes

from inobi.mobile_app import error_codes as app_error_codes

from inobi.utils import picture_from_base64, PictureDecodeError
from inobi.mobile_app.config import APP_USER_PICTURES_DIRECTORY, join
import uuid

from ..db.drivers import (
    user_db, Driver, DriverLoginTransport, DriverLogin,
    Transport, TransportOrganization,
    drivers_of, update_driver_of, delete_driver_of
)

from ..utils import transport_organization_from_token, user_from_token

from inobi.transport.DataBase.transport_v2 import (get_driver_transports,
                                                   save_driver_transports,
                                                   delete_driver_transports)



def dictify_user_transport(driver: Driver, transport: Transport, with_transport: bool, login: DriverLogin = None) -> dict:
    d = driver._asdict()

    if transport:
        transport = transport._asdict()

    if with_transport:
        d['transport'] = transport

    if isinstance(login, DriverLogin):
        d['login'] = login._asdict()

    return d


@bp.route('/v1/drivers', methods=('GET', 'POST'))
@cross_origin()
@secured('transport_admin')
@converted(rest_key='rest')
def drivers(rest: dict,
            token_data, with_transport: Modifier.BOOL = True,
            name: str = None,
            email: Modifier.EMAIL = None,
            phone: Modifier.PHONE = None,
            birthday: float = None,
            transport: int = None,
            payload: dict = None,
            username: Modifier.MINIMUM_SIZED_STRING(3) = None,
            pwd: Modifier.MINIMUM_SIZED_STRING(6) = None,
            available_transport: list=None,
            internal_name: str = None,
            is_voice_available: bool = None
            ):

    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    admin = user_from_token(token_data)

    if request.method == 'GET':
        drivers_and_transports = drivers_of(transport_organization.id,
                                            with_transport=with_transport)
        return http_ok(drivers=[dictify_user_transport(d, t, with_transport=with_transport, login=l) for d, l, t in drivers_and_transports])

    if request.method == 'POST':
        if name is None:
            return http_err('Name Parameter Required', 400,
                            error_code=error_codes.NAME_PARAMETER_REQUIRED)
        if email is None and phone is None:
            return http_err('Email Or Phone Parameter Required', 400,
                            error_code=app_error_codes.EMAIL_OR_PHONE_MUST_PRESENT)

        pic_name = pic = None
        if 'picture' in rest:
            try:
                pic = picture_from_base64(rest['picture'])
            except PictureDecodeError:
                return http_err('Invalid Picture', 400, error_code=error_codes.INVALID_PICTURE)
            else:
                pic_name = '{}.png'.format(uuid.uuid4())
                payload = dict(payload or {})
                payload['picture'] = pic_name

        if internal_name:
            if payload is None:
                payload = {}
            payload.update(internal_name=internal_name)

        if is_voice_available is not None:
            if payload is None:
                payload = {}
            payload.update(is_voice_available=is_voice_available)
        else:
            if payload is None:
                payload = {}
            payload.update(is_voice_available=False)

        u, su, l = user_db.register_user(
            name=name, email=email, phone=phone, birthday=birthday, payload=payload,
            username=username, pwd=pwd,
            require_crendentials=True,
            transport_id=transport, transport_organization_id=transport_organization.id,
            verify_contact=False, available_transport=available_transport, issuer=admin.id
        )

        # user_d = u._asdict()
        # user_d[user_db.SocialUser.LOGIN_KEY] = su._asdict() if su is not None else None
        # user_d[user_db.Login.LOGIN_KEY] = l._asdict() if l is not None else None

        try:
            ((driver, login, transport), ) = drivers_of(transport_organization.id,
                                                        with_transport=True,
                                                        driver_id=u.id)
        except ValueError:
            return http_err()
        else:
            if pic and pic_name:
                pic.save(join(APP_USER_PICTURES_DIRECTORY, pic_name))
            return http_ok(driver=dictify_user_transport(driver, transport, with_transport=with_transport, login=login))

    return abort(405)


@bp.route('/v1/drivers/<int:driver_id>', methods=('GET', 'DELETE', 'PUT', 'PATCH'))
@cross_origin()
@secured('transport_admin')
@converted(rest_key='driver_params')
def drivers_(driver_id, token_data, driver_params: dict = None, with_transport: Modifier.BOOL = True):

    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    admin = user_from_token(token_data)

    if request.method == 'GET':
        try:
            ((driver, login, transport), ) = drivers_of(transport_organization.id,
                                                        with_transport=with_transport,
                                                        driver_id=driver_id)
        except ValueError:
            return http_err('Not Found', 404,
                            error_code=error_codes.DRIVER_NOT_FOUND)
        else:
            return http_ok(driver=dictify_user_transport(driver, transport, with_transport=with_transport, login=login))

    if request.method == 'DELETE':
        driver_params = delete_driver_of(transport_organization, driver_id=driver_id)
        if driver_params is None:
            return http_err('Not Found', 404, error_code=error_codes.DRIVER_NOT_FOUND)

        driver_params.remove_picture()
        return http_ok(deleted=True, driver=driver_params._asdict())

    if request.method in ('PUT', 'PATCH'):
        if driver_params is None:
            return http_err('Driver Parameters Must Present', 400, error_code=error_codes.EMPTY_DRIVER_PARAMETERS)

        try:
            (driver_transport, ) = drivers_of(transport_organization.id,
                                              with_transport=with_transport,
                                              driver_id=driver_id)
        except ValueError:
            return http_err('Not Found', 404,
                            error_code=error_codes.DRIVER_NOT_FOUND)

        old_driver, *_ = driver_transport

        driver = Driver.make_to_update(id=driver_id, d=driver_params)
        driver_login = DriverLogin.make_to_update(driver_params)

        pic_name = pic = None
        pic_to_delete = None

        old_payload = dict(old_driver.payload or {})

        if 'picture' in driver_params:
            _picture_raw = driver_params['picture']

            pic_to_delete = old_payload.pop('picture', None)

            if _picture_raw:
                try:
                    pic = picture_from_base64(_picture_raw)
                except PictureDecodeError:
                    return http_err('Invalid Picture', 400, error_code=error_codes.INVALID_PICTURE)
                else:
                    pic_name = '{}.png'.format(uuid.uuid4())

        internal_driver_name = old_payload.get('internal_name')

        if 'internal_name' in driver_params:
            internal_driver_name = driver_params['internal_name']

        is_voice_available = old_payload.get('is_voice_available', False)

        if 'is_voice_available' in driver_params:
            if isinstance(driver_params['is_voice_available'], bool):
                is_voice_available = driver_params['is_voice_available']

        if isinstance(driver.payload, dict):
            payload = dict(driver.payload)
            if pic_name and pic:
                payload['picture'] = pic_name
            elif 'picture' in old_payload:
                payload['picture'] = old_payload['picture']

            driver = driver._replace(payload=payload)
        else:
            payload = old_payload
            if pic_name and pic:
                payload['picture'] = pic_name
            driver = driver._replace(payload=payload)

        payload.update(internal_name=internal_driver_name)
        payload.update(is_voice_available=is_voice_available)

        tr_stuff = dict()
        if 'transport' in driver_params:
            tr_stuff['transport'] = driver_params['transport']
        if 'available_transport' in driver_params:
            tr_stuff['available_transport'] = driver_params['available_transport']

        r = update_driver_of(transport_organization, driver, driver_login, tr_stuff)
        if r is None:
            return http_err('Not Found', 404, error_code=error_codes.DRIVER_NOT_FOUND)
        updated_driver, prev_driver, updated_login, prev_login = r

        if pic_name and pic:
            pic.save(join(APP_USER_PICTURES_DIRECTORY, pic_name))
        if pic_to_delete:
            prev_driver.remove_picture()

        return http_ok(
            driver=dictify_user_transport(updated_driver, None, login=updated_login, with_transport=False),
            previous=dictify_user_transport(prev_driver, None, login=prev_login, with_transport=False)
        )

    return abort(405)


@bp.route('/v1/drivers/<int:driver_id>/transports')
@secured('transport_admin')
def driver_transports(driver_id):
    transports = get_driver_transports(driver=driver_id, to_dict=True)
    return http_ok(transports=transports)


