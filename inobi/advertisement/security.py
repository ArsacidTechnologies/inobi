from jwt import decode, encode

from .utils import debug_exception

from .config import SECURITY_BOX_SECRET

# Old key (TEZ Key) 'GQDstcKsx0NHjPOuXOYg5MbeJ1XT0uFiwDVvVBrk'

# ADMIN_SECRET_KEY = 'BKYnpVzqmY8qeF98eGH6aZjUsLzeuwa3XWdDar4D'

TEMP_ADMIN_PASSWORD = 'lelkekxd'

BOX_TOKEN_VERIFY_OPTIONS = {
   'verify_signature': True,
   'verify_exp': False,
   'verify_nbf': False,
   'verify_iat': False,
   'verify_aud': False,
   'require_exp': False,
   'require_iat': False,
   'require_nbf': False
}


tag = '@advertisement.security:'


def check_box_token(jwt, base64=False, secret=SECURITY_BOX_SECRET, add_scopes=('box',), options=BOX_TOKEN_VERIFY_OPTIONS):
    try:
        payload = decode(jwt, secret, algorithms=['HS256'], options=options)
        if 'scopes' not in payload:
            payload['scopes'] = add_scopes
        else:
            pss = payload['scopes']
            pss = tuple(set(pss).union(add_scopes))
            payload['scopes'] = pss
        return payload
    except Exception as e:
        debug_exception(tag, e)
        return False


def generate_box_token(payload):
    return encode(payload, SECURITY_BOX_SECRET, algorithm='HS256').decode('utf-8')


def check_admin_key(key):
    return key == TEMP_ADMIN_PASSWORD


class Scope:
    ADS_ADMIN = 'advertisement_admin'
    BOX = 'advertisement_admin box'
    APP = 'application'
