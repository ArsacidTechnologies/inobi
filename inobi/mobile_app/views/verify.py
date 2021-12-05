from datetime import datetime

from flask import request, url_for, redirect
from flask_cors import cross_origin
from validate_email import validate_email

from inobi.config import APP_REGION
from inobi.utils import validate_phone_number, http_err, http_ok
from inobi.utils.converter import converted, Modifier
from .. import route, error_codes, utils
from ..db import user as db
from ..db.contact_verification import fetch_contact
from ..security import verify_contact
from ... import config


@route('/v1/login/check')
@cross_origin()
@converted
def app_check_login_v1(value: str, region: str = APP_REGION):
    phone = validate_phone_number(value, region)

    if phone:
        is_verified = True if fetch_contact(phone, "phone") else False
        db_answer = db.fetch_user_by_login(phone or "", phone or "", phone)
        is_shahkar_verified = verify_contact.check_shahkar(phone_number=phone,
                                                           national_code=db_answer.user.national_code)
        return http_ok(is_registered=db.is_registered(phone=phone), type='phone',
                       value=phone, region=region, is_verified=is_verified,
                       is_shahkar_verified=is_shahkar_verified)

    email = value if validate_email(value) else None

    if email:
        if config.APP_REGION == "IR":
            return http_err('Email for iranian users are disabled.',
                    status=400, error_code=error_codes.EMAL_FOR_IRAN_RESTRICTED)
        is_verified = True if fetch_contact(email, "email") else False
        return http_ok(is_registered=db.is_registered(email=email), type='email',
                       value=email, is_verified=is_verified)

    return http_err('Value Must Be A Valid Phone Number or Email Address',
                    status=400,
                    error_code=error_codes.VALUE_MUST_BE_VALID_EMAIL_OR_PHONE)


@route('/v1/restore_access')
@cross_origin()
@converted(rest_key='rest')
def app_restore_access_v1(contact: str, rest: dict,
                          new_pwd: Modifier.MINIMUM_SIZED_STRING(6) = None,
                          code: str = None, national_code: str = None,
                          region: str = APP_REGION):

    phone = validate_phone_number(contact, region)

    if phone:
        if not db.is_registered(phone=phone):
            return http_err('User is not registered with this contact (phone: {})'.format(phone),
                            400, error_code=error_codes.NO_USER_REGISTERED_WITH_GIVEN_CONTACT)
        if not code:
            return redirect(url_for(app_verify_phone_v1.__name__,
                                    value=phone, region=region, **rest))
        elif not new_pwd:
            return http_err("No Valid 'new_pwd' Parameter Presents", 400,
                            "Password Must Be At Least 6-Character Length",
                            error_code=error_codes.NO_PASSWORD_PARAMETER_PRESENTS_OR_IS_NOT_VALID)
        else:
            if (national_code):
                user = db.fetch_user_by_phone(phone)
                national_code = national_code or user.national_code

                try:
                    national_code = utils.valid_iranian_national_id(national_code)
                except ValueError:
                    return http_err('National code is invalid', 400,
                                    error_code=error_codes.NATIONAL_CODE_IS_NOT_VALID)
                status = bool(national_code)
                if user.national_code:
                    status = verify_contact.check_shahkar(phone_number=phone, national_code=national_code)
                elif national_code:
                    status = verify_contact.register_shahkar(phone_number=phone, national_code=national_code)

                if (not status) or (not (national_code and user.national_code)):
                    return http_err('Shahkar can not be verified..', 400, error_code=error_codes.SHAHKAR_VERIFY_FAILED)
                elif status and (not user.national_code) and national_code:
                    db.update_national_code(national_code, phone=phone)

            try:
                contact = verify_contact.check_phone(phone, code, cleanup_on_success=False)
            except verify_contact.ContactVerificationException:
                raise
            else:
                # ... do stuff
                new_login, prev_login = db.update_password(phone=phone, password=new_pwd)

                verify_contact.clean_phone_verification(phone)

                return http_ok(login=new_login._asdict(), prev=prev_login._asdict())

    email = contact if validate_email(contact) else None

    if email:
        if config.APP_REGION == "IR":
            return http_err('Iranian users can\'t restore access with email.'.format(email),
                            401, error_code=error_codes.EMAL_FOR_IRAN_RESTRICTED)

        if not db.is_registered(email=email):
            return http_err('User is not registered with this contact (email: {})'.format(email),
                            400, error_code=error_codes.NO_USER_REGISTERED_WITH_GIVEN_CONTACT)

        if not code:
            return redirect(url_for(app_verify_email_v1.__name__, value=email, region=region, **rest))
        elif not new_pwd:
            return http_err("No Valid 'new_pwd' Parameter Presents", 400,
                            "Password Must Be At Least 6-Character Length",
                            error_code=error_codes.NO_PASSWORD_PARAMETER_PRESENTS_OR_IS_NOT_VALID)
        else:
            try:
                contact = verify_contact.check_email(email, code, cleanup_on_success=False)
            except verify_contact.ContactVerificationException:
                raise
            else:
                # ... do stuff
                new_login, prev_login = db.update_password(email=email, password=new_pwd)

                verify_contact.clean_email_verification(email)

                return http_ok(login=new_login._asdict(), prev=prev_login._asdict())

    return http_err('Contact Must Be A Valid Phone Number or Email Address',
                    status=400,
                    error_code=error_codes.VALUE_MUST_BE_VALID_EMAIL_OR_PHONE)


@route('/v1/verify/phone')
@cross_origin()
@converted
def app_verify_phone_v1(value: str, region: str = APP_REGION, code: str = None,
                        check: Modifier.BOOL = False, national_code: str = None,
                        method: verify_contact.VerificationMethod.check = verify_contact.VerificationMethod.SMS,
                        lang: verify_contact.Language.check = verify_contact.Language.EN):
    phone = validate_phone_number(value, region)
    if phone is None:
        return http_err('Phone is Not Valid', 400, error_code=error_codes.PHONE_IS_NOT_VALID)

    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if code is not None or check:
        if (config.APP_REGION == "IR") or (national_code):
            user = db.fetch_user_by_phone(phone)
            national_code = national_code or user.national_code

            try:
                national_code = utils.valid_iranian_national_id(national_code)
            except ValueError:
                return http_err('National code is invalid', 400,
                                error_code=error_codes.NATIONAL_CODE_IS_NOT_VALID)
            status = bool(national_code)
            if user.national_code:
                status = verify_contact.check_shahkar(phone_number=phone, national_code=national_code)
            elif national_code:
                status = verify_contact.register_shahkar(phone_number=phone, national_code=national_code)

            if (not status) or (not (national_code and user.national_code)):
                return http_err('Shahkar can not be verified..', 400, error_code=error_codes.SHAHKAR_VERIFY_FAILED)
            elif status and (not user.national_code) and national_code:
                db.update_national_code(national_code, phone=phone)

        try:
            contact = verify_contact.check_phone(phone, code, check=check)
        except verify_contact.ContactVerificationException as e:
            status = verify_contact.get_phone_status(value=phone, status_type="check")
            return http_err(e.msg, 400, error_code=error_codes.TOO_MANY_CHECK_ATTEMPTS, **status)
        else:
            status = verify_contact.get_phone_status(value=phone, status_type="check")
            return http_ok(date=current_date, verified=contact.asdict(), **status)

    try:
        request_id = verify_contact.send_phone_verification(
            phone=phone, method=method,
            language=lang,
            client_ip=request.remote_addr
        )
    except verify_contact.ContactVerificationException as e:
        status = verify_contact.get_phone_status(value=phone, status_type="send")
        return http_err(e.msg, 400, error_code=error_codes.TOO_MANY_SEND_ATTEMPTS, **status)

    d = dict(
        phone=phone,
        method=method,
        lang=lang,
        ip=request.remote_addr,
        id=request_id,
    )
    status = verify_contact.get_phone_status(value=phone, status_type="send", request_id=request_id)
    return http_ok(date=current_date, request=d, **status)


@route('/v1/verify/email')
@cross_origin()
@converted
def app_verify_email_v1(value: Modifier.EMAIL, code: str = None, check: Modifier.BOOL = False):
    if config.APP_REGION == "IR":
        return http_err('Iranian users can\'t restore access with email.'.format(value),
                        401, error_code=error_codes.EMAL_FOR_IRAN_RESTRICTED)

    email = value
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if code is not None or check:
        try:
            contact = verify_contact.check_email(email, code, check=check)
        except verify_contact.ContactVerificationException as e:
            status = verify_contact.get_email_status(email, status_type="check")
            return http_err(e.msg, 400, error_code=error_codes.TOO_MANY_CHECK_ATTEMPTS, **status)
        else:
            status = verify_contact.get_email_status(email, status_type="check")
            return http_ok(date=current_date, verified=contact.asdict(), **status)

    try:
        request_id = verify_contact.send_email_verification(email)
    except verify_contact.ContactVerificationException as e:
        status = verify_contact.get_email_status(value=email, status_type="send")
        return http_err(e.msg, 400, error_code=error_codes.TOO_MANY_SEND_ATTEMPTS, **status)

    d = dict(
        id=request_id,
        email=email,
    )

    status = verify_contact.get_email_status(value=email, status_type="send", request_id=request_id)
    return http_ok(date=current_date, request=d, **status)


@route('/v1/verify')
@cross_origin()
@converted(rest_key='rest')
def app_verify_v1(value: str, rest: dict, region: str = APP_REGION):

    phone = validate_phone_number(value, region)

    if phone:
        return redirect(url_for('App.app_verify_phone_v1', value=phone, region=region, **rest))

    email = value if validate_email(value) else None

    if email:
        return redirect(url_for('App.app_verify_email_v1', value=email, **rest))

    return http_err('Value Must Be A Valid Phone Number or Email Address',
                    status=400, error_code=error_codes.VALUE_MUST_BE_VALID_EMAIL_OR_PHONE)


@route('/v1/timeout/status')
@cross_origin()
@converted()
def app_verify_timeout_status(value: str, region: str = APP_REGION):

    phone = validate_phone_number(value, region)
    email = value if (validate_email(value) and config.APP_REGION != "IR") else None

    if (not phone) and (not email):
        return http_err('Value is Not Valid', 400, error_code=error_codes.VALUE_MUST_BE_VALID_EMAIL_OR_PHONE)

    if email:
        success_message = verify_contact.get_email_status(email)
    elif phone:
        success_message = verify_contact.get_phone_status(phone)
    else:
        return http_err(
            "Invalid value entered/Email for iran is restricted.",
            400,
            error_code=error_codes.EMAL_FOR_IRAN_RESTRICTED
        )

    if not success_message:
        return http_err(
            "User has not tried verification or it's ban duration has expired",
            400,
            error_code=error_codes.REQUEST_VERIFICATION_EXPIRED_OR_NOT_EXISTS
        )

    return http_ok(data=success_message)