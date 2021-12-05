from time import time as now
from collections import namedtuple, OrderedDict
from itertools import chain

from geopy.distance import distance

from .query import SQLQuery
from .utils import coords_from_linestring


def euclidean(node_a, node_b):
    return distance(node_a[-3:-1], node_b[-3:-1]).kilometers
    # *_, lata, lnga, nida = node_a
    # *_, latb, lngb, nidb = node_b
    # return hypot(
    #     lata - latb,
    #     (lnga - lngb) * pow(cos(radians(lngb)), 2)
    # ) * 111.03


class IdentifiedNode(namedtuple('Node', 'id type additional lat lng nid')):

    @classmethod
    def platform(cls, id, sid, did, dpos, lat, lng, nid):
        return cls(id, 'platform', (sid, did, dpos), lat, lng, nid)

    @classmethod
    def point(cls, id, dist, lat, lng, nid=None):
        return cls(id, 'point', dist+0.02, lat, lng, nid)

    @classmethod
    def pointfromdict(cls, id, d, nid=None):
        return cls(id, 'point', d['dist'], d['lat'], d['lng'], nid)

    @property
    def sid(self):
        add = self.additional
        if isinstance(self.additional, tuple):
            return add[0]
        return None

    @property
    def dist(self):
        add = self.additional
        if isinstance(add, (int, float)):
            return add
        return None

    @property
    def did(self):
        add = self.additional
        if isinstance(add, tuple):
            return add[1]
        return None

    @property
    def dpos(self):
        add = self.additional
        if isinstance(add, tuple):
            return add[2]
        return None

    def __eq__(self, other):
        if not isinstance(other, IdentifiedNode):
            return False
        nid = self[-1]
        onid = other[-1]
        if nid is None or onid is None:
            return self[0] == other[0]
        return nid == onid

    def __hash__(self):
        nid = self[-1]
        if nid is None:
            return self[0].__hash__()
        return nid.__hash__()


Node = IdentifiedNode


WALK = 0
TRANSFER = 1
TRANSFER_SAME = 2
SHIFT = 3


Costs = namedtuple('Costs', 'walk transfer transfer_same shift')


tag = '@GisGraph:'


class GisGraph:

    COSTS = Costs(walk=8, transfer=40, transfer_same=-2, shift=2)
    NEIGHBOR_TYPES = {
        'shift': 0,
        'same_platform': 1,
        'same_station': 2,
        'walk': 3
    }

    @property
    def _nodes(self):
        """All nodes of Graph that it works with"""
        return self.__nodes

    def _prep_connection(self, conn) -> None:
        def dist(lat1, lng1, lat2, lng2):
            return distance((lat1, lng1), (lat2, lng2)).kilometers

        conn.create_function(
            'distance',
            4,
            dist
        )
        conn.commit()
        return conn

    def __init__(self, dbconnection, costs=COSTS, platform_walks=0.3, **kwargs):
        super().__init__()
        self.conn = self._prep_connection(dbconnection)
        self.__nodes = []
        self.__dirs = {}
        self.__dlines = {}
        if not isinstance(costs, Costs):
            costs = Costs._make(costs)
        self.costs = costs
        self.platform_walks = platform_walks

        # self.__init_platforms()

        # self.start = start
        # self.destination = destination
        # self.__start_platforms = self.__nearest_platforms(start)
        # self.__dest_platforms = self.__nearest_platforms(destination)

    def reset(self, start=None, destination=None, costs=None, platform_walks=None, **kwargs):
        # if start:
        #     self.start = start
        #     # self.__start_platforms = self.__nearest_platforms(start)
        # if destination:
        #     self.destination = destination
        #     # self.__dest_platforms = self.__nearest_platforms(destination)
        if costs:
            self.costs = costs
        if platform_walks:
            self.platform_walks = platform_walks

    @property
    def minimal_cost(self):
        return self.costs[SHIFT]

    def __init_platforms(self):
        ts = now()

        cursor = self.conn.cursor()
        cursor.execute(*SQLQuery.astarnodes())

        dirs = self.__dirs
        dlines = self.__dlines

        for nid, pid, sid, lat, lng, did, dpos, dline in cursor:
            if did not in dirs:
                dlines[did] = coords_from_linestring(dline)
                dirs[did] = [Node.platform(pid, sid, did, dpos, lat, lng, nid)]
            else:
                dirs[did].append(Node.platform(pid, sid, did, dpos, lat, lng, nid))
        ps = self.__nodes = tuple(chain.from_iterable(dirs.values()))
        print(len(ps))
        print(len(dirs))
        cursor.close()

        print('interval:', now()-ts)

    def __nearest_platforms(self, from_point, dist, minimum=5):
        t = tuple(
            Node.platform(pid, sid, did, dpos, lat, lng, nid)
            for (nid, pid, sid, lat, lng, did, dpos, dist)
            in self.conn.execute(*SQLQuery.pointneighbors(from_point, dist))
        )
        if t:
            return t
        t = tuple(
            Node.platform(pid, sid, did, dpos, lat, lng, nid)
            for (nid, pid, sid, lat, lng, did, dpos)
            in self.conn.cursor().execute(*SQLQuery.pointneighborsminimum(from_point, minimum))
        )
        t = sorted(t, key=lambda n: euclidean(from_point, n))
        return t
        # dist = dist or from_point[2]
        # t = list(
        #     node
        #     for node in self.__nodes
        #     if node is not from_point and euclidean(from_point, node) < dist
        # )
        #
        # if t:
        #     return t
        #
        # return list(
        #     sorted(
        #         self.__nodes,
        #         key=lambda x: euclidean(from_point, x)
        #     )[:minimum]
        # )

    def __platforms(self, p, backward=False, with_type=False):
        return (
            Node.platform(pid, sid, did, dpos, lat, lng, nid)
            for (nid, pid, sid, lat, lng, did, dpos)
            in self.conn.cursor().execute(*SQLQuery.neighbors(p, backward=backward))
        )

        # _dd = -1 if backward else 1
        # pid, _, (sid, did, dpos), lat, lng, nid = p
        #
        # sps = []  # same station transfers
        # cps = []  # same platform transfers
        # np = []  # current directions next platform
        # wps = []  # walk transfers
        #
        # # dp = ()
        # # if backward and p in self.__start_platforms:
        # #     dp = (self.start, )
        # # elif p in self.__dest_platforms:
        # #     dp = (self.destination, )
        #
        # pw = self.platform_walks
        #
        # # def isnposnext(npos):
        # #     return npos < dpos if backward else npos > dpos
        # #
        # # def isnposneighbor(npos):
        # #     return npos == dpos+_dd
        #
        # for node in self.__nodes:
        #     # npid = node[0]
        #     # nsid, ndid, npos = node[2]
        #
        #     npid, _, (nsid, ndid, npos), *_, pnid = node
        #
        #     if node is p:
        #         continue
        #
        #     if ndid == did:
        #         if npos == dpos+_dd:
        #             np.append(node)
        #     elif npid == pid:
        #         cps.append(node)
        #     elif nsid == sid:
        #         sps.append(node)
        #     elif euclidean(p, node) < pw:
        #         wps.append(node)
        #
        # return chain(np, cps, sps, wps)

    def _next_of_node(self, node, backward=False):
        dd = -1 if backward else 1
        did = node.did
        dpos = node.dpos
        for n in self.__nodes:
            if n.did == did and n.dpos == dpos+dd:
                return n
        return None


    def cost(self, from_node, to_node, pure_distance=False):

        if None in (from_node, to_node) or from_node == to_node:
            return 0

        id0, type0, add0, *coords0, fnid = from_node
        id1, type1, add1, *coords1, tnid = to_node

        if 'point' in (type0, type1):
            return self.costs[WALK] * euclidean(from_node, to_node)

        row = self.conn.cursor().execute(*SQLQuery.cost(fnid, tnid)).fetchone()

        type, cost = row

        c = self.costs[TRANSFER]
        if type == 1:
            return c + self.costs[TRANSFER_SAME]
        elif type == 2:
            return c
        elif type == 3:
            return c + (self.costs[WALK] * cost)
        else:
            return cost * self.costs[SHIFT]

        # sid0, did0, dpos0 = add0
        # sid1, did1, dpos1 = add1
        # if did0 == did1:
        #     coords0, coords1 = tuple(coords0), tuple(coords1)
        #     if coords0 == coords1:
        #         d = distance_of_line(self.__dlines[did0])
        #     else:
        #         d = distance_of_lineslice(self.__dlines[did0], tuple(coords0), tuple(coords1))
        #
        #     if not pure_distance:
        #         return d * self.costs[SHIFT]
        #     else:
        #         return d
        #
        # c = self.costs[TRANSFER]
        # if id0 == id1 and did0 != did1:
        #     if not pure_distance:
        #         return c + self.costs[TRANSFER_SAME]
        #     else:
        #         return None
        # if sid0 == sid1:
        #     if not pure_distance:
        #         return c
        #     else:
        #         return None
        # else:
        #     if not pure_distance:
        #         return c + (self.costs[WALK] * euclidean(from_node, to_node))
        #     else:
        #         return euclidean(from_node, to_node)

    def neighbor_type(self, from_node, to_node):
        ntypes = GisGraph.NEIGHBOR_TYPES

        if None in (from_node, to_node) or from_node == to_node:
            return None

        id0, type0, add0, *_ = from_node
        id1, type1, add1, *_ = to_node

        if 'point' in (type0, type1):
            return None
        else:
            sid0, did0, dpos0 = add0
            sid1, did1, dpos1 = add1

            if did0 == did1:
                return ntypes['shift']
            if id0 == id1 and did0 != did1:
                return ntypes['same_platform']
            if sid0 == sid1:
                return ntypes['same_station']
            else:
                return ntypes['walk']

    def neighbors(self, node, backward=False, **kwargs):

        with_cost = kwargs.pop('with_cost', True)
        with_type = kwargs.pop('with_type', False)

        nt = node.type
        ns = None
        if nt == 'point':
            ns = self.__nearest_platforms(node, node.dist)

        elif nt == 'platform':
            ns = self.__platforms(node, backward=backward)

        else:
            raise Exception('Something went wrong')

        def nmapper(n):
            out = [n]
            if with_cost:
                out.append(self.cost(node, n, **kwargs))
            if with_type:
                out.append(self.neighbor_type(node, n))
            return tuple(out)

        return (nmapper(n) for n in ns)
