from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes
from inobi import db
from inobi.transport.DataBase.models import Routes, RouteDirections, Directions, ExcludeRoutes
from ..models import TransportOrganizations


def get(id, organization):
    s = Routes.query.filter(Routes.id == id).first()
    if not s:
        raise BaseInobiException('not found', error_codes.ROUTE_NOT_FOUND, 404)
    return s.as_dict(full=True)


def create(organization, type, name, from_name=None, to_name=None, directions=None, excluded=False):
    obj = Routes(type=type, name=name, from_name=from_name, to_name=to_name)
    ds = []
    if directions:
        for d in directions:
            db_d = Directions(line=d['line'], type=d['type'])
            ds.append(db_d)
            organization.directions.append(db_d)
    organization.routes.append(obj)
    obj.directions = ds
    db.session.add(obj)
    db.session.commit()

    if excluded:
        excluded_obj = ExcludeRoutes(route_id=obj.id)
        db.session.add(excluded_obj)
        db.session.commit()
    return obj.as_dict(full=True)


def update(id, organization: TransportOrganizations, name, type, from_name=None, to_name=None):
    obj = Routes.query.filter(Routes.id == id).first()
    if not obj:
        raise BaseInobiException('not found', error_codes.ROUTE_NOT_FOUND, 404)
    obj.name = name
    obj.type = type
    obj.from_name = from_name
    obj.to_name = to_name
    db.session.add(obj)
    db.session.commit()
    return obj.as_dict(full=True)


def delete(id, organization: TransportOrganizations):
    obj = Routes.query.filter(Routes.id == id).first()
    if not obj:
        raise BaseInobiException('not found', error_codes.ROUTE_NOT_FOUND, 404)
    transports = obj.transports.all()
    if transports:
        raise BaseInobiException('linked transports {}'.format(', '.join([str(t.id) for t in transports])),
                                 error_codes.UNLINK_TRANSPORT_FIRST, 400)
    db.session.delete(obj)
    db.session.commit()
    return obj.as_dict(full=True)


def list_(organization: TransportOrganizations):
    obj = [s.as_dict() for s in organization.routes]
    return obj


def link_directions(organization: TransportOrganizations, route_id: int, direction_ids: list):
    route = Routes.query.filter(Routes.id == route_id).first()
    if not route:
        raise BaseInobiException('not found', error_codes.ROUTE_NOT_FOUND, 404)
    directions = Directions.query.filter(Directions.id.in_(direction_ids)).all()
    direction_ids_set = set(direction_ids)
    db_direction_ids_set = set([d.id for d in directions])

    unknowns = direction_ids_set.difference(db_direction_ids_set)
    if unknowns:
        raise BaseInobiException('directions not found {}'.format(unknowns), error_codes.DIRECTION_NOT_FOUND, 404)

    route.directions = directions
    db.session.add(route)
    db.session.commit()
    return route.as_dict(full=True)
