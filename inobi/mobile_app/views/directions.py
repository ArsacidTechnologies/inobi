from collections import namedtuple, OrderedDict
from flask import abort, request, url_for, send_from_directory

from inobi.security import secured
from inobi.utils import getargs, http_ok, http_err

from .. import route

from ..directions.a_star.utils import sliceline, coords_from_linestring, sortedsetarray
from ..directions.a_star import bidirectional_a_star_search
from ..directions.a_star.graph import GisGraph, Costs, Node, SQLQuery


class Type:
    NUMERIC = (int, float)


class Blueprint:

    POINT = {
        k: Type.NUMERIC
        for k in ('dist', 'lat', 'lng')
    }

    COSTS = {
        k: Type.NUMERIC
        for k in ('walk', 'transfer', 'transfer_same', 'shift')
    }


def checkobject(o, blueprint):
    if not isinstance(o, dict):
        return False
    for key, types in blueprint.items():
        if key not in o or not isinstance(o[key], types):
            return False
    return True


DetailedDirection = namedtuple('DetailedDirection', 'id route_id type line route_type name from_name to_name')
DetailedPlatform = namedtuple('DetailedPlatform', 'id sid lat lng name full_name')

# from gis.utils import coords_from_dbrow
# class DetailedDirection(DetailedDirection):
#     def __new__(cls, *args, **kwargs):
#         line = kwargs.pop('line', None) or args[4]
#         return super(cls, DetailedDirection).__new__(cls, *args[:4], coords_from_dbrow(line), *args[5:], **kwargs)

Step = namedtuple('Step', 'type payload message')


def recoversteps(result):
    # Node: id type additional lat lng nid

    dids = tuple(n.did for n in result if n.type != 'point')

    pds = OrderedDict()
    for did in dids:
        pds[did] = tuple(n for n in result if n.did == did)

    steps = []

    def payload(from_node, to_node):
        return {
            'from': dict(
                lat=from_node.lat,
                lng=from_node.lng,
                direction_id=from_node.did,
                id=from_node.id,
            ),
            'to': dict(
                lat=to_node.lat,
                lng=to_node.lng,
                direction_id=to_node.did,
                id=to_node.id,
            )
        }

    start = result[0]
    goal = result[-1]
    prev = None
    for i, (did, ps) in enumerate(pds.items()):
        if prev is not None:
            p = ps[0]
            _payload = payload(prev, p)
            if prev.id == p.id:
                steps.append(Step('transfer_same', _payload, 'Transfer from route #{} to #{}'.format(prev.did, p.did)))
            elif prev.sid == p.sid:
                steps.append(Step('transfer', _payload, 'Transfer from route #{} to #{} ON ANOTHER platform of SAME station'.format(prev.did, p.did)))
            else:
                steps.append(Step('transfer_walk', _payload, 'Walk to another platform'))

        if i == 0:
            _payload = payload(start, ps[0])
            steps.append(Step('walk', _payload, 'Walk to platform and sit on route #{}'.format(ps[0].did)))

        steps.append(Step('shift', payload(ps[0], ps[-1]), 'Shift on route #{} (from pid #{} to #{})'.format(ps[0].did, ps[0].id, ps[-1].id)))
        prev = ps[-1]

    steps.append(Step('walk', payload(prev, goal), 'Walk to destination'))

    return steps


def dirlineslices(result, directions):
    dids = [n.did for n in result if n.did is not None]
    pds = OrderedDict()
    for did in dids:
        pds[did] = tuple(n for n in result if n.did == did)
    for (did, ns) in pds.items():
        pds[did] = sliceline(coords_from_linestring(directions))


def restorepath(result, dbconnection):

    dids = sortedsetarray(n.did for n in result if n.did is not None)
    pids = sortedsetarray(n.id for n in result if n.id is not None)

    cursor = dbconnection.cursor()

    cursor = cursor.execute(*SQLQuery.detaileddirections(dids))
    directions = [DetailedDirection(*row) for row in cursor]

    print(len(directions))

    cursor = cursor.execute(*SQLQuery.detailedplatforms(pids))
    platforms = [DetailedPlatform(*row) for row in cursor]

    print(len(platforms))

    steps = recoversteps(result)

    dids = [n.did for n in result if n.did is not None]
    ls = line_slices = OrderedDict()
    for did in dids:
        direction = [d for d in directions if d.id == did][0]
        ps = tuple(n for n in result if n.did == did)
        s, d = ps[0], ps[-1]
        ls[did] = sliceline(
            coords_from_linestring(direction.line),
            (s.lat, s.lng),
            (d.lat, d.lng),
            as_dict=True
        )

    return {
        'directions': [d._asdict() for d in directions],
        'platforms': [p._asdict() for p in platforms],
        'direction_line_slices': line_slices,
        'steps': [s._asdict() for s in steps]
    }


@route('/v0/directions')
@secured('application_admin')
def api_directions_v1():
    start, destination, costs, aspire, leaf_checks, amplifier = getargs(
        request,
        'start',
        'destination',
        'costs',
        'aspire',
        'leaf_checks',
        'heuristic_amplifier'
    )
    aspire = aspire if isinstance(aspire, bool) else False
    leaf_checks = leaf_checks if isinstance(leaf_checks, int) else 3
    amplifier = amplifier if isinstance(amplifier, Type.NUMERIC) else 1
    try:
        costs = Costs._make(costs)
    except:
        # return HTTP_ERR('Costs Object Is Not OK', 400, dict(costs=costs))
        costs = GisGraph.COSTS

    if None in (start, destination):
        return http_err('Start And Destination Points Must Present', 400)

    for point in (start, destination):
        if not checkobject(point, Blueprint.POINT):
            return http_err('Point Is Not OK', 400, dict(point=point))

    sp = Node.point(
        id='start',
        dist=start['dist'],
        lat=start['lat'],
        lng=start['lng']
    )
    dp = Node.point(
        id='destination',
        dist=destination['dist'],
        lat=destination['lat'],
        lng=destination['lng']
    )

    from ..config import RESOURCES_APP
    from os.path import join
    import sqlite3
    dbpath = join(RESOURCES_APP, 'directions.db')
    with sqlite3.connect(dbpath) as conn:
        graph = GisGraph(
            dbconnection=conn,
            start=sp,
            destination=dp,
            costs=costs
        )

        result = bidirectional_a_star_search(
            graph=graph,
            start=sp,
            goal=dp,
            aspire=True,  # aspire
            leaf_checks=leaf_checks,
            heuristic_amplifier=2,  # amplifier
        )

        bundle = restorepath(result, conn)

    return http_ok(dict(path=bundle))


import typing as T
from inobi.utils.converter import converted
from ..directions.bfs import Point, search
from ..config import DIRECTIONS_BFS_DB_PATH

from flask_cors import cross_origin


def make_point(type: str) -> T.Callable[[T.Dict], Point]:
    return lambda data: Point(id=type, **data)


@route('/v1/directions')
@cross_origin()
@secured()
@converted
def api_directions_v2(start: make_point('start'), destination: make_point('destination')):

    sr = search(start, destination, db_path=DIRECTIONS_BFS_DB_PATH)

    return http_ok(results=sr, count=len(sr))


