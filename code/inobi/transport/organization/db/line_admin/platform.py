from inobi.utils import connected
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes
from inobi import db
from inobi.transport.DataBase.models import Platforms, Stations
from ..models import TransportOrganizations
# from .models import TransportOrganizationPlatforms as TOP


def get(id, organization):
    p = Platforms.query.filter(Platforms.id == id).first()
    if not p:
        raise BaseInobiException('not found', error_codes.PLATFORM_NOT_FOUND, 404)
    return p.as_dict(full=True)


def create(lat, lng, organization, station_id):
    platform = Platforms(lat=lat, lng=lng)
    station = Stations.query.filter(Stations.id == station_id).first()
    if not station:
        raise BaseInobiException('not found', error_codes.STATION_NOT_FOUND, 404)
    # organization.platforms.append(platform)
    station.platforms.append(platform)
    db.session.add(platform)
    # db.session.add(organization)
    db.session.add(station)
    db.session.commit()
    return platform.as_dict(full=True)


def update(id, lat, lng, organization: TransportOrganizations):
    platform = Platforms.query.filter(Platforms.id == id).first()
    if not platform:
        raise BaseInobiException('not found', error_codes.PLATFORM_NOT_FOUND, 404)
    platform.lat = lat
    platform.lng = lng
    db.session.add(platform)
    db.session.commit()
    return platform.as_dict(full=True)


def delete(id, organization: TransportOrganizations):
    platform = Platforms.query.filter(Platforms.id == id).first()
    if not platform:
        raise BaseInobiException('not found', error_codes.PLATFORM_NOT_FOUND, 404)
    db.session.delete(platform)
    db.session.commit()
    return platform.as_dict(directions=True, stations=True)


import typing as T

Degree = T.Union[int, float]
Coords = T.Tuple[Degree, Degree]
Bounds = T.Dict[str, Coords]


def list_(organization: int, free=False, bounds: T.Optional[Bounds] = None):
    if not free:
        query = db.session.query(Platforms, Stations)\
             .outerjoin(Platforms.stations)\
             .order_by(Platforms.id)
        if bounds:
            lower_lat, upper_lat = sorted(bounds['lat'])
            lower_lng, upper_lng = sorted(bounds['lng'])
            query = query.filter(Platforms.lat >= lower_lat, Platforms.lat <= upper_lat)\
                .filter(Platforms.lng >= lower_lng, Platforms.lng <= upper_lng)

        platforms = [p.as_dict(stations=s) for p, s in query.all()]
    else:
        platforms = [p.as_dict(stations=None) for p in db.session.query(Platforms)
                         .filter(Platforms.stations == None)
                         .order_by(Platforms.id)
                         .all()]
    return platforms

