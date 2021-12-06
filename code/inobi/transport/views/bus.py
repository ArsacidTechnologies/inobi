from ..import route
from inobi.transport.configs import __url_bus, scope, INOBI_BOX_TOKEN
from ..API.bus_api import bus as bus_ping, listBuses, getUnknownBuses
from flask import request
from inobi.security import secured
from inobi.utils import http_err, http_ok, getargs

# from inobi import app
from flask_cors import cross_origin

# from inobi.security import verify as default_verification
# def my_verification(token: str, base64: bool = True) -> dict:
#     if token == INOBI_BOX_TOKEN:
#         return {'scopes': ['transport_unit(old)']}
#     return default_verification(token, base64=base64)


# @route('/v1/bus', methods=['POST', 'GET'])
# def test():
#     id, lat, lng = getargs(request, 'id', 'lat', 'lng')
#     print(id, lat, lng)
#     return 'ok', 200


# @route(__url_bus['bus'], methods=['POST', 'GET'])
# @secured('transport_admin transport_driver transport_unit(old)'.split(),
#          verify=my_verification)
# def bus():
#     # raw_token = request.headers.get('Authorization', '')
#     # if raw_token.startswith('Bearer '):
#     #     raw_token = raw_token[7:]
#     #     if raw_token != INOBI_BOX_TOKEN:
#     #         return HTTP_ERR('Unauthorized', status=401)
#     id, lat, lng = getargs(request, 'id', 'lat', 'lng')
#     data = dict(
#         id=id
#     )
#     if 'transport_driver' in bus._scopes:
#         id = bus._token_data['transport']['device_id']
#         driver = bus._token_data.get('user')
#         data['id'] = id
#         data['driver'] = driver
#
#     for param in (id, lat, lng):
#         if not param:
#             return http_err('parameter is missing', 400)
#     try:
#         data["lat"] = float(lat)
#         data["lng"] = float(lng)
#     except:
#         return http_err('lat and lng must be digits', 400)
#     response = bus_ping(data)
#     if response['code'] != 200:
#         return http_err(response['message'], response['code'])
#     return http_ok()


# @route(__url_bus['deleteBus'], methods=['POST', 'GET'])
# @cross_origin()
# @secured(scope['admin'])
# def delete_Bus():
#     id = getargs(request, 'id')[0]
#     if not id:
#         return http_err('id parameter is missing', 400)
#     try:
#         data = {
#             "id": int(id)
#         }
#     except:
#         return http_err('id must be digit', 400)
#     response = deleteBus(data)
#     if response['code'] != 200:
#         return http_err(response['message'], response['code'])
#     try:
#         for md in app.config.transport_middleware:
#             md.on_deleted(id)
#     except:
#         pass
#     return http_ok(message=response['message'], data=dict(data=response['data']))


# @route(__url_bus['listBuses'], methods=['POST', 'GET'])
# @cross_origin()
# @secured(scope['viewer'])
# def list_Buses():
#     response = listBuses()
#     if response['code'] != 200:
#         return http_err(message=response['message'], status=response['code'])
#     return http_ok(data=dict(data=response['data']))


# @route(__url_bus['saveBus'], methods=['POST'])
# @cross_origin()
# @secured(scope['admin'])
# def save_Bus():
#     try:
#         data = request.get_json(force=True)
#     except:
#         return http_err('json is not valid', 400)
#     required = ['mac', 'line_id', 'plate']
#     for param in required:
#         if param not in data:
#             return http_err('{} argument is missing'.format(param), 400)
#     data['type'] = data['type'].lower()
#     try:
#         data['number'] = int(data['number'])
#     except:
#         return http_err('number parameter must be digit', 400)
#     response = saveBus(data)
#     if response['code'] != 200:
#
#         return http_err(response['message'], response['code'], data=response.get('data', None))
#
#     try:
#         for md in app.config.transport_middleware:
#             if 'id' not in data:
#                 md.on_saved(response['data'])
#             else:
#                 md.on_updated(response['data'])
#     except:
#         pass
#     return http_ok(message=response['message'], data=dict(data=response['data']))


# @route(__url_bus['getUnknownBuses'], methods=['POST', 'GET'])
# @cross_origin()
# @secured(scope['admin'])
# def get_UnknownBuses():
#     response = getUnknownBuses()
#     if response['code'] != 200:
#         return http_err(response['message'], response['code'])
#     return http_ok(data=dict(data=response['data']))

