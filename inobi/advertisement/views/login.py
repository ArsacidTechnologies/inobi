import logging
import typing as T

from flask import request
from flask_cors import cross_origin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from inobi import config as inobi_config, db
from inobi.advertisement.utils.validators import valid_iranian_national_id, valid_mac_address, get_key_from_header, \
    valid_gender
from inobi.mobile_app.security.verify_contact import phone_verifier, ContactVerificationException
from inobi.utils import http_ok, http_err, validate_phone_number, device_description_from_user_agent
from inobi.utils.converter import converted, Modifier
from .. import bp, error_codes
from .. import config
from ..db.models import AdvertisementUser, AdvertisementUserDevice, AdvertisementUserLogin
from ..exceptions import InvalidInputException
from ..utils.shahkar import Shahkar

logger = logging.getLogger(__name__)

RequestId = str


def send_phone_verification(phone, **kwargs) -> T.Optional[RequestId]:
    """Sends verification code to given phone number"""

    try:
        request_id = phone_verifier.send(phone, **kwargs)
    except ContactVerificationException:
        return None
    else:
        return request_id


def check_phone(phone, code, **init_user_kwargs) -> T.Optional[AdvertisementUser]:

    try:
        phone = phone_verifier.check(phone, code)
    except ContactVerificationException:
        return None
    else:
        return AdvertisementUser(phone=phone, **init_user_kwargs)


clean_verification = phone_verifier._clean


def _rebind_device_id(device_id, e=None):
    raise NotImplementedError('Implement rewriting device\'s owner. (device_id: {} has already registered)'.format(device_id), e)


def get_device_description():
    return device_description_from_user_agent(request.user_agent.string)


@bp.route('/v1/login/', methods='GET POST'.split())
@cross_origin()
@converted
def login_v1(phone: str = None,
             device_id: str = None,
             region: str = inobi_config.APP_REGION,
             device_description: str = None,
             ):

    if phone is None and device_id is None:
        return http_err("'phone' Parameter Required", 400)

    phone = validate_phone_number(phone, region)
    if not phone and device_id is None:
        return http_err('Phone is not valid', 400, error_code=error_codes.PHONE_IS_NOT_VALID)

    user = AdvertisementUser.query.options(joinedload(AdvertisementUser.devices))\
        .outerjoin(AdvertisementUserDevice)\
        .filter((AdvertisementUserDevice.mac == device_id) | (AdvertisementUser.phone == phone)) \
        .first()

    if not user:
        return http_err('Not Registered', 401, error_code=error_codes.NOT_REGISTERED)

    device = None

    if device_id and device_id not in (d.mac for d in user.devices):
        device = AdvertisementUserDevice(mac=device_id, description=device_description or get_device_description())
        user.devices.append(device)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            _rebind_device_id(device_id, e)
    else:
        for d in user.devices:
            if d.mac == device_id:
                device = d
                break

    login = AdvertisementUserLogin(device=device)

    user.logins.append(login)

    db.session.add(login)
    db.session.commit()

    d = dict(device=device and device.asdict(), login=login.asdict())

    return http_ok(user=user.asdict(), **d)


@bp.route('/v1/verification/phone/', methods='GET POST'.split())
@cross_origin()
@converted
def verify_v1(phone: str, region: str = inobi_config.APP_REGION):

    phone = validate_phone_number(phone, region)

    if not phone:
        return http_err('Phone is not valid', 400, error_code=error_codes.PHONE_IS_NOT_VALID)

    user = AdvertisementUser.query\
        .filter(AdvertisementUser.phone == phone)\
        .first()

    if user is not None:
        return http_err('User Already Exists', 400, error_code=error_codes.USER_ALREADY_EXISTS)

    if request.method == 'GET':
        return get_verification_v1(phone)
    if request.method == 'POST':
        return post_verification_v1(phone=phone)

    return http_err('Method Not Allowed', 405)


def get_verification_v1(phone, client_mac = None):
    try:
        client_mac = client_mac or get_key_from_header(request, 'device_id', valid_mac_address, '`device_id` is not valid.')
    except Exception:
        pass
    request_id = send_phone_verification(phone, mac=client_mac)
    return http_ok(request={
        'id': request_id,
        'phone': phone,
        'method': 'sms',
        'client_mac': client_mac
    })


@converted
def post_verification_v1(phone, device: AdvertisementUserDevice,
                         code: Modifier.MINIMUM_SIZED_STRING(4),
                         user=None,
                         ):

    _user = check_phone(phone, code)

    if not _user:
        return http_err('Phone Verification Error', 400, error_code=error_codes.VERIFICATION_ERROR)

    user = user or _user

    device.is_verified = True

    login = AdvertisementUserLogin(device=device)
    device.user = user
    user.logins.append(login)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if AdvertisementUser.phone_unique_constraint.name in str(e):
            return http_err('User already Exists', 400, error_code=error_codes.USER_ALREADY_EXISTS)
        else:
            _rebind_device_id(device.mac, e)

    clean_verification(phone)

    return http_ok(user=user.asdict())


""" New APIs """


@bp.route('/v2/login/', methods='GET POST'.split())
@cross_origin()
@converted
def login_v2(phone: str = None,
             national_code: valid_iranian_national_id = None,
             device_id: str = None,
             region: str = inobi_config.APP_REGION):

    device = None

    shahkar = Shahkar(phone, national_code)

    if phone and national_code:
        phone = validate_phone_number(phone, region)
        if not phone:
            return http_err('Phone is not valid', 400, error_code=error_codes.PHONE_IS_NOT_VALID)

        if not shahkar.check():
            return http_err('Invalid parameters for Shahkar service', 400, error_code=error_codes.SHAHKAR_ERROR)

        user = AdvertisementUser.query\
            .filter((AdvertisementUser.phone == phone)) \
            .first()

        if not user:
            return http_err('Not Registered', 401, error_code=error_codes.NOT_REGISTERED)
    else:
        device = None if device_id is None else AdvertisementUserDevice.query\
            .options(joinedload(AdvertisementUserDevice.user))\
            .filter(AdvertisementUserDevice.mac == device_id)\
            .first()

        if device is None:  # or not device.is_verified
            return http_err('Not Registered', 401, error_code=error_codes.NOT_REGISTERED)

        user = device.user

    login = AdvertisementUserLogin(device=device)

    user.logins.append(login)

    db.session.add(login)
    db.session.commit()

    d = dict(device=device and device.asdict(), login=login.asdict())

    return http_ok(user=user.asdict(), **d)


# all actions of this APIs are called by verify_v3.php and App.js->OnLoginV3Submit
@bp.route('/v2/verification/phone/', methods='GET POST'.split())
@cross_origin()
@converted
def verify_v2(phone: str,
              national_code: valid_iranian_national_id = None,
              personal_id: valid_iranian_national_id = None,
              device_id: str = None,
              code: str = None,
              region: str = inobi_config.APP_REGION,
              device_description: str = None,
              fname: str = None,
              lname: str = None,
              gender: int = None,
              age: int = None):

    phone = validate_phone_number(phone, region)
    if not phone:
        return http_err('Phone is not valid', 400, error_code=error_codes.PHONE_IS_NOT_VALID)

    national_code = national_code or personal_id
    shahkar = Shahkar(phone, national_code)

    if request.method == 'GET':
        if not shahkar.check():
            return http_err('Invalid parameters for Shahkar service', 400, error_code=error_codes.SHAHKAR_ERROR)
        return get_verification_v1(phone=phone, client_mac=device_id)

    if request.method == 'POST':
        device = AdvertisementUserDevice.query.filter_by(mac=device_id).first()
        if device is None:
            device = AdvertisementUserDevice(mac=device_id, description=device_description or get_device_description())

        user = AdvertisementUser.query \
            .options(joinedload(AdvertisementUser.devices))\
            .filter(AdvertisementUser.phone == phone)\
            .first()

        if gender:
            try:
                gender = valid_gender(gender)
            except ValueError:
                raise InvalidInputException(msg="`gender` parameter invalid", code=error_codes.GENDER_IS_NOT_VALID)

        return post_verification_v2(user=user, phone=phone, device=device, code=code,
                                    national_code=national_code, shahkar=shahkar, age=age,
                                    fname=fname, lname=lname, gender=gender)

    # if user is not None and device and device in user.devices:
    #     # shahkar_register(phone, national_code)
    #     device.is_verified = True
    #     db.session.add(device)
    #     # todo: do we need this condition at all? just set national_code?
    #     if user.national_code is None or user.national_code != national_code:
    #         user.national_code = national_code
    #         db.session.add(user)
    #     db.session.commit()
    #     return http_err('User Already Exists', 400, error_code=error_codes.USER_ALREADY_EXISTS)

    return http_err('Method Not Allowed', 405)


@converted
def post_verification_v2(phone, device: AdvertisementUserDevice,
                         code: Modifier.MINIMUM_SIZED_STRING(4) = None,
                         user=None, national_code=None, shahkar: Shahkar = None,
                         age=None, fname=None, lname=None, gender=None):

    # FIXME: HERE ABSOLUTELY MUST RAISE ERROR, BECAUSE NO CODE IS PROVIDED
    if user is None:
        user = check_phone(phone, code, age=age, fname=fname, lname=lname, gender=gender)

        if not user:
            return http_err('Phone Verification Error', 400, error_code=error_codes.VERIFICATION_ERROR)

    if shahkar:
        registration_request_id = shahkar.register()
        if config.SHAHKAR_CLOSE_REGISTRATION_IMMEDIATELY and registration_request_id:
            shahkar.close(registration_request_id)

    user.national_code = national_code

    device.is_verified = True

    login_payload = dict()

    if shahkar and shahkar._registration_request_id:
        logger.debug('save shahkar registration_request_id to Login payload: %r', shahkar._registration_request_id)
        login_payload['shahkar_registration_request_id'] = shahkar._registration_request_id

    login = AdvertisementUserLogin(device=device, payload=login_payload or None)
    device.user = user
    user.logins.append(login)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if AdvertisementUser.phone_unique_constraint.name in str(e):
            return http_err('User already Exists', 400, error_code=error_codes.USER_ALREADY_EXISTS)
        else:
            _rebind_device_id(device.mac, e)

    clean_verification(phone)

    return http_ok(user=user.asdict())
