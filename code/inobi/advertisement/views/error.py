
from inobi import app
from inobi.utils import http_err
from ..utils import debug_exception

tag = '@views.error:'


STATUS_500 = 500
STATUS_NOT_FOUND = 404
STATUS_UNAUTHORIZED = 401
STATUS_BAD_REQUEST = 400
STATUS_TOO_MANY_REQUESTS = 429


@app.errorhandler(STATUS_500)
def internal_error(e):
    debug_exception(tag, e, to_file=True)
    return http_err(status=STATUS_500)


@app.errorhandler(STATUS_NOT_FOUND)
def not_found(e):
    # debug_exception(tag, e, to_file=True)
    return http_err(message='Not Found', status=STATUS_NOT_FOUND)


@app.errorhandler(STATUS_BAD_REQUEST)
def bad_request(e):
    debug_exception(tag, e, to_file=True)
    return http_err(message='Bad Request', status=STATUS_BAD_REQUEST)


@app.errorhandler(STATUS_UNAUTHORIZED)
def unauthorized(e):
    # debug_exception(tag, e, to_file=True)
    return http_err(message='Unauthorized', status=STATUS_UNAUTHORIZED)


@app.errorhandler(STATUS_TOO_MANY_REQUESTS)
def too_many_requests(e):
    debug_exception(tag, e, to_file=True)
    return http_err(message='Too Many Requests', status=STATUS_TOO_MANY_REQUESTS)
