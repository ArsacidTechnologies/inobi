from math import inf as INF
import typing as T
import polyline as PL


from geopy.distance import distance


def sortedsetarray(iterable):
    out = []
    for i in iterable:
        if i not in out:
            out.append(i)
    return out

Polyline = str
_Number = T.Union[float, int]
_Coord = T.Tuple[_Number, _Number]


def coords_from_linestring(linestring):
    return linestring_to_coords(linestring, asdict=True)


def linestring_to_coords(linestring, asdict=False):
    mapper = (lambda x: dict(zip(('lat', 'lng'), x))) if asdict else lambda x: tuple(x)
    strcoords = (
        mapper(map(float, ch.split()))
        for ch in linestring[linestring.rindex('(', 0, 30) + 1:linestring.index(')', -20)].split(',')
    )
    return list(strcoords)


def polyline_to_coords(polyline: Polyline) -> T.List[_Coord]:
    return PL.decode(polyline)


def coords_to_polyline(coords: T.List[_Coord]) -> Polyline:
    return PL.encode(coords)


def sliceline(line: T.List[_Coord], coord1: _Coord, coord2: _Coord, as_dict=False):
    _coord1 = (*coord1, 1)
    _coord2 = (*coord2, 2)

    bundle = {}
    for i, c in enumerate(line):
        cc = c
        d1 = distance(_coord1, cc).meters
        d2 = distance(_coord2, cc).meters
        if _coord1 not in bundle or bundle[_coord1][0] > d1:
            bundle[_coord1] = (d1, i)
        if _coord2 not in bundle or bundle[_coord2][0] > d2:
            bundle[_coord2] = (d2, i)
    try:
        si, di = sorted([i for (d, i) in bundle.values()])
    except:
        print(bundle, _coord1, _coord2, line, sep='\n')
        raise

    if di+1 < len(line):
        di += 1
    if as_dict:
        return (
            dict(lat=coord1[0], lng=coord1[1]),
            *(dict(lat=c[0], lng=c[1]) for c in line[si:di]),
            dict(lat=coord2[0], lng=coord2[1])
        )
    return (
        coord1,
        *((c[0], c[1]) for c in line[si:di]),
        coord2
    )


def distance_of_lineslice(line, coord1, coord2):
    l = sliceline(line, coord1, coord2)
    s = []
    for i, c in enumerate(l):
        if i == 0:
            continue
        prev = l[i-1]
        s.append(distance(prev, c))

    dist = sum(s, distance()).kilometers
    return dist


def distance_of_line(line):
    s = []
    for i, c in enumerate(line):
        if i == 0:
            continue
        prev = line[i - 1]
        s.append(distance((prev['lat'], prev['lng']), (c['lat'], c['lng'])))

    dist = sum(s, distance()).kilometers
    return dist


def _recover_path(start, goal, prevs, **kwargs):
    path = []
    p = goal
    while p != start:
        path.append(p)
        p = prevs[p]
    path.append(p)

    if not kwargs.get('reverse', False):
        path.reverse()

    # print('Path length:', len(path))

    return path


def _recover_bidirectional(start, goal, middle, prevs, bprevs, **kwargs):

    ps = _recover_path(start, middle, prevs, **kwargs)[:-1]
    pg = _recover_path(goal, middle, bprevs, **kwargs)[::-1]

    # print(*ps, '', *pg, sep='\n')

    return ps + pg
