import requests
from requests.auth import HTTPBasicAuth
from inobi.transport.configs import traccar_url, traccar_password, traccar_username, TRACCAR_SQL_CONNECTION
from inobi.transport.exceptions import TransportException
import psycopg2
from .remote_db import get_devices as db_devices


def get_users():
    r = requests.get(traccar_url + '/users', auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /users {} {}'.format(r.status_code, r.text)
        raise TransportException(text, 400)
    return r.json()


def save_user(name: str, password: str, readonly: bool=True, attrs: dict=None):
    body = dict(
        name=name,
        email=name,
        password=password,
        readonly=readonly
    )
    if attrs:
        body['attributes'] = attrs
    r = requests.post(traccar_url + '/users',
                      json=body,
                      auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'POST /users {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def get_devices(user_id: int=None):
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        devices = db_devices(conn)
        return devices
    params = dict()
    if user_id:
        params['userId'] = user_id
    else:
        params['all'] = True
    r = requests.get(traccar_url + '/devices',
                     params=params,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /devices {} {} {}'.format(r.status_code, r.text, params)
        raise TransportException(text, 400)
    return r.json()


def save_device(name: str, unique_id: str, group_id=None, phone: str=None, attrs: dict=None):
    body = dict(
        name=name,
        uniqueId=unique_id
    )
    if attrs:
        if not isinstance(attrs, dict):
            raise AttributeError('attrs must be dict type')
        body['attributes'] = attrs
    if phone:
        body['phone'] = phone
    if group_id:
        body['groupId'] = group_id
    r = requests.post(traccar_url + '/devices',
                      json=body,
                      auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'POST /devices {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def update_device(id: int, name: str, unique_id: str, group_id=None, phone: str=None, attrs: dict=None):
    body = dict(
        id=id,
        name=name,
        uniqueId=unique_id
    )
    if attrs:
        if not isinstance(attrs, dict):
            raise AttributeError('attrs must be dict type')
        body['attributes'] = attrs
    if phone:
        body['phone'] = phone
    if group_id:
        body['groupId'] = group_id
    r = requests.put(traccar_url + '/devices/{}'.format(id),
                     json=body,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'PUT /devices {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def delete_device(id: int):
    requests.delete(traccar_url + '/devices/{}'.format(id),
                    auth=HTTPBasicAuth(traccar_username, traccar_password))
    return 200


def get_groups(user_id: int=None):
    params = dict()
    if user_id:
        params['userId'] = user_id
    else:
        params['all'] = True
    r = requests.get(traccar_url + '/groups',
                     params=params,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /groups {} {} {}'.format(r.status_code, r.text, params)
        raise TransportException(text, 400)
    return r.json()


def save_group(name: str, attrs: dict=None, group_id: int=None):
    body = dict(name=name)
    if attrs:
        if not isinstance(attrs, dict):
            raise AttributeError('attrs must be dict type')
        body['attributes'] = attrs
    if group_id:
        body['groupId'] = group_id
    r = requests.post(traccar_url + '/groups',
                      json=body,
                      auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /groups {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def update_group(id: int, name: str, attrs: dict=None):
    body = dict(name=name)
    if attrs:
        body['attributes'] = attrs
    r = requests.put(traccar_url + '/groups/{}'.format(id),
                     json=body,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /groups {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def delete_group(id: int):
    r = requests.delete(traccar_url + '/groups/{}'.format(id),
                        auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'DELETE /groups {} {} {}'.format(r.status_code, r.text, id)
        raise TransportException(text, 400)
    return r.json()


def get_geofences(group_id: int=None, user_id: int=None):
    params = dict()
    if group_id:
        params['groupId'] = group_id
    elif user_id:
        params['userId'] = user_id
    else:
        params['all'] = True
    r = requests.get(traccar_url + '/geofences',
                     params=params,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'GET /geofences {} {} {}'.format(r.status_code, r.text, params)
        raise TransportException(text, 400)
    return r.json()


def save_geofence(name: str, area: str, description: str=None, attrs: dict=None):
    body = dict(
        name=name,
        area=area
    )
    if description:
        body['description'] = description
    if attrs:
        body['attributes'] = attrs
    r = requests.post(traccar_url + '/geofences',
                      json=body,
                      auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'POST /geofences {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def update_geofences(id: int, name: str, area: str, description: str=None, attrs: dict=None):
    body = dict(
        name=name,
        area=area
    )
    if description:
        body['description'] = description
    if attrs:
        body['attributes'] = attrs
    r = requests.put(traccar_url + '/geofences/{}'.format(id),
                     json=body,
                     auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 200:
        text = 'PUT /geofences {} {} {}'.format(r.status_code, r.text, body)
        raise TransportException(text, 400)
    return r.json()


def save_permission(url, user_id=None, device_id=None, group_id=None, geofence_id=None):
    body = dict()
    if user_id:
        body['userId'] = user_id
    if device_id:
        body['deviceId'] = device_id
    if group_id:
        body['groupId'] = group_id
    if geofence_id:
        body['geofenceId'] = geofence_id

    r = requests.post(traccar_url + '/permissions',
                      json=body,
                      auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 204:
        text = 'POST /permissions {} {} {}'.format(r.status_code, r.text, str(body))
        raise TransportException(text, 400)
    return 200


def delete_permissions(url, user_id=None, device_id=None, group_id=None, geofence_id=None):
    body = dict()
    if user_id:
        body['userId'] = user_id
    if device_id:
        body['deviceId'] = device_id
    if group_id:
        body['groupId'] = group_id
    if geofence_id:
        body['geofenceId'] = geofence_id
    r = requests.delete(traccar_url + '/permissions',
                        json=body,
                        auth=HTTPBasicAuth(traccar_username, traccar_password))
    if r.status_code != 204:
        text = 'DELETE /permissions {} {} {}'.format(r.status_code, r.text, str(body))
        raise TransportException(text, 400)
    return 200