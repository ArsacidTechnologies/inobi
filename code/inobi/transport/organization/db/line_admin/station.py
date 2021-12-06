from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes
from inobi import db
from inobi.transport.DataBase.models import Stations, StationPlatforms, Platforms
from ..models import TransportOrganizations


def get(id, organization):
    s = Stations.query.filter(Stations.id == id).first()
    if not s:
        raise BaseInobiException('not found', error_codes.STATION_NOT_FOUND, 404)
    return s.as_dict(full=True)


def create(organization, name, full_name=None, platforms=None):
    station = Stations(name=name, full_name=full_name)
    db.session.add(station)
    if platforms:
        for i, p in enumerate(platforms):
            platform = Platforms(**p)
            # organization.platforms.append(platform)
            db.session.add(platform)
            db.session.commit()
            dp = StationPlatforms(id=station.id, pos=i, entry_id=platform.id)
            db.session.add(dp)

    # db.session.add(organization)
    db.session.commit()
    return station.as_dict(platforms=True)


def update(id, organization: TransportOrganizations, name, full_name=None):
    station = Stations.query.filter(Stations.id == id).first()
    if not station:
        raise BaseInobiException('not found', error_codes.STATION_NOT_FOUND, 404)
    station.name = name
    station.full_name = full_name
    db.session.add(station)
    db.session.commit()
    return station.as_dict(full=True)


def delete(id, organization: TransportOrganizations):
    station = Stations.query.filter(Stations.id == id).first()
    if not station:
        raise BaseInobiException('not found', error_codes.STATION_NOT_FOUND, 404)
    db.session.delete(station)
    db.session.commit()
    return station.as_dict(full=True)


def list_(organization: TransportOrganizations):
    stations = [s.as_dict(platforms=True, platforms_directions=False) for s in Stations.query.all()]
    return stations


def link_platforms(organization: TransportOrganizations, station_id: int, platform_ids: list):
    station = Stations.query.filter(Stations.id == station_id).first()
    if not station:
        raise BaseInobiException('not found', error_codes.STATION_NOT_FOUND, 404)
    platforms = Platforms.query.filter(Platforms.id.in_(platform_ids)).all()
    platform_ids_set = set(platform_ids)
    db_platform_ids_set = set([p.id for p in platforms])
    unknowns = platform_ids_set.difference(db_platform_ids_set)
    if unknowns:
        raise BaseInobiException('platforms not found {}'.format(unknowns), error_codes.PLATFORM_NOT_FOUND, 404)

    station.platforms = platforms
    db.session.add(station)
    db.session.commit()

    return station.as_dict(full=True)


