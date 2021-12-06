
from . import error_codes
from .transport import error_codes as transport_errorcodes
from .mobile_app import error_codes as mobile_app_errorcodes
from .advertisement import error_codes as advertisement_errorcodes
from .city import error_codes as city_errorcodes


_ERROR_CODES_MODULES = (error_codes, transport_errorcodes, mobile_app_errorcodes, advertisement_errorcodes, city_errorcodes)


def lookup(code, _cache={}):
    if _cache:
        return _cache.get(code)

    tmp = {}
    for ec in _ERROR_CODES_MODULES:
        for k in (n for n in dir(ec) if n.isupper()):
            tmp[getattr(ec, k)] = k

    _cache.update(tmp)
    # _cache[CODE_DESCRIPTION_NOT_FOUND] = 'CODE_DESCRIPTION_NOT_FOUND'

    return _cache.get(code)


from inobi.utils import http_ok, http_err
from flask_cors import cross_origin


def register_error_code_info(app):

    @app.route('/_errorcodes/<int:code>')
    @cross_origin()
    def app_errorcode_v1(code):
        l = lookup(code)
        if l is None:
            return http_err('Code Not Found', 404, error_code=error_codes.CODE_DESCRIPTION_NOT_FOUND)
        d = dict() if code != error_codes.CODE_DESCRIPTION_NOT_FOUND else dict(lulz='kek')
        return http_ok(code=code, description=lookup(code), **d)
