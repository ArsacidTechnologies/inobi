from .. import bp
from inobi.mobile_app.db.models import User, Login, UserLogin
from inobi.utils.converter import converted
from inobi.transport import error_codes as ec
from inobi.mobile_app import error_codes
from inobi.error_codes import PERMISSION_DENIED, DISABLED_TOKEN
from inobi.transport.exceptions import TransportException
from inobi import db
from ..db.models import TransportOrganization as TO, TransportOrganizationUser as TOU
from ..scopes import Role
from inobi.security.scope import Transport as Scope, DISABLED
import json
from inobi.security import sign
from inobi.config import TOKEN_EXPIRES_AFTER
from inobi.utils import http_ok
from inobi.city.models import City
from flask_cors import cross_origin


@bp.route('/v1/login', methods=['POST'])
@cross_origin()
@converted()
def login(username: str, pwd: str):
    login = Login.query.filter(Login.username == username).first()
    if not login:
        raise TransportException('not found', ec.NOT_FOUND, 404)
    if not login.verify(pwd):
        raise TransportException('Password Incorrect', error_codes.PASSWORD_INCORRECT, 401)

    user = db.session.query(User).\
        join(UserLogin, User.id == UserLogin.user).\
        filter(UserLogin.login == login.id).\
        first()

    if not user:
        raise TransportException('not found', ec.NOT_FOUND, 404)

    user_scopes = json.loads(user.scopes) if user.scopes else []

    if DISABLED in user_scopes:
        raise TransportException('Disabled Token', DISABLED_TOKEN, 403)

    data = db.session.query(TO, TOU, City).\
        join(TOU, TOU.organization == TO.id).\
        join(City, TO.city == City.id).\
        filter(TOU.user == user.id).\
        first()
    if not data:
        raise TransportException('not connected to organization', PERMISSION_DENIED, 403)
    organization, organization_user, city = data
    if organization_user.role == Role.ADMIN:
        user_scopes.append(Scope.ADMIN)
    elif organization_user.role == Role.VIEWER:
        user_scopes.append(Scope.VIEWER)
    elif organization_user.role == Role.DRIVER:
        user_scopes.append(Scope.DRIVER)

    payload = {
        "user": {
            "id": user.id,
            "register_time": user.register_time,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "scopes": user_scopes,
            "birthday": user.birthday,
            "payload": json.loads(user.payload) if user.payload else None,
            "login": {
                "id": login.id,
                "register_time": login.register_time,
                "username": login.username
            },
            "social_user": None
        },
        "transport_organization": {
            "id": organization.id,
            "name": organization.name,
            "traccar_username": organization.traccar_username,
            "payload": json.loads(organization.payload) if organization.payload else None,
            "city": {
                "id": city.id,
                "name": city.name,
                "lang": city.lang,
                "country": json.loads(city.country) if city.country else None,
                "db_version": city.db_version,
                "payload": json.loads(city.payload) if city.payload else None,
                "location": {
                    "lat": city.lat,
                    "lng": city.lng,
                    "zoom": city.zoom
                }
            },
            "settings": organization.settings,

        },
        "scopes": user_scopes
    }
    token = sign(payload, scopes=user_scopes, expires_after=TOKEN_EXPIRES_AFTER)
    return http_ok(data=payload, token=token)