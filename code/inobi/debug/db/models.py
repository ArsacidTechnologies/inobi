

from inobi import db
from inobi.utils import AsDictMixin
import time
from sqlalchemy import func
import datetime as dt


class Message(db.Model, AsDictMixin):

    _asdict_fields = 'id register_time issuer_time issuer service type to content version'.split()

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    register_time = db.Column(db.Float(precision=15), default=time.time, server_default=func.extract('epoch', func.now()), nullable=False)
    issuer_time = db.Column(db.DateTime, nullable=True)
    version = db.Column(db.String, nullable=True)
    issuer = db.Column(db.String, nullable=False)
    service = db.Column(db.String, nullable=True)
    type = db.Column(db.String, nullable=False)
    to = db.Column(db.String, nullable=True)
    content = db.Column(db.String, nullable=False)

    @property
    def time(self):
        return dt.datetime.fromtimestamp(self.register_time)

    def __str__(self):
        return '@{issuer} #{id} ({type}{service}): {content}'.format(
            issuer=self.issuer,
            id=self.id,
            type=self.type,
            service=(' '+self.service) if self.service else '',
            content=self.content if len(self.content) < 120 else '{}...{}'.format(self.content[:114], self.content[-4:])
        )
