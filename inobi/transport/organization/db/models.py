from inobi import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import UniqueConstraint
from inobi.transport.configs import AUDIO_INFO_RESOURCES
import os
from pathlib import Path
from inobi.transport.organization.scopes import Role as Scopes
from inobi.utils import AsDictMixin


transport_organization_platforms = db.Table('transport_organization_platforms',
                                            db.Column('organization',
                                                      db.Integer,
                                                      db.ForeignKey('transport_organizations.id', ondelete="CASCADE"),
                                                      primary_key=True),
                                            db.Column('platform',
                                                      db.Integer,
                                                      db.ForeignKey('platforms.id', ondelete="CASCADE"),
                                                      primary_key=True))

transport_organization_stations = db.Table('transport_organization_stations',
                                           db.Column('organization',
                                                     db.Integer,
                                                     db.ForeignKey('transport_organizations.id', ondelete="CASCADE"),
                                                     primary_key=True),
                                           db.Column('station',
                                                     db.Integer,
                                                     db.ForeignKey('stations.id', ondelete="CASCADE"),
                                                     primary_key=True))


transport_organization_routes = db.Table('transport_organization_lines',
                                        db.Column('organization',
                                                  db.Integer,
                                                  db.ForeignKey('transport_organizations.id', ondelete="CASCADE"),
                                                  primary_key=True),
                                        db.Column('line',
                                                  db.Integer,
                                                  db.ForeignKey('routes.id', ondelete="CASCADE"),
                                                  primary_key=True),
                                        UniqueConstraint('organization', 'line', name='unique_organization_line'))

transport_organization_directions = db.Table('transport_organization_directions',
                                             db.Column('organization',
                                                       db.Integer,
                                                       db.ForeignKey('transport_organizations.id', ondelete="CASCADE"),
                                                       primary_key=True),
                                             db.Column('direction',
                                                       db.Integer,
                                                       db.ForeignKey('directions.id', ondelete="CASCADE"),
                                                       primary_key=True))

transport_organization_transports = db.Table('transport_organization_transports',
                                             db.Column('organization',
                                                       db.Integer,
                                                       db.ForeignKey('transport_organizations.id', ondelete='CASCADE'),
                                                       primary_key=True),
                                             db.Column('transport',
                                                       db.Integer,
                                                       db.ForeignKey('transports.id', ondelete='CASCADE'),
                                                       primary_key=True),
                                             UniqueConstraint('organization', 'transport', name='unique_organization_transport'))


class TransportOrganizations(db.Model, AsDictMixin):
    _asdict_fields = ('id', 'name', 'traccar_username', 'payload', 'city')
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    traccar_username = db.Column(db.String(50))
    traccar_password = db.Column(db.String(50))
    payload = db.Column(db.Text)
    city = db.Column(db.Integer, nullable=False)
    settings = db.Column(JSON, nullable=True)

    platforms = db.relationship('Platforms', secondary=transport_organization_platforms, lazy='dynamic')
    stations = db.relationship('Stations', secondary=transport_organization_stations, lazy='dynamic')
    routes = db.relationship('Routes', secondary=transport_organization_routes, lazy='dynamic')
    directions = db.relationship('Directions', secondary=transport_organization_directions, lazy='dynamic')
    transports = db.relationship('Transports', secondary=transport_organization_transports, lazy='dynamic')


TransportOrganization = TransportOrganizations


import time
from inobi.utils import AsDictMixin

from sqlalchemy import Index


class Notification(db.Model, AsDictMixin):

    _asdict_fields = 'id organization resolved type domain title content attributes payload register_time'.split()

    __tablename__ = 'transport_organization_notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization = db.Column(db.Integer, nullable=False)
    resolved = db.Column(db.Boolean, default=False, server_default=db.true())
    type = db.Column(db.String, nullable=False)

    domain = db.Column(db.String, nullable=False)

    title = db.Column(db.String, nullable=False)

    content = db.Column(db.String, nullable=False)

    attributes = db.Column(db.String, nullable=True)

    payload = db.Column(db.String, nullable=True)

    register_time = db.Column(db.Float, nullable=False, default=time.time,
                              server_default=db.func.extract('epoch', db.func.now()))

    organization_resolved_index = Index('to_notifications_organization_resolved_idx', organization, resolved)

    __table_args__ = (organization_resolved_index, )


class AudioInfo(db.Model):
    __tablename__ = 'transport_organization_audio_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization = db.Column(db.Integer, db.ForeignKey(TransportOrganization.id), nullable=False)
    name = db.Column(db.String, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Float, nullable=False, default=time.time)
    files = db.relationship('AudioInfoFile', lazy='dynamic')

    def asdict(self):
        return {
            "id": self.id,
            "name": self.name,
            "weight": self.weight,
            "time": self.time,
            "files": [
                f.asdict()
                for f in self.files
            ]
        }


class AudioInfoFile(db.Model, AsDictMixin):
    __tablename__ = 'audio_info_file'
    _asdict_fields = ['id', 'filename', 'language', 'md5', 'time']
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    audio_info = db.Column(db.Integer, db.ForeignKey(AudioInfo.id), nullable=False)
    filename = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    md5 = db.Column(db.String, nullable=False)
    time = db.Column(db.Float, nullable=False, default=time.time)

    def remove(self):
        path = Path(AUDIO_INFO_RESOURCES) / self.language / self.filename
        try:
            os.remove(path.as_posix())
        except FileNotFoundError:
            pass


class TransportOrganizationUser(db.Model):
    __tablename__ = 'transport_organization_users'
    __table_args__ = (
        db.UniqueConstraint('organization', 'user', 'role', name='unique_transport_organization_users'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization = db.Column(db.Integer, db.ForeignKey(TransportOrganization.id))
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String, default=Scopes.VIEWER)
