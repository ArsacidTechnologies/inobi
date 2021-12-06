
import typing as T
import datetime
import logging

import pytz
import requests

from .. import config


logger = logging.getLogger(__name__)

RequestId = str


class Shahkar:

    def __init__(self, phone_number, national_code):
        self.phone_number = phone_number
        self.national_code = national_code
        self._registration_request_id = None
        self._closed = False

    def __str__(self):
        return '{},{},{}'.format(self.phone_number, self.national_code, self._registration_request_id)

    @staticmethod
    def _request_id():
        return datetime.datetime.utcnow() \
            .replace(tzinfo=pytz.UTC) \
            .astimezone(pytz.timezone('Asia/Tehran')) \
            .strftime('0130%Y%m%d%H%M%S%f')  # magic

    def check(self, *args, **kwargs) -> bool:
        if config.SHAHKAR_DEBUG:
            return True

        if not self.phone_number or self.phone_number.strip() == "":
            self.phone_number = kwargs.get("phone_number")

        if not self.national_code or self.national_code.strip() == "":
            self.national_code = kwargs.get("national_code")

        data = {
            "requestId": self._request_id(),
            "serviceNumber": self.phone_number.replace("+98", "0"),
            "serviceType": 2,
            "identificationType": 0,
            "identificationNo": self.national_code,
        }

        try:
            response = requests.post(
                config.SHAHKAR_HOST + config.SHAHKAR_ID_MATCHING_API,
                timeout=8,
                headers={"content-type": "application/json"},
                json=data,
            )
            response.raise_for_status()
            j = response.json()
            logger.debug('%r.check() -> %r', self, j)

            if j["response"] is not None:
                if j["response"] == 200:
                    return True
                else:
                    return False
            else:
                return False

        except requests.exceptions.RequestException:
            return False

    def register(self, *args, _close=False, **kwargs) -> T.Optional[RequestId]:
        if config.SHAHKAR_DEBUG:
            return None

        if not self.phone_number or self.phone_number.strip() == "":
            self.phone_number = kwargs.get("phone_number")

        if not self.national_code or self.national_code.strip() == "":
            self.national_code = kwargs.get("national_code")

        data = {
            "requestId": self._request_id(),
            "mobileNumber": self.phone_number.replace("+98", "0"),
            "identificationType": 0,
            "identificationNo": self.national_code,
        }

        try:
            response = requests.post(
                config.SHAHKAR_HOST + config.SHAHKAR_WIFIMOBILE_API,
                timeout=8,
                headers={"content-type": "application/json"},
                json=data,
            )
            response.raise_for_status()
            j = response.json()
            logger.debug('%r.register() -> %r', self, j)

            if j["response"] is not None:
                if j["response"] == 200:
                    self._registration_request_id = j['id']

                    if _close:
                        if not self.close():
                            logger.warning('CLOSING FAILED: %r.register()', self)
                    return self._registration_request_id
                else:
                    return None
            else:
                return None

        except requests.exceptions.RequestException as e:  # This is the correct syntax
            return None

    def close(self, *args, id: RequestId = None, **kwargs) -> bool:
        registration_request_id = id or self._registration_request_id

        if config.SHAHKAR_DEBUG:
            return False

        if not self.phone_number or self.phone_number.strip() == "":
            self.phone_number = kwargs.get("phone_number")

        if not self.national_code or self.national_code.strip() == "":
            self.national_code = kwargs.get("national_code")

        data = {
            "requestId": self._request_id(),
            "serviceNumber": self.phone_number.replace("+98", "0"),
            "id": registration_request_id,
        }

        try:
            response = requests.post(
                config.SHAHKAR_HOST + config.SHAHKAR_WIFIMOBILE_CLOSE_API,
                timeout=8,
                headers={"content-type": "application/json"},
                json=data,
            )
            response.raise_for_status()
            j = response.json()
            logger.debug('%r.close() -> %r', self, j)

            if j["response"] is not None:
                if j["response"] == 200:
                    self._closed = True
                    return True
                else:
                    return False
            else:
                return False

        except requests.exceptions.RequestException as e:  # This is the correct syntax
            return False
