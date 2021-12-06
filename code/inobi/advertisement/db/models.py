
import datetime as dt
import time

import pytz
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, foreign

from inobi import db
from inobi.utils import AsDictMixin, LocatedMixin, UpdateMixin
from .. import config, utils

datetime = dt.datetime

tag = "@{}:".format(__name__)

import json

import typing as T

from ..exceptions import AdvertisementException as InobiException

from flask import url_for

from inobi import config as inobi_config


class Advertisement(db.Model, AsDictMixin, UpdateMixin):

    __tablename__ = 'ads'

    class Platform:
        WIFI = 1
        ANDROID = 2
        IOS = 4
        BOX = 8

        MOBILE = IOS | ANDROID
        ALL = BOX | WIFI | ANDROID | IOS

        _STR_PLATFORMS = {
            'android': ANDROID,
            'ios': IOS,
            'wifi': WIFI,
            'all': ALL,
            'mobile': MOBILE,
            'box': BOX,
        }

        _EXCLUDE_FROM_STR = frozenset({'all', 'mobile'})

        POSSIBLE_PLATFORM_DESCRIPTORS = tuple(_STR_PLATFORMS.keys())

        @staticmethod
        def platform_fromstr(s) -> int:
            if '|' in s:
                s = s.split('|')
            elif ',' in s:
                s = s.split(',')
            else:
                s = [s]

            p = 0
            for ch in s:
                if ch not in Ad.Platform._STR_PLATFORMS:
                    raise InobiException('Platform not recognized ({}). Options ({})'.format(ch, list(Ad.Platform._STR_PLATFORMS.keys())))
                p = p | Ad.Platform._STR_PLATFORMS[ch]

            return p

        @staticmethod
        def platform_fromint(i) -> str:
            # if (i & Ad.Platform.ALL) == Ad.Platform.ALL:
            #     return 'all'
            return '|'.join(k for k, v in Ad.Platform._STR_PLATFORMS.items() if v & i and k not in Ad.Platform._EXCLUDE_FROM_STR)

    class Radius:
        MIN = config.AD_MIN_RADIUS_PARAMETER
        MAX = config.AD_MAX_RADIUS_PARAMETER
        DEFAULT = config.AD_DEFAULT_RADIUS_PARAMETER

        @staticmethod
        def check_radius(r, _min=MIN, _max=MAX) -> float:
            try:
                radius = float(r)
            except TypeError:
                raise InobiException("'radius' Parameter Expected to Be Floating Point Number Convertible")
            else:
                if not (_min <= radius <= _max):
                    raise InobiException("'radius' Parameter Must Be in [{}:{}] Range".format(_min, _max))
            return radius

    _asdict_fields = (
        'id type duration redirect_url weight views _source:source'
        ' created enabled title description lat lng views_max'
        ' expiration_date requests _platform:platform radius'
        ' cities _time_from:time_from _time_to:time_to start_date'
        ' external_source source:_source'
        ' transport_filters device_filters'
        ' source_full'
        ' display_type'
    ).split()

    _update_fields = (
        'type:_type duration redirect_url:_redirect_url weight:_weight'
        ' external_source source:_source'
        ' enabled title description lat lng views_max'
        ' expiration_date platform:_platform radius:_radius'
        ' cities time_from:_time_from time_to:_time_to start_date '
        ' transport_filters:_transport_filters'
        ' device_filters:_device_filters'
        ' display_type:_display_type'
    ).split()

    @staticmethod
    def time_modifier(x):
        if isinstance(x, dt.time):
            return x
        try:
            time = datetime.strptime(x, '%H:%M:%S').time()
        except ValueError:
            raise InobiException("Time must be in '%H:%M:%S' format")
        return time

    TYPE_BANNER = 'banner'
    TYPE_VIDEO = 'video'
    TYPE_IFRAME = 'iframe'

    TYPES = (TYPE_BANNER, TYPE_VIDEO, TYPE_IFRAME)

    DISPLAY_TYPE_FULLSCREEN = 'fullscreen'
    DISPLAY_TYPE_LIST_ITEM = 'list-item'

    DISPLAY_TYPES = (DISPLAY_TYPE_FULLSCREEN, DISPLAY_TYPE_LIST_ITEM)

    id = db.Column(UUID(as_uuid=False), primary_key=True,
                   server_default=db.func.uuid_generate_v4())
    type = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float(precision=15), nullable=False)
    redirect_url = db.Column(db.String, nullable=False)
    weight = db.Column(db.Integer, nullable=False, default=1)
    views = db.Column(db.Integer, nullable=False, default=0)
    source = db.Column(db.String, nullable=False)
    created = db.Column(db.Float(precision=15), default=time.time, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    lat = db.Column(db.Float(precision=15), nullable=True)
    lng = db.Column(db.Float(precision=15), nullable=True)
    views_max = db.Column(db.Integer, nullable=True)
    expiration_date = db.Column(db.Float(precision=15), nullable=True)
    requests = db.Column(db.Integer, nullable=False, default=0)
    platform = db.Column(db.Integer, nullable=False, default=1023)
    radius = db.Column(db.Float(precision=15), nullable=False, default=0.5)
    transport_filters = db.Column(ARRAY(db.String), nullable=True, default=None)
    cities = db.Column(ARRAY(db.Integer), nullable=True, default=None)
    time_from = db.Column(db.Time, nullable=True)
    time_to = db.Column(db.Time, nullable=True)
    start_date = db.Column(db.Float(precision=15), nullable=True)

    device_filters = db.Column(ARRAY(db.String), nullable=True, default=None)

    chronicles = relationship('AdvertisementChronicle', lazy='dynamic', back_populates='ad', primaryjoin='Advertisement.id == foreign(AdvertisementChronicle.ad_id)', )

    # views already used as column name above
    ad_views = db.relationship('AdvertisementView', back_populates='ad', lazy='dynamic')

    display_type = db.Column(db.String, nullable=False, default=DISPLAY_TYPE_FULLSCREEN, server_default=DISPLAY_TYPE_FULLSCREEN)

    @property
    def _platform(self):
        return self.Platform.platform_fromint(self.platform)

    @_platform.setter
    def _platform(self, value):
        self.platform = self.Platform.platform_fromstr(value)

    def prepare_source(self):
        if not (self.external_source or utils.prepare_source(self.source)):
            raise Exception(tag, 'Could not prepare source: "{}"'.format(self.source))

    @property
    def external_source(self) -> bool:
        return self.source.startswith('!')

    @external_source.setter
    def external_source(self, value):
        current = self.external_source
        if value and not current:
            self.source = '!' + self.source
        if not value and current:
            self.source = self.source[1:]

    @property
    def _source(self):
        return self.source if not self.external_source else self.source[1:]

    @_source.setter
    def _source(self, value):
        self.source = value if not self.external_source else '!'+value

    @property
    def _redirect_url(self) -> str:
        return self.redirect_url

    @_redirect_url.setter
    def _redirect_url(self, value: str):

        if value.startswith('http://'):
            value = value.replace('http://', '', 1)

        if value.startswith('https://'):
            value = value.replace('https://', '', 1)

        self.redirect_url = value

    Coordinate = T.Tuple[float, float]

    @property
    def coordinate(self) -> T.Optional[Coordinate]:
        if self.lat is not None and self.lng is not None:
            return self.lat, self.lng
        return None

    @coordinate.setter
    def coordinate(self, value: T.Optional[Coordinate]):
        if value is None:
            self.lat = self.lng = None
        else:
            self.lat, self.lng = value

    @property
    def _radius(self):
        return self.radius

    @_radius.setter
    def _radius(self, value):
        self.Radius.check_radius(value)
        self.radius = value

    @property
    def _type(self) -> str:
        return self.type

    @_type.setter
    def _type(self, value: str):
        if value not in self.TYPES:
            raise InobiException("'type' Parameter must be one of {}".format(set(self.TYPES)))
        self.type = value

    def _weight(self, value: int):
        if not (0 < value < 11):
            raise InobiException('Weight Parameter Must Be Integer Type And Be In Range [1:10]')
        self.weight = value

    _weight = property(fset=_weight)

    def _transport_filters(self, value: T.List[T.Union[int, str]]):

        if value is None:
            pass
        elif not isinstance(value, list):
            raise InobiException("'transport_filters' Parameter Must Be Array Type", 400)
        elif not value:
            raise InobiException("'transport_filters' Parameter Should Not Be Empty", 400)
        elif not isinstance(value, list) or set(type(i) for i in value).difference((int, str)):
            raise InobiException("'transport_filters' Parameter Must Be List of Integers Or Strings", 400)
        elif all(isinstance(f, str) and f.startswith('!') for f in value):
            raise InobiException(
                "'transport_filters' Parameter Should Contain At Least One Including Filter. Hint: use {} instead".format([*value, 'all']),
                400
            )
        else:
            value = list(map(str, value))

        self.transport_filters = value

    _transport_filters = property(fset=_transport_filters)

    def _device_filters(self, value: T.List[T.Union[int, str]]):

        if value is None:
            pass
        elif not isinstance(value, list):
            raise InobiException("'device_filters' Parameter Must Be Array Type", 400)
        elif not value:
            raise InobiException("'device_filters' Parameter Should Not Be Empty")
        elif set(type(i) for i in value).difference({str, int}):
            raise InobiException("'device_filters' Parameter Must Be An Array of String Or Integer Values")
        elif all(isinstance(f, str) and f.startswith('!') for f in value):
            raise InobiException(
                "'device_filters' Parameter Should Contain At Least One Including Filter. Hint: use {} instead".format([*value, 'all']),
                400
            )
        else:
            value = list(map(str, value))

        self.device_filters = value

    _device_filters = property(fset=_device_filters)

    @property
    def _time_from(self):
        if self.time_from is not None:
            return self.time_from.strftime('%H:%M:%S')

    @_time_from.setter
    def _time_from(self, value):
        if value is not None:
            value = self.time_modifier(value)
        self.time_from = value

    @property
    def _time_to(self):
        if self.time_to is not None:
            return self.time_to.strftime('%H:%M:%S')

    @_time_to.setter
    def _time_to(self, value):
        if value is not None:
            value = self.time_modifier(value)
        self.time_to = value

    @property
    def source_full(self) -> str:
        if self.external_source:
            return self._source
        else:
            return url_for(config.NAME + '.media', filename=self._source, _external=True)

    @property
    def _display_type(self) -> T.Optional[str]:
        return self.display_type

    @_display_type.setter
    def _display_type(self, value: str):
        if value not in self.DISPLAY_TYPES:
            raise InobiException("'type' Parameter must be one of {}".format(set(self.DISPLAY_TYPES)))
        self.display_type = value


Ad = Advertisement


class AdvertisementChronicle(db.Model, AsDictMixin):

    __tablename__ = 'chronicles'

    _asdict_fields = 'client_mac time device box_mac ad_id lat lng redirected _events:events ads_device_id ads_group_id'.split()

    client_mac = db.Column(db.String, nullable=True)
    time = db.Column(db.Float(precision=15), default=time.time, nullable=False)

    device = db.Column(db.String, nullable=True)

    box_mac = db.Column(db.String, nullable=False)

    ad_id = db.Column(UUID(as_uuid=False), nullable=False)

    ad = relationship('Advertisement', primaryjoin=foreign(ad_id) == Ad.id)

    lat = db.Column(db.Float(precision=15), nullable=False)
    lng = db.Column(db.Float(precision=15), nullable=False)

    redirected = db.Column(db.Boolean, nullable=False)

    events = db.Column(db.String, nullable=False)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # _asdict_fields = 'id registered client_mac client_device ad_id device_id group_id lat lng redirected _events:events'.split()

    def __str__(self):
        return '{} ({}), redirected: {}'.format(self.client_mac, self.device, self.redirected)

    @property
    def _events(self):
        if self.events:
            return json.loads(self.events)

    @_events.setter
    def _events(self, value):
        self.events = json.dumps(value)


Chronicle = AdvertisementChronicle


class AdvertisementUser(db.Model, AsDictMixin):

    __tablename__ = 'advertisement_users'

    _asdict_fields = 'id phone national_code gender age registered fname lname'.split()

    phone_unique_constraint = UniqueConstraint('phone', name='advertisement_users_phone_key')

    __table_args__ = (phone_unique_constraint, )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    registered = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())

    national_code = db.Column(db.String, nullable=True)
    fname = db.Column(db.String, nullable=True)
    lname = db.Column(db.String, nullable=True)
    gender = db.Column(db.SmallInteger, nullable=True)
    age = db.Column(db.SmallInteger, nullable=True)
    phone = db.Column(db.String, nullable=False)

    devices = db.relationship('AdvertisementUserDevice', back_populates='user')
    logins = db.relationship('AdvertisementUserLogin', back_populates='user')

    def __str__(self):
        return self.phone


class AdvertisementUserDevice(db.Model, AsDictMixin, UpdateMixin):

    __tablename__ = 'advertisement_user_devices'

    _asdict_fields = 'id user_id mac description is_verified'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mac = db.Column(db.String, unique=True)
    description = db.Column(db.String, nullable=True)

    last_verified_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('advertisement_users.id', ondelete="CASCADE"))
    user = db.relationship('AdvertisementUser', back_populates='devices')

    logins = db.relationship('AdvertisementUserLogin', back_populates='device')

    chronicles = relationship('AdvertisementChronicle', back_populates='user_device', primaryjoin='AdvertisementUserDevice.mac == foreign(AdvertisementChronicle.client_mac)')

    @property
    def is_verified(self) -> bool:
        # if (self.last_verified_at) and dt.datetime.now() - self.last_verified_at < config.USER_DEVICE_VERIFIED_INTERVAL:
        if self.last_verified_at:
            return True
        return False

    @is_verified.setter
    def is_verified(self, value: bool):
        self.last_verified_at = dt.datetime.now() if value else None

    def __str__(self):
        return self.mac


class AdvertisementUserLogin(db.Model, AsDictMixin):

    __tablename__ = 'advertisement_user_logins'

    _asdict_fields = 'id time user_id device_id'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.now(tz=pytz.timezone(inobi_config.APP_TIMEZONE)),
                     server_default=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('advertisement_users.id', ondelete="CASCADE"))
    user = db.relationship('AdvertisementUser', back_populates='logins')

    device_id = db.Column(db.Integer, db.ForeignKey('advertisement_user_devices.id', ondelete="SET NULL"))
    device = db.relationship(AdvertisementUserDevice, back_populates='logins')

    payload = db.Column(db.String, nullable=True, default=None, server_default=None)

    @property
    def _payload(self) -> T.Optional[dict]:
        if isinstance(self.payload, dict):
            return self.payload
        try:
            return json.loads(self.payload)
        except (TypeError, ValueError):
            pass

    @_payload.setter
    def _payload(self, v: dict):
        if v is not None:
            v = json.dumps(v)
        self.payload = v


User = AdvertisementUser
UserDevice = AdvertisementUserDevice
UserLogin = AdvertisementUserLogin

Chronicle.user_device = relationship(UserDevice,
                                     primaryjoin=foreign(Chronicle.client_mac) == UserDevice.mac,
                                     )

from inobi.transport.DataBase.models import Transports

Chronicle.transport = relationship(Transports, primaryjoin=foreign(Chronicle.box_mac) == Transports.device_id)
Transports.chronicles = relationship(Chronicle, primaryjoin=Transports.device_id == foreign(Chronicle.box_mac))


class AdvertisementGroup(db.Model, AsDictMixin, LocatedMixin, UpdateMixin):

    __tablename__ = 'advertisement_groups'

    _asdict_fields = 'id created updated name description location enabled parent_group_id devices groups city_id'.split()

    _update_fields = 'name description location enabled parent_group_id city_id'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    created = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    updated = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())

    name = db.Column(db.String, nullable=False)

    description = db.Column(db.String, nullable=True)

    enabled = db.Column(db.Boolean, nullable=False, default=True)

    parent_group_id = db.Column(db.Integer, db.ForeignKey('advertisement_groups.id', ondelete='CASCADE'), nullable=True)
    # parent_group = db.relationship('AdvertisementGroup', remote_side=[id, ])

    groups = db.relationship("AdvertisementGroup", backref=db.backref('parent_group', remote_side=[id]))

    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'),
                        server_default='1', nullable=False)

    city = relationship('City', backref=db.backref('advertisement_groups', remote_side=[city_id]))

    views = relationship('AdvertisementView', back_populates='ads_group')

    def __str__(self):
        return self.name

    @property
    def _devices(self):
        return [d.asdict() for d in self.devices]

    @property
    def _groups(self):
        return [g.asdict() for g in self.groups]


class AdvertisementDevice(db.Model, AsDictMixin, LocatedMixin, UpdateMixin):

    __tablename__ = 'advertisement_devices'

    _asdict_fields = 'id created updated device_id group_id name description location enabled city_id'.split()

    _update_fields = 'group_id device_id name description enabled location city_id'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    group_id = db.Column(db.Integer, db.ForeignKey('advertisement_groups.id', ondelete='CASCADE'), nullable=True)
    group = db.relationship(AdvertisementGroup, back_populates='devices')

    created = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    updated = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())

    device_id = db.Column(db.String, unique=True, nullable=False)

    name = db.Column(db.String, nullable=True)

    description = db.Column(db.String, nullable=True)

    enabled = db.Column(db.Boolean, nullable=False, default=True)

    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'),
                        server_default='1', nullable=False)

    city = relationship('City', backref=db.backref('advertisement_devices', remote_side=[city_id]))

    views = relationship('AdvertisementView', back_populates='ads_device')

    def __str__(self):
        return self.device_id


AdvertisementGroup.devices = db.relationship('AdvertisementDevice', back_populates='group')

Group = AdvertisementGroup
Device = AdvertisementDevice


Chronicle.ads_device_id = db.Column(db.Integer, db.ForeignKey(Device.id, ondelete='SET NULL'), nullable=True)
Chronicle.ads_group_id = db.Column(db.Integer, db.ForeignKey(Group.id, ondelete='SET NULL'), nullable=True)

Device.client_chronicles = relationship(Chronicle, back_populates='ads_device')
Group.client_chronicles = relationship(Chronicle, back_populates='ads_group')
Chronicle.ads_device = relationship(Device, back_populates='client_chronicles')
Chronicle.ads_group = relationship(Group, back_populates='client_chronicles')


class AdvertisementViewer(db.Model, AsDictMixin):

    __tablename__ = 'advertisement_viewers'

    _asdict_fields = 'id device_id device_description'.split()
    # _update_fields = 'device_id device_description'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    device_id = db.Column(db.String, unique=True, nullable=False)
    device_description = db.Column(db.String, nullable=True)

    views = db.relationship('AdvertisementView', back_populates='viewer', lazy='dynamic')


class AdvertisementView(db.Model, AsDictMixin):

    __tablename__ = 'advertisement_views'

    _asdict_fields = 'id ad_id _ad:ad key created time is_evaluated' \
                     ' _platform:platform provider_id viewer_id lat lng' \
                     ' is_redirected _events:events _viewer:viewer' \
                     ' ads_device_id ads_group_id'.split()
    # _update_fields = 'time platform provider_id viewer_id lat lng redirected events'.split()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    ad_id = db.Column(UUID(as_uuid=False), db.ForeignKey(Advertisement.id), nullable=False)
    ad = db.relationship(Advertisement, back_populates='ad_views')

    key = db.Column(UUID(as_uuid=False), nullable=False, unique=True, server_default=db.func.uuid_generate_v4())

    created = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    time = db.Column(db.DateTime, nullable=True)

    platform = db.Column(db.Integer, nullable=False, default=1023)  # flag field
    provider_id = db.Column(db.String, nullable=True)  # box_mac / app_bundle_id / etc

    viewer_id = db.Column(db.Integer, db.ForeignKey(AdvertisementViewer.id, ondelete='SET NULL'), nullable=True)
    viewer = db.relationship(AdvertisementViewer, back_populates='views')   # type: T.Optional[AdvertisementViewer]

    lat = db.Column(db.Float(precision=15), nullable=True)
    lng = db.Column(db.Float(precision=15), nullable=True)

    is_redirected = db.Column(db.Boolean, nullable=True)

    # json: array of objects, like [{type: SOURCE_FETCHED, time: 5.165}, {type: REDIRECT, time: 15.234}]
    events = db.Column(db.String, nullable=True)

    ads_device_id = db.Column(db.Integer, db.ForeignKey(Device.id, ondelete='SET NULL'), nullable=True)
    ads_device = relationship(Device, back_populates='views')

    ads_group_id = db.Column(db.Integer, db.ForeignKey(Group.id, ondelete='SET NULL'), nullable=True)
    ads_group = relationship(Group, back_populates='views')

    @property
    def is_possible(self) -> bool:
        """Return if view is shown with ad's duration taken into account"""
        assert self.time is not None
        return (self.time - self.created) > dt.timedelta(seconds=self.ad.duration)

    @property
    def is_evaluated(self) -> bool:
        return self.time is not None

    @property
    def _ad(self) -> dict:
        return self.ad.asdict()

    @property
    def _events(self):
        if self.events:
            return json.loads(self.events)

    @_events.setter
    def _events(self, value):
        self.events = json.dumps(value)

    @property
    def _viewer(self) -> dict:
        if self.viewer:
            return self.viewer.asdict()

    @_viewer.setter
    def _viewer(self, value: T.Optional[dict]):
        if value is None:
            self.viewer = None
            return
        if isinstance(value, dict) and 'device_id' in value:
            self.viewer = AdvertisementViewer(device_id=value['device_id'], device_description=value.get('device_description'))
        else:
            # todo: ???
            pass

    @property
    def _platform(self):
        return Ad.Platform.platform_fromint(self.platform)

    @_platform.setter
    def _platform(self, value):
        self.platform = Ad.Platform.platform_fromstr(value)


Viewer = AdvertisementViewer
View = AdvertisementView
