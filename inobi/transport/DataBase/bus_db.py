import json
import psycopg2
from inobi.config import SQL_CONNECTION



SQL_COLUMN_ID = 0
SQL_COLUMN_MAC = 1
SQL_COLUMN_LINE = 2
SQL_COLUMN_NUMBER = 3
SQL_COLUMN_TYPE = 4
SQL_COLUMN_PLATE = 5
SQL_COLUMN_DRIVER = 6
SQL_COLUMN_DEVICE_PHONE = 7

def __parse_sql_bus(item):
    return dict(
        id=item[SQL_COLUMN_ID],
        mac=item[SQL_COLUMN_MAC],
        line_id=item[SQL_COLUMN_LINE],
        number=int(item[SQL_COLUMN_NUMBER]) if item[SQL_COLUMN_NUMBER] else None,
        type=item[SQL_COLUMN_TYPE],
        plate=item[SQL_COLUMN_PLATE],
        driver=json.loads(item[SQL_COLUMN_DRIVER])
        if isinstance(item[SQL_COLUMN_DRIVER], str)
        else item[SQL_COLUMN_DRIVER],
        device_phone=item[SQL_COLUMN_DEVICE_PHONE]
    )

# def __parse_new_sql_bus(item):
#     return dict(
#         id=item[0],
#         device_id=item[1],
#         line_id=item[2],
#         device_phone=item[3],
#         driver=item[4],
#         name=item[5],
#         independent=item[6],
#         payload=item[7]
#     )

# def createBus(self, jBus):
#     selectsql = '''
#         select id, mac, line_id, number, type, plate, driver, device_phone
#         from buses
#         where mac = %s
#     '''
#     SQL = '''
#         INSERT INTO transports
#             (device_id, line_id, name, driver, device_phone, independent, payload)
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#         RETURNING
#             id, device_id, line_id, device_phone, driver, name, independent, payload
#     '''
#     sql_lines = '''
#         select name, type from routes where id = %s
#     '''
#     oldSQL = '''
#         INSERT INTO buses
#             (mac, line_id, number, type, plate, driver, device_phone)
#
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#         RETURNING
#             id, mac, line_id, number, type, plate, driver, device_phone
#     '''
#     sqlAttrs = (
#         jBus.get('device_id') or jBus.get('mac'),
#         jBus['line_id'],
#         jBus.get('name') or jBus['plate'],
#         jBus.get('driver') if isinstance(jBus.get('driver', ''), int) else None,
#         jBus.get('device_phone', None),
#         jBus.get('independent', True),
#         jBus.get('payload')
#     )
#     self.create_conn()
#     exist = self.do(selectsql, params=(jBus['mac'],), out=True)
#     if exist['code'] == 404:
#         sqlData = self.do(SQL, params=sqlAttrs, out=True, commit=True)
#     else:
#         sqlData = dict(code=418, message='record already exists',
#                        data=dict(data=self.__parse_sql_bus(exist['data'][0])))


    # if sqlData['code'] != 200:
    #     return sqlData
    # buses = []
    # for item in sqlData['data']:
    #     bus = self.__parse_new_sql_bus(item)
    #     oldFormatBus = dict()
    #     oldFormatBus['id'] = bus['id']
    #     oldFormatBus['line_id'] = bus['line_id']
    #     oldFormatBus['mac'] = bus['device_id']
    #     oldFormatBus['driver'] = bus['driver']
    #     oldFormatBus['plate'] = bus['name']
    #     oldFormatBus['device_phone'] = bus['device_phone']
    #     sql_routes = self.do(sql_lines, params=(bus['line_id'],), out=True)
    #     self.close_conn()
    #     if sql_routes['code'] != 200:
    #         oldFormatBus['number'] = None,
    #         oldFormatBus['type'] = None
    #     else:
    #         route = sql_routes['data']
    #         oldFormatBus['number'] = route[0][0]
    #         oldFormatBus['type'] = route[0][1]
    #
    #     buses.append(oldFormatBus)
    # return dict(data=buses, code=200, message='OK')

def findBusByMac(mac):
    SQL = '''
        SELECT id, mac, line_id, number, type, plate, driver, device_phone
        FROM buses
        WHERE mac = %s
    '''

    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL, (mac,))
            sqlData = cursor.fetchall()
            if not sqlData:
                return dict(code=404, message='data not found')
            buses = []
            for item in sqlData:
                bus = __parse_sql_bus(item)
                buses.append(bus)
            return dict(data=buses, code=200, message='OK')

def findBusById(id):
    SQL = '''
        SELECT id, mac, line_id, number, type, plate, driver, device_phone
        FROM buses
        WHERE id = %s
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL, (id,))
            sqlData = cursor.fetchall()

            buses = []
            for item in sqlData:
                bus = __parse_sql_bus(item)
                buses.append(bus)
            return dict(data=buses, code=200, message='OK')

def getBuses():
    SQL = '''
        SELECT id, mac, line_id, number, type, plate, driver, device_phone
        FROM buses
    '''
    with psycopg2.connect(SQL_CONNECTION) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SQL)
            sqlData = cursor.fetchall()

            buses = []
            t_buses = []
            s_bus = []
            unknown = []
            for item in sqlData:
                bus = __parse_sql_bus(item)
                if bus['type'].lower() == 'bus':
                    buses.append(bus)
                elif bus['type'].lower() == 'trolleybus':
                    t_buses.append(bus)
                elif bus['type'].lower() == 'shuttle_bus':
                    s_bus.append(bus)
                else:
                    unknown.append(bus)
            jResult = {
                "bus": buses,
                "trolleybus": t_buses
            }
            if s_bus:
                jResult['shuttle_bus'] = s_bus
            if unknown:
                jResult['unknown'] = unknown
            return dict(data=jResult, code=200, message='OK')

# def updateBus(jBus):
#     SQL = '''
#         UPDATE transports SET
#             device_id = %s,
#             line_id = %s,
#             name = %s,
#             driver = %s,
#             device_phone = %s,
#             independent = %s,
#             payload = %s
#         WHERE id = %s
#         RETURNING
#             id, device_id, line_id, device_phone, driver, name, independent, payload
#     '''
#     sql_lines = '''
#         select name, type from routes where id = %s
#     '''
#     sqlAttrs = (
#         jBus.get('device_id') or jBus.get('mac'),
#         jBus['line_id'],
#         jBus.get('name') or jBus['plate'],
#         jBus.get('driver')
#         if isinstance(jBus.get('driver'), int)
#         else None,
#         jBus.get('device_phone'),
#         jBus.get('independent', True),
#         jBus.get('payload'),
#         jBus['id']
#     )
#     self.create_conn()
#     sqlData = self.do(SQL, params=sqlAttrs, out=True, commit=True)
#
#     if sqlData['code'] != 200:
#         return sqlData
#
#     buses = []
#     for item in sqlData['data']:
#         bus = self.__parse_new_sql_bus(item)
#         oldFormatBus = dict()
#         oldFormatBus['id'] = bus['id']
#         oldFormatBus['line_id'] = bus['line_id']
#         oldFormatBus['mac'] = bus['device_id']
#         oldFormatBus['driver'] = bus['driver']
#         oldFormatBus['plate'] = bus['name']
#         oldFormatBus['device_phone'] = bus['device_phone']
#         sql_routes = self.do(sql_lines, params=(bus['line_id'],), out=True)
#         self.close_conn()
#
#         if sql_routes['code'] != 200:
#             oldFormatBus['number'] = None,
#             oldFormatBus['type'] = None
#         else:
#             route = sql_routes['data']
#             oldFormatBus['number'] = route[0][0]
#             oldFormatBus['type'] = route[0][1]
#
#         buses.append(oldFormatBus)
#     return dict(data=buses, code=200, message='OK')

# def deleteBus(self, id):
#     SQL = '''
#         DELETE FROM transports
#         WHERE id = %s
#         RETURNING
#             id, device_id, line_id, device_phone, driver, name, independent, payload
#     '''
#     sql_lines = '''
#         select name, type from routes where id = %s
#     '''
#     self.create_conn()
#     sqlData = self.do(SQL, params=(id,), out=True, commit=True)
#
#     if sqlData['code'] != 200:
#         return sqlData
#
#     buses = []
#     for item in sqlData['data']:
#         bus = self.__parse_new_sql_bus(item)
#         oldFormatBus = dict()
#         oldFormatBus['id'] = bus['id']
#         oldFormatBus['line_id'] = bus['line_id']
#         oldFormatBus['mac'] = bus['device_id']
#         oldFormatBus['driver'] = bus['driver']
#         oldFormatBus['plate'] = bus['name']
#         oldFormatBus['device_phone'] = bus['device_phone']
#         sql_routes = self.do(sql_lines, params=(bus['line_id'],), out=True)
#         self.close_conn()
#         if sql_routes['code'] != 200:
#             oldFormatBus['number'] = None,
#             oldFormatBus['type'] = None
#         else:
#             route = sql_routes['data']
#             oldFormatBus['number'] = route[0][0]
#             oldFormatBus['type'] = route[0][1]
#         buses.append(oldFormatBus)
#     return dict(data=buses, code=200, message='OK')
