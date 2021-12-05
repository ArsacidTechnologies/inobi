from flask import abort

from inobi.security import verify as _verify


tag = '@app.security:'

ID_KEY = 'id'


def verify(jwt, return_full_data=True, **kwargs):
    if not jwt:
        return False

    token_data = _verify(jwt, **kwargs)
    if not token_data:
        return False

    if return_full_data:
        return token_data
    return token_data[ID_KEY]


def check_with_abort(token, verifier=verify, **kwargs):
    if not verifier(token, **kwargs):
        abort(401)
