from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes
from inobi import db
from inobi.transport.DataBase.models import Directions, DirectionPlatforms, Platforms, Routes
from ..models import TransportOrganizations


def get(id, organization):
    s = Directions.query.filter(Directions.id == id).first()
    if not s:
        raise BaseInobiException('not found', error_codes.DIRECTION_NOT_FOUND, 404)
    return s.as_dict(True)


def create(organization, type, line, route_id):
    obj = Directions(type=type, line=line)
    route = Routes.query.filter(Routes.id == route_id).first()
    if not route:
        raise BaseInobiException('route not found', error_codes.ROUTE_NOT_FOUND, 404)
    route.directions.append(obj)
    # organization.directions.append(obj)
    db.session.add(obj)
    # db.session.add(organization)
    db.session.add(route)
    db.session.commit()
    return obj.as_dict(full=True)


def update(id, organization: TransportOrganizations, type, line):
    obj = Directions.query.filter(Directions.id == id).first()
    if not obj:
        raise BaseInobiException('not found', error_codes.DIRECTION_NOT_FOUND, 404)
    obj.line = line
    obj.type = type
    db.session.add(obj)
    db.session.commit()
    return obj.as_dict(full=True)


def delete(id, organization: TransportOrganizations):
    obj = Directions.query.filter(Directions.id == id).first()
    if not obj:
        raise BaseInobiException('not found', error_codes.DIRECTION_NOT_FOUND, 404)
    db.session.delete(obj)
    db.session.commit()
    return obj.as_dict(full=True)


def list_(organization: TransportOrganizations, free=False):
    if not free:
        directions = [d.as_dict(routes=r) for d, r in db.session.query(Directions, Routes)
                         .outerjoin(Directions.routes)
                         .order_by(Directions.id)
                         .all()
        ]
    else:
        directions = [
            d.as_dict(routes=None) for d in db.session.query(Directions)
             .join(TransportOrganizations.directions)
             .order_by(Directions.id)
             .all()
            ]
    return directions


def link_platforms(organization: TransportOrganizations, direction_id: int, platform_ids: list):
    direction = Directions.query.filter(Directions.id == direction_id).first()
    if not direction:
        raise BaseInobiException('not found', error_codes.DIRECTION_NOT_FOUND, 404)
    platforms = Platforms.query.filter(Platforms.id.in_(platform_ids)).all()
    platform_ids_set = set(platform_ids)
    db_platform_ids_set = set([p.id for p in platforms])

    unknowns = platform_ids_set.difference(db_platform_ids_set)
    if unknowns:
        raise BaseInobiException('platforms not found {}'.format(unknowns), error_codes.PLATFORM_NOT_FOUND, 404)

    direction.platforms = []
    db.session.add(direction)
    db.session.commit()
    a = set()
    for i, platform_id in enumerate(platform_ids):
        if platform_id in a:
            continue
        a.add(platform_id)
        dp = DirectionPlatforms(id=direction.id, pos=i, entry_id=platform_id)
        db.session.add(dp)
    db.session.commit()

    return direction.as_dict(full=True)


