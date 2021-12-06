from inobi import db
from sqlalchemy.orm import backref
from inobi.transport.configs import AudioConfig, AUDIO_RESOURCES, TKeys
import os
import json
from sqlalchemy import Index, func, ForeignKeyConstraint
from datetime import datetime
from inobi.redis import getredis
from inobi.config import RedisSegments


class PlatformTimeTravel(db.Model):
    __tablename__ = 'platform_time_travel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id', ondelete="CASCADE"))
    transport_id = db.Column(db.Integer, db.ForeignKey('transports.id', ondelete="CASCADE"))
    entry_time = db.Column(db.Float)
    leave_time = db.Column(db.Float)
    time = db.Column(db.DateTime, default=datetime.now, server_default=func.now())

    def as_report(self):
        transport = self.transport
        driver = transport.user
        data = {
            "enrty_time": self.entry_time,
            "leave_time": self.leave_time,
            "duration": self.leave_time - self.entry_time,
            "transport": transport.name if transport.name else transport.device_id,
            "type": transport.route.type,
            "driver": driver.name if driver else None
        }
        return data


Index('platform_time_travel_ind', PlatformTimeTravel.time, PlatformTimeTravel.platform_id, unique=False)


class Transports(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(100), nullable=False, unique=True)
    line_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False)
    device_phone = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    independent = db.Column(db.Boolean, default=True)
    payload = db.Column(db.Text, nullable=True)
    driver = db.Column(db.Integer, unique=True)
    device_type = db.Column(db.String(100), nullable=True)
    ip = db.Column(db.String(100), nullable=False)
    port = db.Column(db.SmallInteger, nullable=False)
    tts = db.Column(db.Integer, nullable=False)

    platforms_travel_time = db.relationship('PlatformTimeTravel', lazy='dynamic', backref='transport',
                                            order_by=PlatformTimeTravel.id)

    def as_dict(self, full=False, route=False, driver=False):
        if self.payload:
            try:
                payload = json.loads(self.payload)
            except json.JSONDecodeError:
                payload = self.payload
        else:
            payload = self.payload
        data = {
            "id": self.id,
            "device_id": self.device_id,
            "line_id": self.line_id,
            "device_phone": self.device_phone,
            "name": self.name,
            "payload": payload,
            "driver": self.driver
        }
        return data

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, dict(id=self.id,
                                                             device_id=self.device_id,
                                                             route_id=self.line_id,
                                                             ))

    def __repr__(self):
        return str(self)


class StationPlatforms(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('stations.id', ondelete="CASCADE"), primary_key=True)
    pos = db.Column(db.Integer)
    entry_id = db.Column(db.Integer, db.ForeignKey('platforms.id', ondelete="CASCADE"), primary_key=True, unique=True)


Index('station_platform_unique', StationPlatforms.id, StationPlatforms.entry_id, unique=True)


class RouteDirections(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('routes.id', ondelete="CASCADE"), primary_key=True)
    pos = db.Column(db.Integer)
    entry_id = db.Column(db.Integer, db.ForeignKey('directions.id', ondelete="CASCADE"), primary_key=True, unique=True)


Index('route_directions_unique', RouteDirections.id, RouteDirections.entry_id, unique=True)


class DirectionPlatforms(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('directions.id', ondelete="CASCADE"), primary_key=True)
    pos = db.Column(db.Integer)
    entry_id = db.Column(db.Integer, db.ForeignKey('platforms.id', ondelete="CASCADE"), primary_key=True)


Index('direction_platforms_unique', DirectionPlatforms.id, DirectionPlatforms.entry_id, unique=True)


class Routes(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    from_name = db.Column(db.String(100), nullable=True)
    to_name = db.Column(db.String(100), nullable=True)

    directions = db.relationship('Directions', secondary='route_directions', lazy='dynamic',
                                 backref=backref('routes', lazy='dynamic'),
                                 order_by=RouteDirections.pos, cascade='delete-orphan,delete', single_parent=True)
    transports = db.relationship('Transports', lazy='dynamic', backref='route',
                                 order_by=Transports.id)

    def as_dict(self, full=False, directions=False):
        data = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "from_name": self.from_name,
            "to_name": self.to_name
        }
        if full:
            directions = True
        if isinstance(directions, bool) and directions:
            data['directions'] = [
                d.as_dict(platforms=True) for d in self.directions
            ]
        elif directions is None:
            data['directions'] = []
        return data


class Stations(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=True)

    platforms = db.relationship('Platforms', secondary='station_platforms', lazy='dynamic',
                                backref=backref('stations', lazy='dynamic'),
                                order_by=StationPlatforms.pos, cascade='delete-orphan,delete', single_parent=True)

    def as_dict(self, full=False, platforms=False, platforms_directions=True):
        data = {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name
        }
        if full:
            platforms = True
        if platforms:
            data['platforms'] = [
                p.as_dict(directions=platforms_directions, audios=True) for p in self.platforms
            ]
        return data


class Platforms(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lat = db.Column(db.Float(precision=53), nullable=False)
    lng = db.Column(db.Float(precision=53), nullable=False)

    transports_travel_time = db.relationship('PlatformTimeTravel', lazy='dynamic', order_by=PlatformTimeTravel.id)

    def as_dict(self, full=False, stations=False, directions=False, audios=False, audio_direction_id=None):
        data = {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
        }
        if full:
            stations = True
            directions = True
            audios = True
        if isinstance(stations, bool) and stations:
            s = self.stations.first()
            data['station'] = s.as_dict() if s else None
        elif isinstance(stations, Stations):
            data['station'] = stations.as_dict()
        elif stations is None:
            data['station'] = None
        if directions:
            dirs = []
            for d in self.directions:
                obj = d.as_dict(routes=True)
                dirs.append(obj)
            data['directions'] = dirs
            if audios:
                for direction in dirs:
                    direction['audio'] = {}
                    for lang in AudioConfig.Lang.ALL:
                        direction['audio'][lang] = {}
                        lang_path = os.path.join(AUDIO_RESOURCES, lang)
                        dir_path = os.path.join(lang_path, str(direction['id']))
                        for type in AudioConfig.Type.ALL:
                            direction['audio'][lang][type] = None
                            filename = "{}_{}.{}".format(data['id'], type, AudioConfig.FORMAT)
                            if os.path.exists(os.path.join(dir_path, filename)):
                                direction['audio'][lang][type] = filename
        if audios:
            data['audio'] = {}
            for lang in AudioConfig.Lang.ALL:
                data['audio'][lang] = {}
                lang_path = os.path.join(AUDIO_RESOURCES, lang)
                for type in AudioConfig.Type.ALL:
                    data['audio'][lang][type] = None
                    filename = "{}_{}.{}".format(data['id'], type, AudioConfig.FORMAT)
                    if os.path.exists(os.path.join(lang_path, filename)):
                        data['audio'][lang][type] = filename
                    if audio_direction_id:
                        if os.path.exists(os.path.join(os.path.join(lang_path, str(audio_direction_id)), filename)):
                            data['audio'][lang][type] = filename
        return data


class Directions(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(100), nullable=False)
    line = db.Column(db.Text, nullable=False)

    platforms = db.relationship('Platforms', secondary='direction_platforms', lazy='dynamic',
                                backref=backref('directions', lazy='dynamic'),
                                order_by=DirectionPlatforms.pos)

    def as_dict(self, full=False, platforms=False, routes=False):
        data = {
            "id": self.id,
            "type": self.type,
            "line": self.line
        }
        if full:
            platforms = True
            routes = True
        if platforms:
            data['platforms'] = [
                p.as_dict(stations=True, audios=True, audio_direction_id=self.id) for p in self.platforms
            ]
        if routes is True:
            r = self.routes.first()
            data['route'] = r.as_dict() if r else None
        elif isinstance(routes, Routes):
            data['route'] = routes.as_dict()
        return data


class ExcludeRoutes(db.Model):
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id",  ondelete="CASCADE"), primary_key=True, nullable=False)


class ETAPassesTime(db.Model):
    __tablename__ = "eta_passes_time"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transport_id = db.Column(db.Integer, nullable=True)
    route_id = db.Column(db.Integer, nullable=True)
    route_type = db.Column(db.String(20), nullable=True)
    hour = db.Column(db.Integer, nullable=True)
    quarter = db.Column(db.Integer, nullable=True)
    weekday = db.Column(db.Integer, nullable=True)
    start_platform = db.Column(db.Integer, nullable=True)
    start_time = db.Column(db.Float, nullable=True)
    end_platform = db.Column(db.Integer, nullable=True)
    end_time = db.Column(db.Float, nullable=True)
    time = db.Column(db.DateTime, default=datetime.now, server_default=func.now())






Transport = Transports

Route = Routes
Direction = Directions
Platform = Platforms
Station = Stations

RouteDirection = RouteDirections
DirectionPlatform = DirectionPlatforms
ExcludeRoute = ExcludeRoutes
StationPlatform = StationPlatforms
