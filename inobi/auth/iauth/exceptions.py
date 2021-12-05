from inobi.auth import error_codes as ec


class BaseCommunicationException(Exception):
    code = ec.SERVER_ERROR
    msg = None
    http_code = 500

    def __init__(self, code=code, msg=msg, http_code=http_code):
        self.code = code
        self.msg = msg
        self.http_code = http_code

    def __str__(self):
        return self.msg


class UnknownError(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'unknown error'
    http_code = 500


class PermissionDenied(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'server is unauthorized with auth server'
    status_code = 500


class TokenExpired(BaseCommunicationException):
    code = ec.TOKEN_EXPIRED
    msg = 'token expired'
    status_code = 401


class InvalidStructure(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'invalid structure'
    status_code = 500


class NotJSONException(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'not json'
    status_code = 500


class NotSavedException(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'not saved, try again'
    status_code = 500


class NotFoundException(BaseCommunicationException):
    code = ec.AUTHENTICATION_FAILED
    msg = 'not found'
    status_code = 401


class InternalServerError(BaseCommunicationException):
    code = ec.SERVER_ERROR
    msg = 'internal server error'
    status_code = 500


class LoginRequiredException(BaseCommunicationException):
    code = ec.RE_LOGIN_REQUIRED
    msg = 're login required'
    status_code = 401


def get_exception(code):
    return {
        0: UnknownError,
        2: PermissionDenied,
        3: TokenExpired,
        4: InvalidStructure,
        5: NotJSONException,
        6: NotSavedException,
        7: NotFoundException,
        8: LoginRequiredException
    }.get(code, UnknownError)
