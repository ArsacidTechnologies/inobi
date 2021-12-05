
from datetime import datetime
from time import time as now

from flask import abort, redirect, url_for

from flask_cors import cross_origin

from inobi.security import sign
from inobi.utils import http_err, http_ok

from inobi.utils.converter import converted, Modifier

from .. import route

from ..security import LOGIN_HANDLERS, ID_KEYS
from .. import db


from ..config import TOKEN_EXPIRES_AFTER, APP_VERSION


tag = '@app.views.login:'


@route('/v0/login/<type_>')
@converted
def app_login_v0(type_, token: str = None, jwt: str = None):
    return redirect(url_for(app_login_v1.__name__, type=type_, token=(token or jwt)))


@route('/v1/login')
@cross_origin()
@converted
def app_login_v1(type: str, token: str = None, jwt: str = None):

    input_token = token or jwt

    if type == 'skip':
        # print(type, input_token)
        skip_payload = {
            'type': type,
            'login_id': None,
            'id': None,
            'user_id': None,
            'scopes': [
                'skip', 'application_public'
            ]
        }
        return http_ok(user=None, token=sign(skip_payload, scopes='application', expires_after=TOKEN_EXPIRES_AFTER))

    if type not in LOGIN_HANDLERS:
        return http_err(message='Type is Not Allowed ({})'.format(type), status=400)

    if not input_token:
        return http_err(message='Token is Missing', status=400)

    token_data = LOGIN_HANDLERS[type](input_token, True)

    if not token_data:
        abort(401)

    if type == 'update':
        token_data.pop('exp')
        token_data.pop('iat')
        return http_ok(
            token=sign(token_data, scopes=token_data['scopes'], expires_after=TOKEN_EXPIRES_AFTER),
            transport=token_data.get('transport'),
            transport_organization=token_data.get('transport_organization'),
            user=token_data.get('user')
        )

    social_user_id = token_data[ID_KEYS[type]]
    # print(type, social_user_id)

    token_type = token_data.get('type', type)
    if token_type not in LOGIN_HANDLERS:
        token_type = type

    if social_user_id is not None:
        login_id, registered_user = db.log_login(social_user_id, token_type, token_data)
        # print(registered_user)
        if not registered_user:
            return http_err("Not Registered", 403)
        user_id = registered_user['id']
    else:
        login_id = registered_user = user_id = None

    some_data = {
        'login_id': login_id,
        'type': token_type,
        'id': social_user_id,
        'user_id': user_id,
        'updated': token_data.get('updated', -1) + 1,  # token_data['updated'] + 1 if 'updated' in token_data else 0,
    }

    scopes = ['application_public']
    if registered_user:
        scopes.extend(registered_user['scopes'])

    token = sign(some_data, scopes=scopes, expires_after=TOKEN_EXPIRES_AFTER)

    return http_ok(token=token, app_version=APP_VERSION, user=registered_user)


@route('/v1/register')
@cross_origin()
@converted
def app_register_v1(name: str, type: str,
                    email: Modifier.EMAIL = None, phone: Modifier.PHONE = None,
                    birthday: str = None, payload: dict = None,
                    token: str = None, jwt: str = None):

    if email is None and phone is None:
        return http_err("'email' Or 'phone' Parameter Is Required", 400)

    if birthday is not None:
        try:
            birthday = datetime.strptime(birthday, '%d/%m/%Y').strftime('%d/%m/%Y')
        except ValueError:
            birthday = None
            # return HTTP_ERR("'birthday' Must Be Valid 'dd/MM/yyyy'-like String", 400)

    if type not in LOGIN_HANDLERS:
        return http_err(message='Type is Not Allowed ({})'.format(type), status=400)

    input_token = token or jwt

    if not input_token:
        return http_err(message='Token is Missing', status=400)

    token_data = LOGIN_HANDLERS[type](input_token, True)

    if not token_data:
        abort(401)

    user_id = token_data[ID_KEYS[type]]
    # print(type, user_id)

    login_id, registered_user = db.register_user(name, email, phone, birthday, payload, user_id, type, token_data)
    # login_id, registered_user = register_user_legacy(name, email, birthday, payload, user_id, type, token_data)

    token_type = token_data.get('type', type)
    if token_type not in LOGIN_HANDLERS:
        token_type = type

    scopes = ['application_public']
    if registered_user:
        scopes.extend(registered_user['scopes'])

    some_data = {
        # 'registered_user': registered_user,
        'login_id': login_id,
        'type': token_type,
        'id': user_id,
        'updated': token_data.get('updated', -1) + 1  # token_data['updated'] + 1 if 'updated' in token_data else 0,
    }

    token = sign(some_data, scopes=scopes, expires_after=TOKEN_EXPIRES_AFTER)

    return http_ok(token=token, user=registered_user, app_version=APP_VERSION)
