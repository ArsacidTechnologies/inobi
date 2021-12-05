import logging
import typing as T
from datetime import datetime, timedelta

import pytz
from flask import request
from flask_cors import cross_origin
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from inobi import config as inobi_config, db
from inobi.advertisement.utils.validators import valid_iranian_national_id, valid_mac_address, valid_gender, \
    get_key_from_header
from inobi.mobile_app.security import verify_contact
from inobi.utils import HTTP_OK_DATA, HTTP_ERR_DATA, validate_phone_number, device_description_from_user_agent, HTTP_OK
from inobi.utils.converter import converted
from .. import bp, error_codes
from .. import config
from ..db.models import AdvertisementUser, AdvertisementUserDevice, AdvertisementUserLogin
from ..exceptions import InvalidInputException
from ..utils.shahkar import Shahkar
from ...redis import getredis

logger = logging.getLogger(__name__)

RequestId = str


def phone_verification_send(phone, mac=None):
    try:
        request_id = verify_contact.ads_send_phone(contact=phone, method='sms',
                                                   language='en', mac=mac)
    except verify_contact.ContactVerificationException as e:
        return {'error': e}
    else:
        return request_id


def phone_verification_check(phone, code, mac=None):
    try:
        phone = verify_contact.ads_check_phone(phone, code, mac=mac)
    except verify_contact.ContactVerificationException as e:
        return {'error': str(e)}
    else:
        return phone


def phone_verification_status(value, request_id=None, status_type="all", mac=None) -> T.Optional[dict]:
    try:
        status = verify_contact.get_phone_status(value=value, status_type=status_type,
                                                 request_id=request_id, mac=mac)
    except verify_contact.ContactVerificationException:
        return None
    else:
        return status


def shahkar_check(phone, national_code):
    shahkar = Shahkar(phone, national_code)
    return shahkar.check()

def shahkar_register(phone, national_code):
    shahkar = Shahkar(phone, national_code)
    return shahkar.register()

def validate_inputs(phone, national_code, gender=None, age=None):
    if phone is None:
        raise InvalidInputException(msg='`phone` Parameter required.', code=error_codes.PHONE_IS_NOT_VALID)
    phone = validate_phone_number(phone, inobi_config.APP_REGION)
    if not phone:
        raise InvalidInputException(msg='Phone is not valid', code=error_codes.PHONE_IS_NOT_VALID)

    if inobi_config.APP_REGION == "IR":
        try:
            national_code = valid_iranian_national_id(national_code)
        except (AssertionError, TypeError, ValueError):
            raise InvalidInputException(msg="`national_code` parameter invalid", code=error_codes.NATIONAL_CODE_NOT_VALID)
        if national_code is None or (not isinstance(national_code, str)):
            raise InvalidInputException(msg="`national_code` parameter invalid", code=error_codes.NATIONAL_CODE_NOT_VALID)
        national_code = national_code.strip()
        if national_code == "":
            raise InvalidInputException(msg="`national_code` parameter invalid", code=error_codes.NATIONAL_CODE_NOT_VALID)

    if gender:
        try:
            gender = valid_gender(gender)
        except ValueError:
            raise InvalidInputException(msg="`gender` parameter invalid", code=error_codes.GENDER_IS_NOT_VALID)

    if not isinstance(age, (int, float)) and age is not None:
        raise InvalidInputException(msg="`age` parameter invalid", code=error_codes.AGE_IS_NOT_VALID)

    return phone, national_code, gender, age


def get_user_status(phone, national_code, client_mac):
    user = AdvertisementUser.query \
        .filter((AdvertisementUser.phone == phone)) \
        .filter((AdvertisementUser.national_code == national_code)) \
        .first()
    is_user_registered = True if user else False

    device = None if client_mac is None else AdvertisementUserDevice.query \
        .options(joinedload(AdvertisementUserDevice.user)) \
        .filter(AdvertisementUserDevice.mac == client_mac) \
        .first()
    is_device_registered = False
    is_device_verified = False
    if device:
        is_device_registered = True if device else False
        if is_device_registered:
            is_device_verified = True if device.is_verified else False

    return (user, device, (is_user_registered, is_device_registered, is_device_verified))


def get_ad_device_description():
    return device_description_from_user_agent(request.user_agent.string)


def _rebind_device_id(device_id, e=None):
    return None
    # raise NotImplementedError('Implement rewriting device\'s owner. (device_id: {} has already registered)'.format(device_id), e)


def update_ad_user_device(user: AdvertisementUser, device: AdvertisementUserDevice, device_values: dict) -> tuple:
    device.last_verified_at = datetime.now()
    device.user = user
    is_updated = device.update(values=device_values)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if AdvertisementUser.phone_unique_constraint.name in str(e):
            return False, ('User already exist', error_codes.USER_ALREADY_REGISTERED)
        return False, (str(e), None)
    if device and user and is_updated:
        return True, None
    return False, None


def create_ad_user_device(user: AdvertisementUser, device_values: dict) -> tuple:
    device = AdvertisementUserDevice(**device_values)
    device.last_verified_at = datetime.now()
    device.user = user
    db.session.add(device)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if AdvertisementUser.phone_unique_constraint.name in str(e):
            return False, ('User already exist', error_codes.USER_ALREADY_REGISTERED)
        return False, (str(e), None)
    if device and user:
        return True, None
    return False, None


def is_user_reached_max_login(user: AdvertisementUser, mac: str,
                              timezone: str = inobi_config.APP_TIMEZONE, status_only: bool = False,
                              use_cache: bool = True) -> tuple:
    block_duration_delta = timedelta(minutes=config.AD_USER_LOGIN_BLOCK_DURATION)
    try:
        r = None if (not use_cache) else getredis()
    except:
        r = None

    if r is None:
        now_time = datetime.now(tz=pytz.timezone(timezone))
        last_logins = db.session.query(AdvertisementUserLogin).filter_by(user_id=user.id). \
            order_by(desc(AdvertisementUserLogin.time)). \
            limit(config.AD_USER_MAX_LOGIN_DAY).all()
        for i in range(len(last_logins)):
            if (now_time - last_logins[i]) > block_duration_delta:
                return True, config.AD_USER_MAX_LOGIN_DAY - i, None
        return False, 0, None

    cache_key = 'adUserAttempts_{}_{}'.format(user.id, mac)
    counter = r.get(cache_key)
    try:
        int_counter = int(counter)
    except (TypeError, ValueError):
        int_counter = 0

    if int_counter <= config.AD_USER_MAX_LOGIN_DAY:
        if not status_only:
            r.incr(cache_key)
            r.expire(cache_key, int(block_duration_delta.total_seconds()))
    else:
        return False, 0, r.ttl(cache_key)
    # at it's last try of available user, and it's calling is because of `connection_status` API, return False
    return True, (config.AD_USER_MAX_LOGIN_DAY - int_counter), None


@bp.route('/v3/login', methods='POST'.split())
@cross_origin()
@converted
def login_v3(phone: str = None,
             national_code: valid_iranian_national_id = None,
             connect: bool = False,
             timezone: str = inobi_config.APP_TIMEZONE):
    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except ValueError as e:
        return HTTP_ERR_DATA(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    try:
        phone, national_code, _, _ = validate_inputs(phone, national_code)
    except InvalidInputException as e:
        return HTTP_ERR_DATA(message=e.msg, error_code=e.code, status=e.http_code or 400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    shahkar_result = shahkar_register(phone, national_code)

    user, device, user_status = get_user_status(phone, national_code, client_mac)
    is_user_registered, is_device_registered, is_device_verified = user_status

    if is_user_registered and is_device_registered and is_device_verified and (user.id == device.user_id):
        connection_duration = int(timedelta(minutes=config.AD_USER_CONNECTION_DURATION).total_seconds())
        allowed, attempts, seconds = is_user_reached_max_login(user=user, mac=client_mac,
                                                               timezone=timezone, status_only=not connect)
        connection_status = {'remaining_attempts': attempts, 'remaining_seconds': seconds,
                             'connection_duration': connection_duration, 'max_attempts': config.AD_USER_MAX_LOGIN_DAY}
        if not allowed:
            # TODO: may be need to add user and device to response
            return HTTP_ERR_DATA('User has used max logins and connections. Try later.',
                                 error_code=error_codes.MAX_CONNECTION_REACHED, status=400,
                                 **dict(connection_status=connection_status, is_logined=False, open_connection="false"))
        output = dict(device=device.asdict(), user=user.asdict(), is_logined=True,
                      open_connection="true", connection_status=connection_status)
        if connect:
            if (inobi_config.APP_REGION == "IR") and (not config.SHAHKAR_DEBUG):
                if shahkar_result is None:
                    return HTTP_ERR_DATA(message="Shahkar register failed", error_code=error_codes.SHAHKAR_CHECK_FAILED, status=400,
                                         **dict(is_logined=False, open_connection="false", connection_status={}))
            login = AdvertisementUserLogin(device=device)
            user.logins.append(login)
            db.session.add(login)
            db.session.commit()
            output.update(dict(login=login.asdict()))
        return HTTP_OK_DATA(**output)

    return HTTP_ERR_DATA("User/Device not found.", status=200, error_code=error_codes.USER_OR_DEVICE_NOT_FOUND,
                        **dict(is_logined=False, open_connection="false", connection_status={}))


@bp.route('/v3/connection/status', methods='POST'.split())
@cross_origin()
@converted
def connection_status(phone: str = None,
                      national_code: valid_iranian_national_id = None,
                      timezone: str = inobi_config.APP_TIMEZONE):
    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except ValueError as e:
        return HTTP_ERR_DATA(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    try:
        phone, national_code, _, _ = validate_inputs(phone, national_code)
    except InvalidInputException as e:
        return HTTP_ERR_DATA(message=e.msg, error_code=e.code, status=e.http_code or 400,
                             **dict(is_logined=False, open_connection=False, connection_status={}))

    user, device, user_status = get_user_status(phone, national_code, client_mac)
    is_user_registered, is_device_registered, is_device_verified = user_status

    if is_user_registered and is_device_registered and is_device_verified and (user.id == device.user_id):
        connection_duration = int(timedelta(minutes=config.AD_USER_CONNECTION_DURATION).total_seconds())
        allowed, attempts, seconds = is_user_reached_max_login(user=user, status_only=True,
                                                               mac=client_mac, timezone=timezone)
        connection_status = {'remaining_attempts': attempts, 'remaining_seconds': seconds,
                             'connection_duration': connection_duration, 'max_attempts': config.AD_USER_MAX_LOGIN_DAY}
        if not allowed:
            # TODO: may be need to add user and device to response
            return HTTP_ERR_DATA('User has used max logins and connections. Try later.', status=200,
                            open_connection=False, error_code=error_codes.MAX_CONNECTION_REACHED,
                            **dict(connection_status=connection_status))
        output = dict(device=device.asdict(), user=user.asdict(),
                      open_connection=True, connection_status=connection_status)
        return HTTP_OK_DATA(**output)

    return HTTP_ERR_DATA("User/Device not found.", status=200, error_code=error_codes.USER_OR_DEVICE_NOT_FOUND,
                        **dict(open_connection=False, connection_status={}))


@bp.route('/v3/send', methods='POST'.split())
@cross_origin()
@converted
def otp_send_v3(phone: str = None,
                national_code: valid_iranian_national_id = None):
    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except ValueError as e:
        return HTTP_ERR_DATA(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    try:
        phone, national_code, _, _ = validate_inputs(phone, national_code)
    except InvalidInputException as e:
        return HTTP_ERR_DATA(message=e.msg, error_code=e.code, status=e.http_code or 400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    if not shahkar_check(phone, national_code):
        return HTTP_ERR_DATA(message="Shahkar check failed", error_code=error_codes.SHAHKAR_CHECK_FAILED, status=400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    user, device, user_status = get_user_status(phone, national_code, client_mac)
    is_user_registered, is_device_registered, is_device_verified = user_status

    is_device_related = False
    if device and user:
        is_device_related = (user.id == device.user_id)

    if is_user_registered and is_device_registered and is_device_verified and is_device_related:
        return HTTP_ERR_DATA(message="User is already registered. Login.",
                             error_code=error_codes.USER_ALREADY_REGISTERED, status=400,
                             **dict(is_otp_sent='false', otp_status={}))

    request_id = phone_verification_send(phone=phone, mac=client_mac)
    otp_status = phone_verification_status(value=phone, request_id=request_id, mac=client_mac)
    if isinstance(request_id, dict):
        return HTTP_ERR_DATA(message=request_id['error'], error_code=error_codes.OTP_SEND_FAILED,
                        **dict(otp_status=otp_status, is_otp_sent='false'), status=400)

    return HTTP_OK_DATA(**dict(is_otp_sent='true', otp_status=otp_status))


@bp.route('/v3/verify', methods='POST'.split())
@cross_origin()
@converted
def otp_verify_v3(phone: str = None,
                  national_code: valid_iranian_national_id = None,
                  code: str = None):
    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except ValueError as e:
        return HTTP_ERR_DATA(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    try:
        phone, national_code, _, _ = validate_inputs(phone, national_code)
    except InvalidInputException as e:
        return HTTP_ERR_DATA(message=e.msg, error_code=e.code, status=e.http_code or 400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    if not shahkar_check(phone, national_code):
        return HTTP_ERR_DATA(message="Shahkar check failed", error_code=error_codes.SHAHKAR_CHECK_FAILED, status=400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    user, device, user_status = get_user_status(phone, national_code, client_mac)
    is_user_registered, is_device_registered, is_device_verified = user_status

    is_device_related = None
    if device and user:
        is_device_related = (user.id == device.user_id)

    if is_user_registered and is_device_registered and is_device_verified and (is_device_related == True):
        return HTTP_ERR_DATA(message="User is already registered. Login.",
                        error_code=error_codes.USER_ALREADY_REGISTERED, status=400,
                        **dict(is_code_valie=False, otp_status={}, need_register=False))

    phone = phone_verification_check(phone=phone, code=code, mac=client_mac)
    otp_status = phone_verification_status(value=phone, mac=client_mac)
    if isinstance(phone, dict):
        return HTTP_ERR_DATA(message=phone['error'], error_code=error_codes.OTP_CHECK_FAILED, status=400,
                        **dict(is_code_valie=False, otp_status=otp_status, need_register=False))

    success_message, need_register = None, None
    if is_user_registered:
        if is_device_related == False:
            updated, e = update_ad_user_device(
                user, device, device_values=dict(mac=client_mac, description=get_ad_device_description()))
            if not updated:
                return HTTP_ERR_DATA(message='Device update failed.' if (not e) else e[0], status=400,
                                error_code=error_codes.DEVICE_UPDATE_FAILED if ((not e) or (not e[1])) else e[1])
            success_message, need_register = "Code validated and device updated successfully.", False
        else:
            created, e = create_ad_user_device(
                user, device_values=dict(mac=client_mac, description=get_ad_device_description()))
            if not created:
                return HTTP_ERR_DATA(message='Device creation failed.' if (not e) else e[0], status=400,
                                error_code=error_codes.DEVICE_CREATE_FAILED if ((not e) or (not e[1])) else e[1])
            success_message, need_register = "Code validated and device created successfully.", False

    return HTTP_OK_DATA(message=success_message or 'Verification succeed.',
                        **dict(is_code_valid=True, otp_status=otp_status,
                        need_register=need_register if (need_register != None) else True))


@bp.route('/v3/register', methods='POST'.split())
@cross_origin()
@converted
def register_v3(phone: str = None,
                national_code: valid_iranian_national_id = None,
                fname: str = None,
                lname: str = None,
                gender: int = None,
                age: int = None):
    try:
        client_mac = get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except ValueError as e:
        return HTTP_ERR_DATA(message=str(e), error_code=error_codes.MAC_ADDRESS_NOT_VALID, status=400)

    try:
        phone, national_code, gender, age = validate_inputs(phone, national_code, gender=gender, age=age)
    except InvalidInputException as e:
        return HTTP_ERR_DATA(message=e.msg, error_code=e.code, status=e.http_code or 400,
                             **dict(is_logined=False, open_connection="false", connection_status={}))

    # if not shahkar_check(phone, national_code):
    #     return HTTP_ERR_DATA(message="Shahkar check failed", error_code=error_codes.SHAHKAR_CHECK_FAILED, status=400,
    #                          **dict(is_logined=False, open_connection="false", connection_status={}))

    user, device, user_status = get_user_status(phone, national_code, client_mac)
    is_user_registered, is_device_registered, is_device_verified = user_status
    if is_user_registered:
        return HTTP_ERR_DATA(message="User is already registered. Try to verify device.",
                        error_code=error_codes.USER_ALREADY_REGISTERED, status=400)

    user = AdvertisementUser(phone=phone, national_code=national_code, fname=fname, lname=lname, gender=gender, age=age)
    if is_device_registered:
        updated, e = update_ad_user_device(
            user, device, device_values=dict(mac=client_mac, description=get_ad_device_description()))
        if not updated:
            return HTTP_ERR_DATA(message='Device update failed.' if (not e) else e[0], status=400,
                            error_code=error_codes.DEVICE_UPDATE_FAILED if ((not e) or (not e[1])) else e[1])
        success_message = "Register completed and device updated successfully."
    else:
        created, e = create_ad_user_device(
            user, device_values=dict(mac=client_mac, description=get_ad_device_description()))
        if not created:
            return HTTP_ERR_DATA(message='Device creation failed.' if (not e) else e[0], status=400,
                            error_code=error_codes.DEVICE_CREATE_FAILED if ((not e) or (not e[1])) else e[1])
        success_message = "Register completed and device created successfully."

    return HTTP_OK(message=success_message or 'Registration completed.', status=201)




