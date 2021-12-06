
import typing as T

import time
import json

from datetime import datetime
from collections import namedtuple

from uuid import UUID
from ..utils import purge_uuid, is_valid_uuid, media_exists, prepare_source
from ..utils.stats import parse_device_from_ua

from ..exceptions import InobiException

from ..config import AD_MIN_RADIUS_PARAMETER, AD_MAX_RADIUS_PARAMETER, AD_DEFAULT_RADIUS_PARAMETER

import builtins

from flask import url_for
from .. import config


tag = "@{}:".format(__name__)


class OldSelectFieldsMixin:

    _select_fields = ()

    @classmethod
    def select_fields(cls, label: str = None) -> str:
        if label:
            _l = label + '.'
        else:
            _l = ''

        fs = cls._select_fields
        if isinstance(fs, str):
            fs = fs.split()

        return ', '.join(map(lambda i: _l + i, fs))


class Chronicle(namedtuple('Chronicle', 'client_mac time device box_mac ad_id lat lng redirected events id'),
                OldSelectFieldsMixin):

    _select_fields = 'client_mac time device box_mac ad_id lat lng redirected events id'

    @classmethod
    def construct(cls, box_mac: str, ad_id: str, lat: float, lng: float, redirected: bool, events: list, client_mac: str = None, user_agent: str = None) -> T.Optional['Chronicle']:

        if not is_valid_uuid(ad_id):
            return None

        return cls(
            client_mac=client_mac,
            time=time.time(),
            device=parse_device_from_ua(user_agent),
            box_mac=box_mac,
            ad_id=ad_id,
            lat=lat,
            lng=lng,
            redirected=redirected,
            events=events,
            id=None,
        )

    @classmethod
    def make_from_query(cls, row) -> 'Chronicle':
        chronicle = cls._make(row)
        return chronicle._replace(events=json.loads(chronicle.events))

    @property
    def as_db_row(self) -> 'Chronicle':
        # return (self.client_mac, self.time, self.device, self.box_mac, self.ad_id, self.lat, self.lng, self.redirected, json.dumps(self.events))
        return self._replace(events=json.dumps(self.events))[:-1]


class AdView(namedtuple('AdView', 'client_mac time user_agent box_mac ad_id lat lng'),
             OldSelectFieldsMixin):

    _select_fields = 'client_mac time user_agent box_mac ad_id lat lng'

    @classmethod
    def construct(cls, box_mac: str, ad_id: str, lat: float, lng: float, client_mac: str = None, user_agent: str = None) -> T.Optional['AdView']:

        if not is_valid_uuid(ad_id):
            return None

        return cls(
            client_mac=client_mac,
            time=time.time(),
            user_agent=user_agent,
            box_mac=box_mac,
            ad_id=ad_id,
            lat=lat,
            lng=lng
        )

    def device(self):
        ua = self.user_agent
        if '(' in ua and ')' in ua:
            return ua[ua.index('(')+1:ua.index(')')]
        return 'unknown'

    def datetime(self):
        return datetime.fromtimestamp(self.time)


class _noupdate:  # Marker object to show that ad property should not be updated
    pass


class Ad(namedtuple(
    'Ad',
    'id type duration redirect_url weight views source '
    'created enabled title description lat lng views_max '
    'expiration_date requests platform radius transport_filters '
    'cities time_from time_to start_date'),
    OldSelectFieldsMixin
         ):

    _select_fields = (
        'id type duration redirect_url weight views source '
        'created enabled title description lat lng views_max '
        'expiration_date requests platform radius transport_filters '
        'cities time_from time_to start_date'
    )

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
            if (i & Ad.Platform.ALL) == Ad.Platform.ALL:
                return 'all'
            return '|'.join(k for k, v in Ad.Platform._STR_PLATFORMS.items() if v & i and k not in Ad.Platform._EXCLUDE_FROM_STR)

    class Radius:
        MIN = AD_MIN_RADIUS_PARAMETER
        MAX = AD_MAX_RADIUS_PARAMETER
        DEFAULT = AD_DEFAULT_RADIUS_PARAMETER

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

    @staticmethod
    def time_modifier(x):
        try:
            time = datetime.strptime(x, '%H:%M:%S').time()
        except ValueError:
            raise InobiException("Time must be in '%H:%M:%S' format")
        return time

    noupdate = _noupdate

    TYPES = frozenset({'banner', 'video', 'iframe'})

    @classmethod
    def create(cls, type: str, duration: float, redirect_url: str, source: str,
                    title: str, external_source: bool = False, description: str = None, lat: float = None, lng: float = None,
                    views_max: int = None, expiration_date: float = None,
                    enabled: bool = True, weight: int = 1, platform: int = Platform.ALL,
                    radius: float = Radius.DEFAULT, transport_filters: list = None,
                    cities: list = None, time_from: datetime.time = None, time_to: datetime.time = None,
                    start_date: float = None
               ) -> 'Ad':

        geo_count = [lat, lng].count(None)
        if geo_count == 2:
            pass
        elif geo_count != 0:
            raise InobiException("'lat' And 'lng' Parameters Must Come Alongside Each Other")

        Ad.Radius.check_radius(radius)

        if type not in Ad.TYPES:
            raise InobiException("'type' Parameter must be one of {}".format(set(Ad.TYPES)))

        if not (0 < weight < 11):
            raise InobiException('Weight Parameter Must Be Integer Type And Be In Range [1:10]')

        if external_source:
            source = '!' + source
        else:
            if not media_exists(source, in_temp=True):
                raise InobiException('Source file does not exist in Uploads')

        if transport_filters is not None:
            if not transport_filters:
                raise InobiException("'transport_filters' Parameter Should Not Be Empty")
            if set(builtins.type(i) for i in transport_filters).difference({str, int}):
                raise InobiException("'transport_filters' Parameter Must Be An Array of String Or Integer Values")

            transport_filters = list(map(str, transport_filters))

        ad = cls(
            id=None,
            type=type,
            duration=duration,
            redirect_url=redirect_url,
            weight=weight,
            views=0,
            source=source,
            created=time.time(),
            enabled=enabled,
            title=title,
            description=description,
            lat=lat,
            lng=lng,
            views_max=views_max,
            expiration_date=expiration_date,
            requests=0,
            platform=platform,
            radius=radius,
            transport_filters=transport_filters,
            cities=cities,
            time_from=time_from,
            time_to=time_to,
            start_date=start_date
        )

        return ad

    def prepare_source(self):
        if not (self.source.startswith('!') or prepare_source(self.source)):
            raise Exception(tag, 'Could not prepare source: "{}"'.format(self.source))

    @classmethod
    def update(cls, id: str, type: str = _noupdate, duration: float = _noupdate,
                    redirect_url: str = _noupdate, source: str = _noupdate,
                    title: str = _noupdate, description: str = _noupdate,
                    enabled: bool = _noupdate, weight: int = _noupdate,
                    lat: float = _noupdate, lng: float = _noupdate,
                    views_max: int = _noupdate, expiration_date: float = _noupdate,
                    external_source: bool = _noupdate, platform: int = _noupdate
               ):

        if type not in Ad.TYPES:
            raise InobiException("'type' Parameter must be one of {}".format(set(Ad.TYPES)))

        if not (0 < weight < 11):
            raise InobiException('Weight Parameter Must Be Integer Type And Be In Range [1:10]')

        if external_source:
            source = '!' + source
        else:
            if not media_exists(source, in_temp=True):
                raise InobiException('Source file does not exist in Uploads')

        raise NotImplementedError('kek')

    def _asdict(self):
        d = super(Ad, self)._asdict()

        d['external_source'] = self.external_source
        d['source'] = self._source
        d['source_full'] = self.source_full

        d['platform'] = Ad.Platform.platform_fromint(self.platform)
        if self.time_to:
            d['time_to'] = d['time_to'].strftime('%H:%M:%S')
        if self.time_from:
            d['time_from'] = d['time_from'].strftime('%H:%M:%S')

        return d

    @property
    def external_source(self) -> bool:
        return self.source.startswith('!')

    @staticmethod
    def parse_id(raw_id):
        try:
            return str(UUID(bytes_le=bytes(raw_id)))
        except:
            return purge_uuid(raw_id)

    def getid(self):
        return Ad.parse_id(self.id)

    @property
    def _source(self):
        return self.source if not self.external_source else self.source[1:]

    @property
    def source_full(self) -> str:
        if self.external_source:
            return self.source[1:]
        else:
            return url_for(config.NAME + '.media', filename=self.source, _external=True)


import json


class AppAdView(namedtuple('AppAdView', 'ad_id user device_id lat lng time platform result payload'),
                OldSelectFieldsMixin):

    _select_fields = 'ad_id user device_id lat lng time platform result payload'

    class Platform(namedtuple('Platform', 'bundle_id os version build')):
        @classmethod
        def modifier(cls, arg):
            return cls(**{k: v for k, v in arg.items() if k in cls._fields})

        @property
        def json(self):
            return json.dumps(self._asdict())

    @staticmethod
    def make_from_query(row) -> 'AppAdView':
        view = AppAdView._make(row)
        return view._replace(
            platform=AppAdView.Platform(**json.loads(view.platform)),
            payload=json.loads(view.payload)
        )

    def asdict(self):
        return self._replace(platform=self.platform._asdict())._asdict()

    @property
    def as_db_row(self) -> 'AppAdView':
        return self._replace(
            platform=self.platform.json,
            payload=json.dumps(self.payload)
        )
