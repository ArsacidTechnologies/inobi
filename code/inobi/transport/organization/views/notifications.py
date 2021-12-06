
import datetime

import operator

from flask import request, abort, render_template
from flask_socketio import emit
from flask_cors import cross_origin

from .. import bp

from inobi.transport import configs as transport_config

from inobi.security import secured, scope
from inobi.utils import http_ok, http_err
from inobi.utils.converter import converted, Modifier

from ...DataBase.classes import TransportOrganization

from ... import error_codes

from ..utils import transport_organization_from_token, user_from_token


from ..db.notifications import Notification

from ..db import models
from inobi.transport.DataBase import models as transport_models
from inobi import db
from inobi.mobile_app.db import models as app_models

from ...exceptions import TransportException


@bp.route('/v1/notifications', methods=('POST',))
@cross_origin()
@secured(scope.Transport.ADMIN)
def alerts_v1(token_data):

    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    admin = user_from_token(token_data)
    return post_alerts_v1(to=transport_organization)


@bp.route('/v1/notifications', methods=('GET',))
@cross_origin()
@secured(scope.Transport.VIEWER)
def alerts_v1_get(token_data):

    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    return get_alerts_v1(to=transport_organization)


@bp.route('/v1/notifications/demo', methods=('GET', ))
@secured(scope.Transport.ADMIN)
def alerts_demo_v1(token_data):
    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    admin = user_from_token(token_data)

    import json

    return render_template('transport/notifications.html', notifications=Notification.get_all(transport_organization.id), json=json)


@bp.route('/v1/notifications/<int:notification_id>', methods=('GET', 'PATCH'))
@cross_origin()
@secured(scope.Transport.ADMIN)
def alerts_by_id_v1(token_data, notification_id):

    transport_organization = transport_organization_from_token(token_data)
    if not isinstance(transport_organization, TransportOrganization):
        return http_err('No Organization in Token Payload', 403,
                        error_code=error_codes.NO_ORGANIZATION_TOKEN_PAYLOAD)

    admin = user_from_token(token_data)

    if request.method == 'GET':
        return get_alerts_by_id_v1(id=notification_id, to=transport_organization)
    if request.method == 'PATCH':
        return patch_alert_by_id_v1(id=notification_id, to=transport_organization)

    abort(405)


def get_alerts_by_id_v1(to: TransportOrganization, id: int):
    notification = Notification.get_by_id(to.id, id=id)
    if notification is None:
        return http_err('Not Found', 404, error_code=error_codes.NOTIFICATION_NOT_FOUND)
    return http_ok(notification=notification._asdict())


@converted
def patch_alert_by_id_v1(id: int, to: TransportOrganization, **values):

    notification = Notification.make_to_update(id, to.id, values).resolve()
    if notification is None:
        return http_err('Not Found', 404, error_code=error_codes.NOTIFICATION_NOT_FOUND)

    emit(transport_config.Event.NOTIFICATION,
         dict(type=transport_config.Event.NotificationType.DELETE, payload=notification.id),
         room=transport_config.Room.notification(to.id),
         namespace=transport_config.WS_ADMIN_NAMESPACE)

    return http_ok(notification=notification._asdict())


@converted
def post_alerts_v1(type: str, domain: str,
                   title: str, content: str,
                   attributes: dict = None, payload: dict = None,
                   resolved=False,
                   to: TransportOrganization = None):
    notification = Notification.add(to.id, type, domain, title, content, attributes, payload, resolved=resolved)
    nd = notification._asdict()
    data = dict(type=transport_config.Event.NotificationType.ADD, payload=nd)
    emit(transport_config.Event.NOTIFICATION,
         data,
         room=transport_config.Room.notification(to.id),
         namespace=transport_config.WS_ADMIN_NAMESPACE)
    return http_ok(notification=nd)


@converted
def get_alerts_v1(to: TransportOrganization, resolved: Modifier.BOOL = False,
                  order_by: Modifier.COLLECTION(Notification._fields) = 'register_time',
                  desc: Modifier.BOOL = True,
                  from_time: Modifier.DATETIME = None,
                  to_time: Modifier.DATETIME = None
                  ):

    n = db.alias(models.Notification, 'n')

    order_by_c = getattr(n.c, order_by)

    q = db.session.query(n)\
        .filter(n.c.resolved == resolved)\
        .filter(n.c.organization == to.id)\
        .order_by(order_by_c.desc() if desc else order_by_c)

    if not from_time and not to_time:
        to_time = datetime.datetime.now()
        from_time = to_time - datetime.timedelta(days=7)
    elif to_time and from_time:
        pass
    else:
        raise TransportException('{!r} and {!r} parameters are required alongside each other'.format('from_time', 'to_time'),
                                 error_codes.TIME_BOUNDS_REQUIRED)

    q = q.filter(n.c.register_time.between(db.func.extract('epoch', from_time), db.func.extract('epoch', to_time)))

    # ns = Notification.get_all(to.id, resolved=resolved,
    #                           order_by=order_by, desc=desc,
    #                           from_time=from_time,
    #                           to_time=to_time,
    #                           )

    mapper = operator.methodcaller('_asdict')

    ns = q.all()

    return http_ok(count=len(ns), notifications=list(map(mapper, ns)))


from ...notification_configs.transport_speed_violation import DOMAIN as SPEED_VIOLATION_DOMAIN


@bp.route('/v1/reports/notifications/<domain>/', methods=('GET', ))
@cross_origin()
@secured([scope.Transport.VIEWER, ])
@converted
def get_notifications_report_v1(domain, from_time: Modifier.DATETIME, to_time: Modifier.DATETIME, transport: int):

    if domain not in (SPEED_VIOLATION_DOMAIN, ):
        raise TransportException('reports for given domain is not implemented (domain: {})'.format(domain),
                                 error_codes.UNKNOWN_NOTIFICATIONS_DOMAIN,
                                 404)

    session = db.session

    n = db.alias(models.Notification, 'n')
    r = db.alias(transport_models.Route, 'r')
    t = db.alias(transport_models.Transport, 't')
    u = db.alias(app_models.User, 'u')

    q = session.query(
        n.c.id,
        n.c.organization,
        n.c.domain,
        n.c.register_time,
        n.c.attributes.cast(db.JSON).label('attributes'),
        n.c.payload.cast(db.JSON).label('payload')
    ).select_from(n)\
        .filter(db.func.to_timestamp(n.c.register_time).between(from_time, to_time))

    sub = q.subquery('q')

    attrs_c = sub.c.attributes
    payload_c = sub.c.payload

    q = session.query('id', 'register_time',
                      attrs_c['speed'].cast(db.String).cast(db.Float).label('speed'),
                      payload_c['id'].cast(db.String).cast(db.Integer).label('transport_id'),
                      payload_c['line_id'].cast(db.String).cast(db.Integer).label('route_id'),
                      db.case([
                          (payload_c['driver_id'].is_(db.null()), db.null())
                      ], else_=payload_c['driver'].cast(db.String).cast(db.Integer)
                      ).label('driver_id'),
                      payload_c['location'].label('location'),
                      payload_c['time'].label('ping_time'),
                      ).select_from(sub)\
        .filter(payload_c['id'].cast(db.String).cast(db.Integer) == transport)

    sub = q.subquery('q')

    q = session.query(sub, u.c.name.label('driver_name'), u.c.phone.label('driver_phone'),
                      r.c.name.label('route_name'), r.c.type.label('route_type'),
                      t.c.name.label('transport_name'), t.c.device_id.label('device_id'))\
        .outerjoin(u, sub.c.driver_id == u.c.id)\
        .outerjoin(t, sub.c.transport_id == t.c.id)\
        .outerjoin(r, sub.c.route_id == r.c.id)\
        .order_by('register_time')

    def mapper(n):
        return n._asdict()

    return http_ok(notifications=list(map(mapper, q)))
