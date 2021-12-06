

tag = '@SQLQuery:'


class SQLQuery:

    @staticmethod
    def nearest_platforms(lat, lng, kms=0.6, limit=-1):
        return ('''
SELECT p.* FROM platforms AS p
    INNER JOIN (
        SELECT
            id,
            distance(lat, lng, ?, ?) as dist
        FROM platforms
        WHERE dist < ?
      ) AS d
        ON p.id = d.id
    ORDER BY d.dist
    LIMIT ?
''', (lat, lng, kms, limit))

    @staticmethod
    def station_platforms(sid, pid):
        return ('''
SELECT * FROM platforms
    WHERE sid = ? AND id != ?
''', (sid, pid))

    @staticmethod
    def direction_platforms(pid, did=None):
        return ('''
SELECT n.did AS did, p.* FROM (
        SELECT 
            d.id AS did,
            a.id AS id,
            av.pos+1 AS pos
        FROM directions AS d
            INNER JOIN arrays AS a
                ON d.platforms = a.id
            INNER JOIN array_values AS av
                ON a.id = av.id
            INNER JOIN platforms AS p
                ON av.entry_id = p.id
            WHERE p.id = ?
    ) AS n
    INNER JOIN array_values AS av
        ON av.id = n.id AND n.pos = av.pos
    INNER JOIN platforms AS p
        ON av.entry_id = p.id
''', (pid,))

    @staticmethod
    def allplatforms():
        return ('''
SELECT d.id AS did, av.pos AS pos, d.line AS dline, p.* FROM directions AS d
    INNER JOIN arrays AS a
        ON a.id = d.platforms
    INNER JOIN array_values AS av
        ON av.id = a.id
    INNER JOIN platforms AS p
        ON av.entry_id = p.id
    ORDER BY did, pos
''', ())

    @staticmethod
    def astarnodes():
        return ('''
SELECT n.*, d.line AS dline FROM as_nodes n
    INNER JOIN directions d
        ON n.did = d.id
    ORDER BY did, dpos
''', ())

    @staticmethod
    def pointneighbors(point, dist):
        *_, lat, lng, nid = point
        return ('''
SELECT n.*, d.dist FROM as_nodes n
    INNER JOIN (
        SELECT nid, distance(lat, lng, ?, ?) AS dist
        FROM as_nodes
        WHERE dist < ?
    ) d
        ON d.nid = n.nid
    ORDER BY d.dist
''', (lat, lng, dist))

    @staticmethod
    def pointneighborsminimum(point, min=5):
        *_, lat, lng, nid = point
        return ('''
SELECT n.* FROM as_nodes n
    INNER JOIN (
        SELECT nid, (abs(?-lat) + abs(?-lng)) AS dist
        FROM as_nodes
    ) d
        ON d.nid = n.nid
    ORDER BY d.dist ASC
    LIMIT ?
''', (lat, lng, min))

    @staticmethod
    def neighbors(node, backward=False):
        return ('''
SELECT n.*
    FROM as_node_neighbors nn
    INNER JOIN as_nodes n
        ON n.nid = nn.nto
    WHERE type != ? AND nfrom = ?
    ORDER BY nn.type, nn.cost
''', (0 if backward else -1, node.nid))

    @staticmethod
    def cost(nfrom, nto):
        return ('''
SELECT type, cost 
    FROM as_node_neighbors nn
    INNER JOIN (SELECT ? as nfrom, ? as nto) i
    WHERE 
        nn.nfrom = i.nfrom AND nn.nto = i.nto
        OR nn.nfrom = i.nto AND nn.nto = i.nfrom AND type > 0
    LIMIT 1
''', (nfrom, nto))

    @staticmethod
    def directions(dids):
        return('''
SELECT * 
    FROM directions
    WHERE id IN ({})'''.format(', '.join('?' for d in dids)), dids)

    @staticmethod
    def detailedplatforms(pids):
        qmarks = ', '.join('?' for _ in pids)
# id sid lat lng name full_name
        return ('''
SELECT p.id, s.id, p.lat, p.lng, s.name, s.full_name 
    FROM platforms p
    INNER JOIN station_platforms sp
        ON sp.entry_id = p.id
    INNER JOIN stations s
        ON sp.id = s.id
    WHERE p.id IN ({})'''.format(qmarks), pids)

    @staticmethod
    def detaileddirections(dids):
        qmarks = ', '.join(('?' for _ in dids))
# id route_id type platforms line route_type name from_name to_name
        return ('''
SELECT d.id, r.id, d.type, d.line, r.type, r.name, r.from_name, r.to_name
    FROM directions d
    INNER JOIN route_directions rd
        ON rd.entry_id = d.id
    INNER JOIN routes r
        ON rd.id = r.id
    WHERE d.id IN ({})'''.format(qmarks), dids)

