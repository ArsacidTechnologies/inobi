
import attr

import datetime as dt
import collections as C


class Message(C.namedtuple('Message', 'id register_time issuer service type to content')):

    @classmethod
    def from_view(cls, iss, type, content, service=None, to=None):
        return cls(None, None, iss, service, type, to, content)

    def print(self):
        print("""From: {issuer}
Service: {service}
Type: {type}
To: {to}

{content}
""".format(**self._asdict()))

    @property
    def time(self):
        return dt.datetime.fromtimestamp(self.register_time)
