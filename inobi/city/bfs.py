
import enum
import time
import typing as T
import functools as FT
import itertools as IT
import collections as C
import geopy.distance as D

from . import config

import sqlite3


class GisObject:

    def __eq__(self, another):
        """eq kek"""
        return isinstance(another, GisObject) and another.id == self.id

    def __hash__(self):
        """hash lel"""
        return hash(self.id) ^ -7398564994278908910  # hash('GisObject')


class Platform(GisObject, C.namedtuple('Platform', 'id lat lng')):
    _distance_to_cache = {}

    @staticmethod
    def _clear_cache():
        Platform._distance_to_cache = {}

    # @FT.lru_cache(None)
    def distance_to(self, another: 'Platform') -> float:
        if self.id < another.id:
            key = (self.id, another.id)
        else:
            key = (another.id, self.id)

        value = Platform._distance_to_cache.get(key)

        if value is None:
            value = D.distance((self.lat, self.lng), (another.lat, another.lng)).kilometers
            Platform._distance_to_cache[key] = value

        return value

        # return D.distance((self.lat, self.lng), (another.lat, another.lng)).kilometers


class Direction(GisObject):
    class Link(C.namedtuple('Link', 'type from_direction to_direction pfrom pfromi pto ptoi')):

        class TransferType(enum.Enum):
            PLATFORM = 0
            STATION = 1
            WALK = 2

        MAX_TO_WALK = 0.5

        @staticmethod
        def best_link_key_func(link: 'Link'):
            return link.pfromi, link.type.value, -link.ptoi

        def __str__(self):
            return ('Link(type={type}, from={fromd}, '
                    'to={tod}, pfrom=(id: {pfrom}, i: {pfromi}), '
                    'pto=(id: {pto}, i: {ptoi}))'
                    ).format(
                type=self.type.name,
                fromd=self.from_direction.id,
                tod=self.to_direction.id,
                pfrom=self.pfrom.id,
                pto=self.pto.id,
                pfromi=self.pfromi,
                ptoi=self.ptoi
            )

    def __init__(self, id_, type_, platforms, pair):
        self.id = id_
        self.type = type_
        self.platforms = platforms
        self.pair = pair

    def __str__(self):
        return 'Direction(id={id}, type={type}, platforms_count={pc}, pair={pair})'.format(
            id=self.id,
            type=self.type,
            pc=len(self.platforms),
            pair=(self.pair.id if self.pair is not None else None)
        )

    def links_to(self, another: 'Direction'):
        links = []
        for fpi, fp in enumerate(self.platforms):
            for tpi, tp in enumerate(another.platforms):
                if fp is tp:
                    links.append(Direction.Link(
                        type=Direction.Link.TransferType.PLATFORM,
                        from_direction=self,
                        to_direction=another,
                        pfrom=fp, pfromi=fpi,
                        pto=tp, ptoi=tpi
                    ))
                elif fp.distance_to(tp) < Direction.Link.MAX_TO_WALK:
                    links.append(Direction.Link(
                        type=Direction.Link.TransferType.WALK,
                        from_direction=self,
                        to_direction=another,
                        pfrom=fp, pfromi=fpi,
                        pto=tp, ptoi=tpi
                    ))
        return links


def extract_bfs(db_path: str, routes_table=config.BFS_ROUTES_TABLE_NAME):
    with sqlite3.connect(db_path) as conn:
        _extract_bfs(conn, routes_table=routes_table)


def _extract_bfs(conn: sqlite3.Connection, routes_table='user_routes'):

    import builtins
    print = lambda *a, **kw: None

    c = cursor = conn.cursor().execute('select * from platforms')

    platforms = [Platform._make(row) for row in cursor]
    platforms = {
        p.id: p
        for p in platforms
    }

    print('platforms:', len(platforms))

    c.execute('''
select d.id, d.type, dp.* from {} r 
    inner join route_directions rd 
        on rd.id = r.id
    inner join directions d 
        on rd.entry_id = d.id
    inner join direction_platforms dp 
        on dp.id = d.id 

    order by d.id, dp.pos
'''.format(routes_table))

    directions = {}
    for did, dir_platforms in IT.groupby(c, lambda row: row[0]):
        fp, *_ = dir_platforms = list(dir_platforms)

        dir_platforms = list(dir_platforms)
        print(dir_platforms)

        d = Direction(
            did,
            fp[1],
            platforms=list(map(lambda x: x[1], sorted(map(lambda ds: (ds[-2], platforms[ds[-1]]), dir_platforms)))),
            pair=None
        )
        directions[d.id] = d

    print('directions:', len(directions))

    for rid, ds in IT.groupby(
            c.execute('select rd.* from {} r inner join route_directions rd on r.id = rd.id'.format(routes_table)),
            lambda row: row[0]):
        ds = list(ds)
        assert len(ds) < 3, "Wtf! {}".format(ds)

        if len(ds) == 2:
            # first direction index, second direction index
            fdi, sdi = map(lambda rpd: rpd[-1], ds)
            directions[fdi].pair = directions[sdi]
            directions[sdi].pair = directions[fdi]
        else:
            # print('single direction:', ds, directions[ds[0][-1]])
            pass

    direction_links = dl = C.defaultdict(list)

    dirs = list(directions.values())
    for i, d in enumerate(dirs):
        ts = time.time()

        dlinks = []
        for another_d in dirs:
            if d.pair is another_d or d is another_d:
                continue

            links = d.links_to(another_d)
            # print(*links, sep='\n')

            if links:
                dlinks.append(min(links, key=Direction.Link.best_link_key_func))

        dl[d].extend(dlinks)

        print()
        print('iteration: {} (of {} total), took: {:.3f} seconds'.format(i, len(dirs), time.time() - ts))
        print('links found:', len(dlinks))
        print('direction:', d)
        print('platforms.distance_to.cache:', len(Platform._distance_to_cache))

    print()
    print('Total links:', FT.reduce(lambda a, b: a + b, map(len, dl.values())))

    c.executescript('''
drop table if exists direction_links;
CREATE TABLE direction_links (
    dfrom int, 
    dto int, 
    type int, 
    pfrom int, 
    pfromi int, 
    pto int, 
    ptoi int, 
    primary key(dfrom, dto, type)
);''')

    def map_link_to_insert_row(link: Direction.Link) -> T.Tuple[int, int, int, int, int, int, int]:
        return link.from_direction.id, link.to_direction.id, \
               link.type.value, link.pfrom.id, link.pfromi, \
               link.pto.id, link.ptoi

    c.executemany('insert into direction_links values(?, ?, ?, ?, ?, ?, ?)',
                  map(map_link_to_insert_row, IT.chain.from_iterable(dl.values())))

    c.executescript('vacuum;')

    Platform._clear_cache()

