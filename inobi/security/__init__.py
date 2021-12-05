
from functools import wraps
from base64 import b64decode

from inobi.utils import getargs
from .token import verify, sign

from typing import Union, Iterable, Dict, Callable

from inspect import signature

from .. import error_codes


tag = '@inobi.security:'

GOD_SCOPES = frozenset(['inobi', ])


ACCESS_ROLES = dict(
    inobi=0,
    admin=1,
    viewer=2,
    public=3
)
PROJECTS = frozenset(['transport', 'advertisement', 'application'])
DISABLED = frozenset(['disabled'])


class SecurityException(Exception):

    def __init__(self, view, reason, error_code):
        self.view = view
        self.reason = reason
        self.error_code = error_code


def secured(scopes: Union[str, Iterable[str]] = (), allow_from_headers=True,
            include_god=True, else_answer=None, expect_base64=True,
            verify: Callable[[str], Dict] = verify,
            token_key: str = 'token', token_data_key: str = 'token_data',
            scopes_key: str = 'scopes'
            ):
    """
    Security checker decorator

    Usage:
    @route('/some/route')
    @secured(scopes='admin moderator')
    def some_route():
        ...

    or:
    @route('/some/route')
    @secured(scopes=['admin', 'moderator'], else_answer=403)
    def some_route():
        ...

    Original token and token data available inside decorated func
    by its _token and _token_data attributes if needed

    Note: scopes parameter can be iterable or string. String are splitted
    Note: 'god' scope appended to given ones by default

    :param scopes:                  allowed scopes as iterable or string
    :param allow_from_headers:      allow token lookup in request.headers
    :param include_god:             include or not GOD_SCOPES. Default is True
    :param else_answer:             passed to flask's abort func (http code or response obj)
    :param expect_base64:           expect token encoded in base64 or not, default True
    :param verify:                  a verification func. Must return payload if verified
    :return:                        throws 401 or wrapped func's results
    """

    # if isinstance(scopes, str):
    #     scopes = scopes.split()
    # if include_god:
    #     _scopes = set(scopes).union(GOD_SCOPES)

    # IF NO SCOPE PASSED, _scopes WILL BE INOBI OR GOD_SCOPE
    if scopes:
        allow_empty_scopes = False
    else:
        allow_empty_scopes = True
    _scopes = []
    if not allow_empty_scopes:
        if isinstance(scopes, str):
            scopes = scopes.split()

        raw = scopes[0].split('_')

        if len(raw) == 1:
            access_level = ACCESS_ROLES.__len__()
            project = raw[0]
        else:
            project = raw[0]
            access_level = ACCESS_ROLES.get(raw[1])

        if project not in PROJECTS:
            raise NameError(project)

        for role, access in ACCESS_ROLES.items():
            if access <= access_level:
                _scopes.append('{}_{}'.format(project, role))
        _scopes += scopes[1:]
    _scopes = set(_scopes)
    if include_god:
        _scopes = _scopes.union(GOD_SCOPES)

    def wrapper_of_wrapper(f):

        params = signature(f).parameters
        secured_keys = {token_key, scopes_key, token_data_key}.intersection(params.keys())

        @wraps(f)
        def wrapper(*args, **kwargs):

            from flask import request

            token_from_headers = None
            if allow_from_headers:
                token_from_headers = request.headers.get('Authorization', '')
                if token_from_headers.startswith('Bearer '):
                    token_from_headers = token_from_headers[7:]

            t, jwt = getargs(request, token_key, 'jwt')

            token64 = token_from_headers or t or jwt

            if not token64:
                if else_answer:
                    return else_answer
                raise SecurityException(f.__name__, 'No Access Token Presents', error_codes.NO_TOKEN_PRESENTS)
                # return abort(else_answer) if else_answer else else_answer

            token = token64

            token_data = verify(token, base64=expect_base64)
            if not token_data:
                if else_answer:
                    return else_answer
                raise SecurityException(f.__name__, 'Token Not Verified or Expired', error_codes.NOT_VERIFIED_OR_EXPIRED)
                # return abort(else_answer) if else_answer else else_answer

            tscopes = set(token_data.get('scopes', ()))
            if DISABLED.intersection(tscopes):
                if else_answer:
                    return else_answer
                raise SecurityException(f.__name__, 'Disabled Token', error_codes.DISABLED_TOKEN)
                # return abort(else_answer) if else_answer else else_answer

            if not allow_empty_scopes:
                if not _scopes.intersection(tscopes):
                    if else_answer:
                        return else_answer
                    raise SecurityException(f.__name__, 'Forbidden', error_codes.PERMISSION_DENIED)
                    # return abort(else_answer) if else_answer else else_answer

            wrapper._scopes = tscopes
            wrapper._token = token
            wrapper._token_data = token_data

            secured_kwargs = {
                token_key: token,
                token_data_key: token_data,
                scopes_key: tscopes
            }

            secured_kwargs = {
                k: v
                for k, v in secured_kwargs.items() if k in secured_keys
            }

            return f(*args, **kwargs, **secured_kwargs)

        return wrapper

    return wrapper_of_wrapper
