
from flask_cors import cross_origin
from validate_email import validate_email

from inobi.security import secured, sign
from inobi.utils import http_err, http_ok, validate_phone_number
from inobi.utils.converter import converted, Modifier
from .. import route, security as socials, error_codes, utils
from ..config import APP_VERSION, TOKEN_EXPIRES_AFTER, SHAHKAR_CLOSE_REGISTRATION_IMMEDIATELY
from ..db import user as db
from ..db.contact_verification import fetch_contact
from ..security import verify_contact
from ... import config

tag = "@{}:".format(__name__)


def _responsify(db_answer: db.ReturnUser, login_key: str, **kwargs) -> dict:
    user, login, transport, organization, city, is_to_admin, is_driver = db_answer

    scopes = ['application_public', *user.scopes]

    user_d = user._asdict()
    user_d[login_key] = login._asdict()

    payload = dict(user=user_d)

    if is_driver:
        scopes.append('transport_driver')
        payload['transport'] = None
        if transport is not None:
            payload['transport'] = transport._asdict()

    if is_to_admin:
        scopes.append('transport_admin')

        organization = organization._asdict()
        if city is not None:
            organization['city'] = city._asdict()

        payload['transport_organization'] = organization

    payload['user']['scopes'] = scopes
    for kwarg in kwargs.keys():
        if kwargs[kwarg] is not None:
            payload['user'][kwarg] = kwargs[kwarg]

    return http_ok(
        **payload,
        token=sign(
            payload,
            scopes=scopes,
            expires_after=30,
        ),
        simple_token=sign(
            payload,
            scopes=scopes,
            expires_after=30,
            base64ify=False
        ),
        version=APP_VERSION
    )


@route('/v2/login')
@cross_origin()
@converted
def app_login_v2(device_id: Modifier.MINIMUM_SIZED_STRING(17) = None,
                 use_device_id: bool = True,
                 login: str = None,
                 pwd: Modifier.MINIMUM_SIZED_STRING(6) = None,
                 username: str = None,
                 email: Modifier.EMAIL = None,
                 phone: Modifier.PHONE = None,
                 type: Modifier.COLLECTION(*socials.LOGIN_HANDLERS.keys()) = None,
                 token: str = None, jwt: str = None):

    if device_id:
        device_id = device_id.lower()

    if device_id and use_device_id:
        try:
            db_answer = db.fetch_user_by_device_id(device_id)
        except db.InobiException:
            pass
        else:
            return _responsify(db_answer, db.Login.LOGIN_KEY)

    if login and pwd:

        # user, login, transport, organization = db2.fetch_user_by_login(username=username, email=email)
        phone = validate_phone_number(login) or login
        db_answer = db.fetch_user_by_login(phone or "", phone or "", phone or "", device_id=device_id or "")

        login_type = None
        if validate_phone_number(login, config.APP_REGION):
            login_type = 'phone'
        elif validate_email(login):
            login_type = 'email'

        is_verified = False
        if fetch_contact(login, login_type):
            is_verified = True

        if not db_answer.verify(pwd):
            return http_err('Password Incorrect', 400,
                            error_code=error_codes.PASSWORD_INCORRECT)

        return _responsify(db_answer, db.Login.LOGIN_KEY, is_verified=is_verified)

    if pwd and (username or (email or phone)):

        if username and (email or phone):
            return http_err('Username And (Email Or Phone) Parameters Given. Provide Only One of Them',
                            400, error_code=error_codes.SINGLE_CREDENTIAL_REQUIRED)
        if username is None and email is None and phone is None:
            return http_err("'username' or 'email' or 'phone' Parameter Required",
                            400, error_code=error_codes.USERNAME_EMAIL_OR_PHONE_REQUIRED)

        # user, login, transport, organization = db2.fetch_user_by_login(username=username, email=email)
        is_email_verified = True if fetch_contact(email, 'email') else False
        is_phone_verified = True if fetch_contact(phone, 'phone') else False
        is_verified = is_email_verified or is_phone_verified

        db_answer = db.fetch_user_by_login(username or "", email or "", phone or "", device_id=device_id or "")

        if not db_answer.verify(pwd):
            return http_err('Password Incorrect', 400,
                            error_code=error_codes.PASSWORD_INCORRECT)

        return _responsify(db_answer, db.Login.LOGIN_KEY, is_verified=is_verified)

    if type and (token or jwt):

        social_token = token or jwt

        token_data = socials.LOGIN_HANDLERS[type](social_token, True)

        if not token_data:
            return http_err('User Not Verified ({})'.format(type), 400,
                            error_code=error_codes.SOCIALS_TOKEN_NOT_VERIFIED)

        social_user_id = token_data[socials.ID_KEYS[type]]
        # print(type, social_user_id)

        db_answer = db.fetch_user_by_social(type, social_user_id)

        return _responsify(db_answer, db.SocialUser.LOGIN_KEY)

    if login or (username or (email or phone)):
        return http_err('Password Is Invalid', 400, error_code=error_codes.NO_PASSWORD_PARAMETER_PRESENTS_OR_IS_NOT_VALID)
    if pwd:
        return http_err('Login Parameter Required', 400, error_code=error_codes.LOGIN_PARAMETER_REQUIRED)

    if type:
        return http_err('Token Parameter Required', 400, error_code=error_codes.TOKEN_PARAMETER_REQUIRED)
    if token or jwt:
        return http_err('Type Parameter Required', 400, error_code=error_codes.TYPE_PARAMETER_REQUIRED)

    return http_err('Credential Are Required', 400,
                    error_code=error_codes.NO_VALID_CREDENTIALS_PROVIDED)


# THIS API IS FOR IRANIAN PEOPLE REDIRECTED FROM PHP BACKEND ON BOX
# WITH PWA APP
# USE ONLY SHAHKAR AUTH
@route('/v3/login', methods=('POST',))
@cross_origin()
@converted
def app_login_v3(login: Modifier.PHONE = None, pwd: Modifier.MINIMUM_SIZED_STRING(6) = None,
                token: str = None, jwt: str = None):
    if (not login) or (not pwd):
        return http_err('Phone/Password is not valid', 400,
                        error_code=error_codes.PHONE_IS_NOT_VALID)

    phone = validate_phone_number(login)
    if (not phone) or (phone is None):
        return http_err('Phone is not valid', 400,
                        error_code=error_codes.PHONE_IS_NOT_VALID)

    if not pwd:
        return http_err('Password is not valid', 400,
                        error_code=error_codes.PASSWORD_IS_NOT_VALID)

    db_answer = db.fetch_user_by_login(phone, phone, phone)

    is_verified = True
    if not fetch_contact(phone, "phone"):
        is_verified = False

    is_shahkar_verified = True
    if not verify_contact.check_shahkar(phone_number=phone, national_code=db_answer.user.national_code):
        is_shahkar_verified = False

    if not db_answer.verify(pwd):
        return http_err('Password Incorrect', 400,
                        error_code=error_codes.PASSWORD_INCORRECT)

    return _responsify(db_answer, db.Login.LOGIN_KEY,
                       is_verified=is_verified, is_shahkar_verified=is_shahkar_verified)


@route('/v1/update_token')
@cross_origin()
@secured()
@converted
def update_token_v2(token_data, scopes):
    token_data.pop('exp')
    token_data.pop('iat')
    return http_ok(
        token=sign(token_data, scopes=scopes, expires_after=TOKEN_EXPIRES_AFTER),
        transport=token_data.get('transport'),
        transport_organization=token_data.get('transport_organization'),
        user=token_data.get('user')
    )


@route('/v2/register')
@cross_origin()
# @secured('application_inobi')
@converted
def app_register_v2(name: str,
                    email: Modifier.EMAIL = None,
                    phone: Modifier.PHONE = None,
                    birthday: float = None,
                    gender: int = None,
                    national_code: str = None,
                    payload: dict = None,
                    device_id: str = None,
                    username: Modifier.MINIMUM_SIZED_STRING(3) = None,
                    pwd: Modifier.MINIMUM_SIZED_STRING(6) = None,
                    type: Modifier.COLLECTION(*socials.ENTRY_POINT_LOGINS) = None,
                    token: str = None,
                    jwt: str = None):

    if (national_code):
        # if not national_code:       # for the case of config.APP_REGION == "IR"
        #     return http_err('National code is not provided', 400,
        #                     error_code=error_codes.NATIONAL_CODE_NOT_PROVIDED)

        phone = validate_phone_number(phone)
        if not phone:
            return http_err('Phone is not valid', 400,
                            error_code=error_codes.PHONE_IS_NOT_VALID)
        try:
            national_code = utils.valid_iranian_national_id(national_code)
        except ValueError:
            return http_err('National code is invalid', 400,
                            error_code=error_codes.NATIONAL_CODE_IS_NOT_VALID)
        registration_request_id = verify_contact.register_shahkar(phone_number=phone,
                                                                  national_code=national_code)
        if SHAHKAR_CLOSE_REGISTRATION_IMMEDIATELY and registration_request_id:
            verify_contact.close_shahkar(id=registration_request_id, phone_number=phone,
                                         national_code=national_code)
    else:
        national_code = ''

    if not (email or phone):
        return http_err('Email Or Phone Must Be Provided', 400,
                        error_code=error_codes.EMAIL_OR_PHONE_MUST_PRESENT)

    if not (username and pwd) and not (type and token):
        return http_err('Credentials not Provided', 400,
                        error_code=error_codes.CREDENTIALS_NOT_PROVIDED)

    social_token = token or jwt
    social_id = social_payload = None
    if type and social_token:
        token_data = socials.LOGIN_HANDLERS[type](social_token, True)
        if not token_data:
            if not (username and pwd):
                return http_err('Social Token not Approved', 400,
                                error_code=error_codes.SOCIALS_TOKEN_NOT_VERIFIED)
        else:
            social_id = token_data[socials.ID_KEYS[type]]
            social_payload = token_data

    user, social_user, login = db.register_user(
        name=name, email=email, phone=phone, birthday=birthday, payload=payload,
        username=username, pwd=pwd, gender=gender, national_code=national_code,
        social_type=type, social_id=social_id, social_payload=social_payload,
        device_id=device_id, verify_contact=False
    )

    user_d = user._asdict()
    user_d[db.SocialUser.LOGIN_KEY] = social_user._asdict() if social_user is not None else None
    user_d[db.Login.LOGIN_KEY] = login._asdict() if login is not None else None

    payload = dict(user=user_d, transport=None, transport_organization=None)

    scopes = ['application_public', *user.scopes]

    return http_ok(
        **payload,
        version=APP_VERSION,
        token=sign(payload, scopes, expires_after=TOKEN_EXPIRES_AFTER)
    )