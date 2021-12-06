from requests import get, exceptions
from time import time as now

from ..config import FACEBOOK_APP_ACCESS_TOKEN, FACEBOOK_APP_ID


tag = "@{}:".format(__name__)


FACEBOOK_API_HOST = 'https://graph.facebook.com'

FACEBOOK_API_DEBUG_TOKEN = FACEBOOK_API_HOST+'/debug_token'
FACEBOOK_API_ME = FACEBOOK_API_HOST+'/me'

APP_ID = FACEBOOK_APP_ID
APP_ACCESS_TOKEN = FACEBOOK_APP_ACCESS_TOKEN

ID_KEY = 'user_id'


def verify(token, return_full_data=True):
    data = dict(input_token=token, access_token=APP_ACCESS_TOKEN)
    try:
        r = get(FACEBOOK_API_DEBUG_TOKEN, params=data, timeout=3)
    except exceptions.Timeout:
        return False

    json = r.json()

    if 'error' in json:
        return False
        # raise Exception(json['error']['message'])

    data = json['data']

    if 'error' in data:
        return False
        # raise Exception(data['error']['message'])

    if data['app_id'] != APP_ID:
        return False
        # raise Exception('Not Allowed App: {}'.format(data['app_id']))

    if data['expires_at'] < now():
        return False
        # raise Exception('Expired token')

    if not data['is_valid']:
        return False
        # raise Exception('Not Valid')

    if return_full_data:
        d = fetch_facebook_info(token)
        d[ID_KEY] = d['id']
        return d

    return data[ID_KEY]


def fetch_facebook_info(token, fields='verified,id,name,email,timezone,locale,gender,picture,installed,age_range,link'.split(',')):

    data = dict(access_token=token, fields=','.join(fields))
    r = get(FACEBOOK_API_ME, params=data)

    json = r.json()

    return json
