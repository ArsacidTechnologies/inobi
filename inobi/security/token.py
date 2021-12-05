from time import time as now
from typing import NewType, Dict, Union, Iterable

from base64 import b64encode

from jwt import decode, encode
from jwt.exceptions import InvalidTokenError

from inobi.config import APP_TOKEN_SECRET
from inobi.utils import decode_base64
from flask import current_app


Token = NewType('Token', str)


tag = '@Inobi.security:'

OPTIONS = {
   'verify_signature': True,
   'verify_exp': True,
   'verify_nbf': False,
   'verify_iat': True,
   'verify_aud': False,
   'require_exp': False,
   'require_iat': False,
   'require_nbf': False
}


def verify(token: Token, secret=APP_TOKEN_SECRET, decode_options=OPTIONS, base64=True) -> Union[bool, Dict]:
    if not token:
        return False
    if not isinstance(token, str):
        return False
    # if len(token) == 36:
    #     data = current_app.app_auth.payload(token)
    #     scopes = data.get('scopes', [])
    #     scopes.append('application_public')
    #     data['scopes'] = scopes
    #     return data
    if base64:
        try:
            token = decode_base64(token)
        except:
            return False
    try:
        data = decode(
            jwt=token,
            key=secret,
            algorithms=['HS256'],
            options=decode_options,
        )
        return data
    except InvalidTokenError:
        return False


def sign(payload: Dict, scopes: Union[str, Iterable[str]] = (),
         secret=APP_TOKEN_SECRET, expires_after=10,
         base64ify=True) -> Token:
    """
    Signs payload (aka data, dict) with key

    :param payload:             data to sign
    :param scopes:              scopes to include. If 'scopes' in payload, updates it with given ones
    :param secret:              secret to sign with (should not touch it, default is Inobi App Token from configs)
    :param expires_after:       expiration interval in minutes
    :param base64ify:           encode to base64 or not, default True
    :return:                    token (aka jwt)
    """

    if isinstance(scopes, str):
        scopes = scopes.split()

    p = dict(payload)
    ts = int(now())

    _pscopes = p.get('scopes')
    if not _pscopes:
        _pscopes = scopes
    elif _pscopes and scopes:
        _pscopes = list(set(scopes).union(set(_pscopes)))
    else:
        _pscopes = list()
    p['scopes'] = _pscopes

    p['iat'] = ts
    if expires_after is not None:
        p['exp'] = ts + (expires_after*60)

    token = encode(
        payload=p,
        key=secret,
        algorithm='HS256'
    ).decode('utf-8')

    if base64ify:
        return b64encode(token.encode()).decode()
    return token


def main():

    data = {
        'kek': 'lel',
        'xd': 'lol',
        'id': 'lalal'
    }
    token = sign(data)
    print(tag, token)

    payload = verify(token)
    print(tag, payload)


if __name__ == '__main__':
    main()
