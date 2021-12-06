import time
import sqlite3
import geopy.distance as dist
import collections as C
import typing as T
import itertools as IT, functools as FT, operator
import os
import uuid


tag = "@{}:".format(__name__)


Point = C.namedtuple('Point', 'id lat lng dist')

DirectionLink = C.namedtuple('DirectionLink', 'dfrom dto')

_DirectionId = int

Platform = C.namedtuple('Platform', 'id lat lng')

_From = T.Union[_DirectionId, Point]


class Query:
    NEAREST_DIRECTIONS_WITHIN_RADIUS_V2 = '''
select did, dist from (
    select d.id as did, p.dist from (select *, distance(lat, lng, ?, ?) as dist from platforms) p
        inner join station_platforms sp
            on p.id = sp.entry_id
        inner join stations s
            on sp.id = s.id
        inner join station_routes sr
            on sr.id = s.id 
        inner join routes r
            on r.id = sr.entry_id
        inner join route_directions rd
            on rd.id = r.id
        inner join directions d
            on d.id = rd.entry_id
        
        where p.dist < (?)
        group by d.id
    )
'''

    NEAREST_DIRECTIONS_WITHIN_RADIUS = '''
select s.did, s.dist from (
    select dp.id as did, p.dist as dist from direction_platforms dp
        inner join (
            select *, distance(lat, lng, ?, ?) as dist from platforms
        ) p
            on p.id = dp.entry_id
        where dist < (?)
    ) s
    order by dist asc
'''

    NEAREST_DIRECTIONS_MINIMUM = '''
select s.did, s.dist from (
    select dp.id as did, p.dist as dist from direction_platforms dp
        inner join (
            select *, distance(lat, lng, ?, ?) as dist from platforms
        ) p
            on p.id = dp.entry_id
        order by dist asc
        limit ?
    ) s
'''

    DIRECTION_LINKS = '''
select dto, type from direction_links
    where dfrom = ?
    order by dto, type
'''

    DIRECTION_LINKS_FROM_PLATFORM_POSITION = '''
select dto, type from direction_links
    where dfrom = (?) and pfromi >= (?)
    order by dto, type
'''

    NEAREST_PLATFORM_TO_POINT_OF_DIRECTION = '''
select pl.id, pl.lat, pl.lng from (
    select p.*, p.dist as dist from directions d
        inner join direction_platforms dp
            on d.id = dp.id
        inner join (
            select *, distance(lat, lng, ?, ?) as dist from platforms
        ) p
            on dp.entry_id = p.id

        where d.id = (?)
        order by dist
        limit 1
    ) pl
'''

    NEAREST_ID_AND_POS_OF_DIRECTIONS_PLATFORMS = '''
select * from (
    select p.id, min(dp.pos) as pos from directions d
        inner join direction_platforms dp
            on d.id = dp.id
        inner join (
            select *, distance(lat, lng, ?, ?) as dist from platforms
        ) p
            on dp.entry_id = p.id

        where d.id = (?)
        group by round(p.dist * 5)
        order by p.dist
        limit 3
    )
'''
    LINK_PLATFORM_OF_FROM_AND_TO_DIRECTIONS = '''
select p.id, p.lat, p.lng from direction_links dl
    inner join platforms p
        on p.id = dl.pto
    where dl.dfrom = (?) and dl.dto = (?)
'''
    ID_AND_POS_OF_LINK_PLATFORM_OF_DIRECTIONS = '''
select dl.pto, dl.ptoi from direction_links dl
    where dl.dfrom = (?) and dl.dto = (?)
'''
    ID_AND_POS_OF_LINK_PLATFORM_OF_DIRECTIONS_FROM_LINK = '''
select dl.pfrom, dl.pfromi from direction_links dl
    where dl.dfrom = (?) and dl.dto = (?)
'''
    DIRECTION_PLATFORMS = '''
select p.id, p.lat, p.lng from directions d
    inner join direction_platforms dp
        on dp.id = d.id
    inner join platforms p
        on dp.entry_id = p.id

    where dp.id = (?)
    order by dp.pos
'''


@FT.lru_cache(None)
def distance(lat1, lng1, lat2, lng2):
    return dist.distance((lat1, lng1), (lat2, lng2)).kilometers


class Direction:
    def __init__(self, did: _DirectionId, conn: sqlite3.Connection):
        c = conn.cursor()
        self.platforms = platforms = list(c.execute('''
select p.*, s.name as sname from directions d
    inner join direction_platforms dp
        on d.id = dp.id
    inner join platforms p
        on p.id = dp.entry_id
    inner join station_platforms sp
        on sp.entry_id = p.id
    inner join stations s
        on sp.id = s.id
    where d.id = (?)
''', (did,)))
        *self.info, self.line = *info, line = list(c.execute('''
select r.name as rname, r.type as rtype, d.* from routes r
    inner join route_directions rd
        on rd.id = r.id
    inner join directions d
        on d.id = rd.entry_id
    where d.id = (?)
''', (did,)))[0]

    def __str__(self):
        return str(self.info + ", {} platforms".format(len(self.platforms)))


LinkPlatform = C.namedtuple('LinkPlatform', 'pid position')

class DirGraph:
    def __init__(self, conn: sqlite3.Connection, minimum_platforms=3):
        ts = time.time()
        conn.create_function(
            'distance',
            4,
            distance
        )
        print('distance func created in', time.time() - ts)
        self.conn = conn
        self.minimum_platforms = minimum_platforms

    def directions_of_point(self, ep: Point) -> T.List[_DirectionId]:
        c = self.conn.cursor()
        ts = time.time()
        dirs = list(map(lambda x: x[0],
                        c.execute(Query.NEAREST_DIRECTIONS_WITHIN_RADIUS_V2,
                                  (ep.lat, ep.lng, ep.dist))
                        ))
        print('directions within radius in', time.time() - ts, ep)
        ts = time.time()
        if len(dirs) == 0:
            dirs = list(map(lambda x: x[0],
                            c.execute(Query.NEAREST_DIRECTIONS_MINIMUM,
                                      (ep.lat, ep.lng, self.minimum_platforms))
                            ))
            print('directions with minimum in', time.time() - ts, ep)
        c.close()
        return dirs

    def directions_links(self, did: _DirectionId, prev: _From, exclude: T.Iterable) -> T.List[_DirectionId]:
        pl = self._platform_of(did, prev)
        return list(filter(lambda x: x not in exclude,
                           map(lambda x: x[0],
                               self.conn.cursor().execute(
                                   Query.DIRECTION_LINKS_FROM_PLATFORM_POSITION,
                                   (did, pl.position))
                               )
                           )
                    )

    def _platform_of(self, did: _DirectionId, from_: _From, pfrom: bool = False) -> LinkPlatform:
        if isinstance(from_, _DirectionId):

            sql = Query.ID_AND_POS_OF_LINK_PLATFORM_OF_DIRECTIONS_FROM_LINK if pfrom else Query.ID_AND_POS_OF_LINK_PLATFORM_OF_DIRECTIONS
            sql_args = (did, from_) if pfrom else (from_, did)

            out = list(self.conn.cursor().execute(
                sql,
                sql_args
            ))
            assert len(out) == 1, str([did, from_, out])
            return LinkPlatform._make(out[0])
        elif isinstance(from_, Point):
            out = list(self.conn.cursor().execute(
                Query.NEAREST_ID_AND_POS_OF_DIRECTIONS_PLATFORMS,
                (from_.lat, from_.lng, did)
            ))
            return LinkPlatform._make(out[0])
            pfirst_filtered = list(filter(lambda x: x[1] == 0, out))
            pmax = max(out, key=lambda x: x[1])
            if len(pfirst_filtered) == 0:
                return LinkPlatform._make(out[0])
            return LinkPlatform._make(pfirst_filtered[0])
        else:
            assert False, 'wtf!'

    def reachable(self, from_: _From, to: Point, by: _DirectionId) -> bool:
        to_platform = self._platform_of(by, to)
        from_platform = self._platform_of(by, from_)
        return from_platform.position <= to_platform.position


NamedPlatform = C.namedtuple('NamedPlatform', 'id lat lng name')


def pair_iter(iterable):
    prev = None
    for i, el in enumerate(iterable):
        if i == 0:
            prev = el
            continue
        yield prev, el
        prev = el


_T = T.TypeVar('_T')
def iter_with_adjacents(iterable: T.List[_T]) -> T.Iterator[T.Tuple[T.Optional[_T], _T, T.Optional[_T]]]:
    l = len(iterable)
    for i, el in enumerate(iterable):
        prev = iterable[i-1] if i != 0 else None
        next_ = iterable[i+1] if i < l-1 else None
        yield(prev, el, next_)


def make_path(path_list: T.Union[Point, _DirectionId], graph: DirGraph):

    start, *dids, destination = path_list
    start = start._asdict()
    destination = destination._asdict()
    path = dict(start=start, destination=destination)

    conn = graph.conn

    Route = C.namedtuple('Route', 'id type name from_name to_name')
    _Platform = C.namedtuple('_Platform', 'id lat lng name')

    def platforms_of(direction, from_, to):
        pfrom = graph._platform_of(direction, from_)
        pto = graph._platform_of(direction, to, True)
        c = conn.execute('''
            select p.id, p.lat, p.lng, s.name from platforms p
                inner join station_platforms sp
                    on p.id = sp.entry_id
                inner join stations s
                    on s.id = sp.id
                inner join direction_platforms dp
                    on dp.entry_id = p.id
                inner join directions d
                    on d.id = dp.id
                where d.id = (?)
                order by d.id, dp.pos''', (direction,))
        platforms = [_Platform._make(row)._asdict() for row in c]
        pfromi, ptoi = pfrom.position, pto.position
        if pfromi > ptoi:
            pfromi, ptoi = ptoi, pfromi
        return platforms[pfromi:ptoi+1]

    from ..a_star.utils import polyline_to_coords, coords_to_polyline, sliceline

    directions = []
    for i, (from_, cur, to) in zip(range(len(path_list)), IT.islice(iter_with_adjacents(path_list), 10)):
        if i == 0 or i == len(path_list)-1:
            continue

        c = conn.execute('''
            select d.id, d.line from directions d
            where d.id = (?)''', (cur,))
        (_, line) = list(c)[0]

        c = conn.execute('''
            select r.id, r.type, r.name, r.from_name, r.to_name from routes r
                inner join route_directions rd
                    on rd.id = r.id
                inner join directions d
                    on rd.entry_id = d.id
                where d.id = (?)''', (cur,))
        r = list(map(Route._make, c))[0]

        platforms = platforms_of(cur, from_, to)
        pfrom = (platforms[0]['lat'], platforms[0]['lng'])
        pto = (platforms[-1]['lat'], platforms[-1]['lng'])

        sliced = sliceline(polyline_to_coords(line), pfrom, pto, as_dict=False)

        d = {
            'id': cur,
            'route': r._asdict(),
            'line': coords_to_polyline(sliced),
            'platforms': platforms
        }
        directions.append(d)

    # directions = [
    #     {
    #         'id': id_,
    #         'route': r._asdict(),
    #         'line': coords_to_polyline(coords_from_dbrow(line)),
    #         'platforms': platforms_of(cur, from_, to)
    #     }
    #     for ((from_, cur, to), r, (id_, line)) in zip(IT.islice(triple_iter(path_list), 1, 10), routes, list(c))
    # ]

    path['directions'] = directions
    path['id'] = uuid.uuid4().hex
    path['cost'] = FT.reduce(lambda a, b: a+b, map(lambda x: len(x), map(lambda d: d['platforms'], directions)))

    fp = directions[0]['platforms'][0]
    lp = directions[-1]['platforms'][-1]

    path['cost'] += distance(start['lat'], start['lng'], fp['lat'], fp['lng']) * 10
    path['cost'] += distance(destination['lat'], destination['lng'], lp['lat'], lp['lng']) * 10

    return path


class Path:
    def __init__(self, path_list):
        self.start = path_list[0]
        self.destination = path_list[-1]
        self._directions = path_list[1:-1]


def search(start: Point, destination: Point, db_path: str, paths_count: int = 5):
    ts = time.time()

    if not os.path.isfile(db_path):
        raise Exception('Database not exists!')

    with sqlite3.connect(db_path) as conn:
        print('db connection inited in', time.time() - ts)
        print(start, '->', destination)

        graph = DirGraph(conn, minimum_platforms=5)

        goals = set(graph.directions_of_point(destination))    # type: T.Set[_DirectionId]

        start_directions = graph.directions_of_point(start)

        prevs = {  # type: T.Dict[_DirectionId, _From]
            direction: start
            for direction in start_directions
        }
        alt_prevs = C.defaultdict(set)

        def valid_directions(directions: T.Iterable[_DirectionId],
                             prevs=prevs,
                             goals=goals
                             ) -> T.List[_DirectionId]:

            ds = set(directions)
            intsect = ds.intersection(goals)
            if intsect:
                valids = list(filter(lambda dir: graph.reachable(from_=prevs[dir],
                                                                 to=destination,
                                                                 by=dir),
                                     intsect))
                return valids
            return []

        source = set(start_directions)
        valids = valid_directions(source)

        i = 0
        while not valids:

            print('\tsrc:   ', source)
            print('\tgoals: ', goals)
            print('\tvalids:', valids)

            if i > 4:
                print('too much shifts, exiting, no way here. Iteration', i)
                return []

            src = set()
            for did in source:
                dirs = graph.directions_links(did, prevs[did], prevs.keys())
                src.update(dirs)
                for d in dirs:
                    if d not in prevs:
                        prevs[d] = did
                    else:
                        alt_prevs[d].add(did)

            source = src
            valids = valid_directions(source)

            i += 1


        def restore_path(did, with_alternatives=True) -> T.List:
            out = []
            viewed = set()

            def lead_to_start(node, path, depth=0):
                while node is not start:
                    path.append(node)

                    if with_alternatives and depth-1 <= i and \
                        node not in viewed and alt_prevs[node]:

                        viewed.add(node)
                        for alt_prev_node in alt_prevs[node]:
                            if alt_prev_node in viewed:
                                continue
                            out.append(lead_to_start(alt_prev_node, list(path), depth=depth+1))

                    node = prevs[node]
                path.append(start)
                return list(reversed(path))

            path = [destination]
            node = did
            return out + [lead_to_start(node, path), ]

        print('valids:', valids)
        print('count:', len(valids))
        # print([(v, prevs[v]) for v in valids])
        # print(*[(v, alt_prevs[v]) for v in valids], sep='\n')

        # for v in valids:
        #     print(v, prevs[v])
        #     print(alt_prevs[v])

        valid_paths = list(IT.chain.from_iterable(map(restore_path, valids)))  # [restore_path(did) for did in valids]

        print(i, 'iterations')

        mapper = lambda x: make_path(x, graph)

        return sorted(map(mapper, valid_paths), key=lambda x: x['cost'])
