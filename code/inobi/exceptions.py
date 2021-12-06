

class BaseInobiException(Exception):

    __slots__ = ['msg', 'code', 'http_code']

    def __init__(self, msg, code, http_code=None):
        self.msg = msg
        self.code = code
        self.http_code = http_code

    def __str__(self):
        return self.msg


from inobi.utils import http_err
from flask_cors import cross_origin


def register_error_handlers(app):

    @app.errorhandler(BaseInobiException)
    @cross_origin()
    def base_inobi_exception_handler(e: BaseInobiException):
        return http_err(message=e.msg,
                        status=(e.http_code or 400),
                        error_code=e.code)

    from inobi.security import SecurityException

    @app.errorhandler(SecurityException)
    @cross_origin()
    def on_security_error(e: SecurityException):
        view, reason, error_code = e.view, e.reason, e.error_code
        return http_err('Unauthorized', 401, reason, error_code=error_code)

    from marshmallow import ValidationError

    @app.errorhandler(ValidationError)
    @cross_origin()
    def on_validation_error(e: ValidationError):
        return http_err('Bad Request', 400, e.messages)

    # from inobi.auth import BaseAuthException
    #
    # @app.errorhandler(BaseAuthException)
    # @cross_origin()
    # def on_auth_exception_handler(e: BaseAuthException):
    #     return http_err(message=e.msg,
    #                     status=(e.http_code or 400),
    #                     error_code=e.code)
