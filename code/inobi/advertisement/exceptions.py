

class InobiAdsException(Exception):
    pass


InobiException = InobiAdsException


from inobi.exceptions import BaseInobiException


class AdvertisementBaseException(BaseInobiException):
    pass


from .error_codes import UNKNOWN


class AdvertisementException(AdvertisementBaseException):

    def __init__(self, msg, code=None, http_code=None):
        super().__init__(msg, code or UNKNOWN, http_code=http_code)


class InvalidInputException(AdvertisementException):
    pass
