from ...organization import bp
from inobi.security import secured
from inobi.utils import http_err, http_ok, picture_from_base64

from flask_cors import cross_origin
from flask import request

from ...API.transport_v2 import get_all_transport

from ...API.transport_v2 import get_transport, delete_transport, save_transport, update_transport
from flask import current_app as app, send_from_directory
from inobi.transport.configs import TRANSPORT_PICTURE_DIRECTORY
from ... import transport_middlewares
import uuid
from ..views import logger

from inobi.transport.API.bus_api import clear_redis
from inobi.transport import error_codes as ec


@bp.route('/v1/buses/picture/<filename>')
@cross_origin()
def download_picture(filename):
    return send_from_directory(TRANSPORT_PICTURE_DIRECTORY, filename)


def convert_empty_str_to_none(data: dict):
    for k, v in data.items():
        if not data[k] and isinstance(data[k], str):
            data[k] = None
    return data


@bp.route('/v1/buses', methods=['GET'])
@cross_origin()
@secured('transport_viewer')
def transport_view(token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403, error_code=ec.ACCESS_DENIED)

    _id = request.args.get('id')

    if not _id:
        response = get_all_transport(organization_id)
    else:
        try:
            _id = int(_id)
        except:
            return http_err('id must be digit', 400, error_code=ec.ID_MUST_BE_DIGIT)
        response = get_transport(_id, organization_id)
    return http_ok(dict(data=response))


@bp.route('/v1/buses', methods=['PATCH', 'PUT', 'DELETE', 'POST'])
@cross_origin()
@secured('transport_admin')
def transport_update(token_data):
    organization = token_data.get('transport_organization')
    if not organization:
        return http_err("Organization Data Is Missing", 403, error_code=ec.ACCESS_DENIED)
    organization_id = organization.get('id')
    if not organization_id:
        return http_err("Organization Id Is Missing", 403, error_code=ec.ACCESS_DENIED)

    if request.method == 'DELETE':
        _id = request.args.get('id')
        if not _id:
            return http_err('id parameter is missing', 400, error_code=ec.MISSING_ID)
        try:
            _id = int(_id)
        except:
            return http_err('id must be digit', 400, error_code=ec.ID_MUST_BE_DIGIT)

        transport = delete_transport(_id, organization_id)
        logger.info('ip:{} deleted transport {}'.format(request.remote_addr, _id))
        transport_md = dict()
        for md in transport_middlewares:
            try:
                md.on_deleted(_id)
                transport_md[md.get_name()] = 'OK'
            except Exception as e:
                logger.exception('ip:{} MD delete {} {}'.format(request.remote_addr, md.get_name(), e))
                transport_md[md.get_name()] = str(e)
        return http_ok(dict(data=transport), transport_md=transport_md)
    data = request.get_json(force=True, silent=True)
    if not data:
        return http_err('json required', 400, error_code=ec.JSON_REQUIRED)
    issuer = token_data['user']['id']
    if 'payload' in data:
        if not isinstance(data['payload'], dict):
            return http_err('payload must be dictionary', 400, error_code=ec.PAYLOAD_MUST_BE_DICTIONARY)
        if 'picture' in data['payload']:
            return http_err('picture parameter must be in first level json', 400,)
    data = convert_empty_str_to_none(data)

    # PICTURE WORK
    pic = None
    pic_filename = None
    if 'picture' in data:
        if data['picture']:
            try:
                pic = picture_from_base64(data['picture'])
            except Exception as e:
                return http_err(str(e), 400, error_code=ec.INVALID_PICTURE)
            pic_filename = '{}.png'.format(uuid.uuid4())
            data['payload']['picture'] = pic_filename
        else:
            data['payload']['picture'] = None
    if 'driver' in data:
        data.pop('driver')
    if request.method == 'POST':
        if 'device_id' not in data:
            return http_err('device_id is missing', 400, error_code=ec.EMPTY_DEVICE_ID_PARAMETER)
        if not isinstance(data['device_id'], str):
            return http_err('device_id must be string', 400, error_code=ec.DEVICE_ID_MUST_BE_STRING)
        if 'line_id' not in data:
            return http_err('line_id is missing', 400, error_code=ec.EMPTY_LINE_ID_PARAMETER)
        if not isinstance(data['line_id'], int):
            return http_err('line_id must be int', 400, error_code=ec.LINE_ID_MUST_BE_INT)
        if 'ip' not in data:
            return http_err('ip is missing', 400, error_code=ec.EMPTY_IP_PARAMETER)
        if 'port' not in data:
            return http_err('port is missing', 400, error_code=ec.EMPTY_PORT_PARAMETER)
        if 'tts' not in data:
            return http_err('tts is missing', 400, error_code=ec.EMPTY_TTS_PARAMETER)

        transport = save_transport(organization_id=organization_id, **data)
        if pic:
            pic.save(TRANSPORT_PICTURE_DIRECTORY + '/' + pic_filename, 'PNG')
        logger.info('ip:{} saved {}'.format(request.remote_addr, transport['device_id']))
        transport_md = dict()
        for md in transport_middlewares:
            try:
                md.on_saved(transport)
                transport_md[md.get_name()] = 'OK'
            except Exception as e:
                logger.exception('ip:{} MD save {} {}'.format(request.remote_addr, md.get_name(), e))
                transport_md[md.get_name()] = str(e)
        return http_ok(dict(data=transport), transport_md=transport_md)

    elif request.method == 'PUT':
        if 'id' not in data:
            return http_err('id is missing', 400, error_code=ec.MISSING_ID)
        if not isinstance(data['id'], int):
            return http_err('id must be int', 400, error_code=ec.ID_MUST_BE_DIGIT)
        if 'device_id' not in data:
            return http_err('device_id is missing', 400, error_code=ec.EMPTY_DEVICE_ID_PARAMETER)
        if not isinstance(data['device_id'], str):
            return http_err('device_id must be string', 400, error_code=ec.DEVICE_ID_MUST_BE_STRING)
        if 'line_id' not in data:
            return http_err('line_id is missing', 400, error_code=ec.EMPTY_LINE_ID_PARAMETER)
        if not isinstance(data['line_id'], int):
            return http_err('line_id must be int', 400, error_code=ec.LINE_ID_MUST_BE_INT)
        if 'device_phone' not in data:
            return http_err('device_phone is missing', 400, error_code=ec.EMPTY_DEVICE_PHONE_PARAMETER)
        if 'name' not in data:
            return http_err('name is missing', 400, error_code=ec.EMPTY_NAME_PARAMETER)
        # if 'ip' not in data:
        #     return http_err('ip is missing', 400, error_code=ec.EMPTY_IP_PARAMETER)
        # if 'port' not in data:
        #     return http_err('port is missing', 400, error_code=ec.EMPTY_PORT_PARAMETER)
        # if 'tts' not in data:
        #     return http_err('tts is missing', 400, error_code=ec.EMPTY_TTS_PARAMETER)


    else:
        if 'id' not in data:
            return http_err('id is missing', 400, error_code=ec.MISSING_ID)
        if not isinstance(data['id'], int):
            return http_err('id must be int', 400, error_code=ec.ID_MUST_BE_DIGIT)
        if 'device_id' in data:
            if not isinstance(data['device_id'], str):
                return http_err('device_id must be string', 400, error_code=ec.DEVICE_ID_MUST_BE_STRING)
        if 'line_id' in data:
            if not isinstance(data['line_id'], int):
                return http_err('line_id must be int', 400, error_code=ec.LINE_ID_MUST_BE_INT)
        # if 'ip' not in data:
        #     return http_err('ip is missing', 400, error_code=ec.EMPTY_IP_PARAMETER)
        # if 'port' not in data:
        #     return http_err('port is missing', 400, error_code=ec.EMPTY_PORT_PARAMETER)
        # if 'tts' not in data:
        #     return http_err('tts is missing', 400, error_code=ec.EMPTY_TTS_PARAMETER)
    transport = update_transport(organization_id=organization_id, issuer=issuer, **data)
    if pic:
        pic.save(TRANSPORT_PICTURE_DIRECTORY + '/' + pic_filename, 'PNG')
    logger.info('ip:{} updated {}'.format(request.remote_addr, transport['device_id']))
    transport_md = dict()
    for md in transport_middlewares:

        try:
            md.on_updated(transport)
            transport_md[md.get_name()] = 'OK'
        except Exception as e:
            logger.exception('ip:{} MD update {} {}'.format(request.remote_addr, md.get_name(), e))
            transport_md[md.get_name()] = str(e)
    return http_ok(dict(data=transport), transport_md=transport_md)