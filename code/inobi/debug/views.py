
from flask import request, render_template

from . import bp

from inobi.utils import http_ok, http_err
from inobi.utils.converter import Modifier, converted

from inobi import db
from .db import models


@bp.route('/v1/messages', methods=('GET', 'POST'))
@converted
def messages_v1(iss: str = None, type: str = None, content: str = None,
                service: str = None, to: str = None, time: Modifier.DATETIME = None,
                version: str = None,
                order_by: Modifier.COLLECTION(*models.Message.__table__.columns.keys()) = models.Message.register_time.key,
                desc: Modifier.BOOL = True,
                limit: int = 20,
                offset: int = 0,
                page: Modifier.BOOL = False
                ):

    if request.method == 'POST':

        if None in (iss, type, content):
            return http_err("'iss', 'type' And 'content' Parameters Required and Must Be Strings")

        message = models.Message(issuer=iss, type=type, content=content,
                                 service=service, to=to, issuer_time=time,
                                 version=version)

        db.session.add(message)

        db.session.commit()

        return http_ok(message=message.asdict())

    ms = db.alias(models.Message, 'm')

    messages = db.session.query(ms, db.func.to_timestamp(ms.c.register_time).label('time'))

    if order_by:
        messages = messages.order_by(order_by if not desc else (order_by + ' desc'))

    if iss:
        messages = messages.filter(ms.c.issuer == iss)

    if to:
        messages = messages.filter(ms.c.to == to)

    if service:
        messages = messages.filter(ms.c.service == service)

    if type:
        messages = messages.filter(ms.c.type == type)

    if version is not None:
        messages = messages.filter(ms.c.version == version)

    if limit:
        messages = messages.limit(limit)

    if offset:
        messages = messages.offset(offset)

    messages = messages.all()

    if page:
        return render_template('debug/messages.html', messages=messages, count=len(messages))

    return http_ok(messages=[m._asdict() for m in messages], count=len(messages))
