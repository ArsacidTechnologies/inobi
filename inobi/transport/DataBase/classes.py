
import collections as C
import typing as T
import json
import polyline

from inobi.utils import polyline_to_linestring
from flask import url_for


class Transport(C.namedtuple('Transport', 'id device_id line_id device_phone name independent payload driver device_type ip port tts')):

    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['Transport']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t._replace(payload=json.loads(t.payload) if t.payload is not None else None)

    @property
    def asdbrow(self):
        return self._replace(payload=json.dumps(self.payload, ensure_ascii=False))

    def asdict(self):
        d = super(Transport, self)._asdict()
        payload = d.get('payload')
        if payload:
            if payload.get('picture'):
                payload['picture'] = url_for('Transport Organization.download_picture', filename=payload['picture'], _external=True)
        return d


class TransportOrganization(C.namedtuple('TransportOrganization', 'id name traccar_username traccar_password payload city settings')):

    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['TransportOrganization']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        to = cls._make(row)
        return to._replace(
            payload=json.loads(to.payload) if to.payload is not None else None
        )

    @property
    def asdbrow(self):
        return self._replace(
            payload=json.dumps(self.payload, ensure_ascii=False),
            settings=json.dumps(self.settings, ensure_ascii=False) if self.settings is not None else None
        )

    def _asdict(self):
        d = super(TransportOrganization, self)._asdict()
        del d['traccar_password']
        return d


class Route(C.namedtuple('Route', 'id, type, name, from_name, to_name')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['Route']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(Route, self)._asdict()
        return d


class Direction(C.namedtuple('Direction', 'id, type, line')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0, convert=False) -> T.Optional['Direction']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        if convert:
            return t._replace(line=polyline_to_linestring(t.line))
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(Route, self)._asdict()
        return d

    @staticmethod
    def polyline_to_linestring(raw: str):
        converted = polyline.decode(raw)
        linestring = ','.join('{} {}'.format(lat, lng) for lat, lng in converted)
        linestring = 'LINESTRING ({})'.format(linestring)
        return linestring


class Platform(C.namedtuple('Platform', 'id, lat, lng')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0, convert=False) -> T.Optional['Platform']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(Platform, self)._asdict()
        return d


class Stations(C.namedtuple('Stations', 'id, name, full_name')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['Stations']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(Stations, self)._asdict()
        return d


class TransportDriverChanges(C.namedtuple('TransportDriverChanges', 'transport, time, type, prev, next, reason, issuer')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['TransportDriverChanges']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(TransportDriverChanges, self)._asdict()
        return d

class BusInfo(C.namedtuple('BusInfo', 'id, device_id, lat, lng, status, time, total_time_on')):
    @classmethod
    def make_from_db_row(cls, row: T.Iterable, start_index=0) -> T.Optional['BusInfo']:
        row = row[start_index:start_index + len(cls._fields)]
        if row.count(None) == len(cls._fields):
            return None
        t = cls._make(row)
        return t

    @property
    def asdbrow(self):
        return self

    def asdict(self):
        d = super(BusInfo, self)._asdict()
        return d


