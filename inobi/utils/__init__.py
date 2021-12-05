
import time
import functools as FT

from flask import jsonify, make_response
import random


def polyline_to_linestring(raw: str, max_length=4000):
    import polyline
    converted = polyline.decode(raw)
    # converted = converted[:100]
    linestring = ','.join('{} {}'.format(round(lat, 4), round(lng, 4)) for lat, lng in converted)
    linestring = 'LINESTRING ({})'.format(linestring)
    return linestring

from PIL import Image
from io import BytesIO
import re
import base64
import binascii


class PictureDecodeError(Exception):
    pass


def picture_from_base64(pic_base64):
    try:
        pic_base64 = re.sub('^data:image/.+;base64', '', pic_base64)
        pic = Image.open(BytesIO(base64.b64decode(pic_base64)))
    except (OSError, binascii.Error, TypeError) as e:
        raise PictureDecodeError(e)
    return pic


def http_ok(data=None, message='OK', status=200, **kwargs):
    if not isinstance(data, dict):
        data = dict(
            status=status,
            message=message
        )
    data.update(kwargs)
    if 'message' not in data:
        data['message'] = message
    if 'status' not in data:
        data['status'] = status

    r = jsonify(data)

    return r, status


def http_err(message='Internal Server Error', status=500, data=None, *, error_code=None, **kwargs):
    if isinstance(data, str):
        data = dict(
            error=message,
            message=data,
            status=status
        )
    elif not isinstance(data, dict):
        data = dict(
            error=message,
            status=status
        )

    if error_code is not None:
        data['error_code'] = error_code

    data.update(kwargs)

    if 'error' not in data:
        data['error'] = message
    if 'status' not in data:
        data['status'] = status

    r = jsonify(data)

    return r, status


def http_ok_data(message='Success', status=200, data: dict = None, **kwargs):
    if not data:
        data = {}
    data.update(dict(data=kwargs))

    if 'message' not in data:
        data['message'] = message
    if 'status' not in data:
        data['status'] = status

    r = jsonify(data)

    return r, status


def http_err_data(message='Internal Server Error', status=500, data: dict = None, error_code=None, **kwargs):
    if not data:
        data = {}
    data.update(dict(data=kwargs))

    if 'error' not in data:
        data['error'] = message
    if 'status' not in data:
        data['status'] = status

    if error_code is not None:
        data['error_code'] = error_code

    r = jsonify(data)

    return r, status


HTTP_OK = http_ok
HTTP_OK_DATA = http_ok_data
HTTP_ERR = http_ok
HTTP_ERR_DATA = http_err_data


import itertools as IT


class requestdict:

    __slots__ = ['args', 'form', 'json', '_raw_json']

    def __init__(self, request):
        self.args = dict(request.args.items())
        self.form = dict(request.form.items())
        self._raw_json = request.get_json(silent=True, force=True)
        self.json = dict(self._raw_json if isinstance(self._raw_json, dict) else {})

    def __getitem__(self, item):
        if item in self.args:
            return self.args[item]
        if item in self.form:
            return self.form[item]
        return self.json[item]

    def __setitem__(self, key, value):
        raise Exception('Can not mutate request args')

    def __repr__(self):
        return '{}(args={}, form={}, json={}, _raw_json={})'.format(requestdict.__name__, self.args, self.form, self.json, self._raw_json)

    def get(self, k, default=None):
        return self.args.get(k, None) or self.form.get(k, None) or self.json.get(k, default)

    def pop(self, k, default=None):
        v = default
        for d in (self.json, self.form, self.args, ):
            # dv = d.pop(k, None)
            # v = v or dv
            if k in d:
                v = d.pop(k)
        return v

    def keys(self):
        return set(IT.chain(self.args.keys(), self.form.keys(), self.json.keys(), ))

    def values(self):
        return IT.chain(self.args.values(), self.form.values(), self.json.values(),)

    def items(self):
        return IT.chain(self.args.items(), self.form.items(), self.json.items(), )

    def __iter__(self):
        yield from self.keys()


def getargs(request, *keys, default_val=None, _rest=False):
    """
    Returns values as tuple from request args if exist else from request.form else from request.json
    :param request:             flask's Request object
    :param keys:                values to search by
    :param default_val:         default value if none was found
    :return:                    tuple of values
    """

    d = requestdict(request)

    t = tuple(d.pop(k, default_val) for k in keys)

    if _rest:
        return t + (d, )

    return t


def generate_key(length):
    from random import SystemRandom
    from string import ascii_letters, digits
    _chs = ascii_letters + digits
    return ''.join(SystemRandom().choice(_chs) for _ in range(length))


from base64 import b64decode as _b64decode


def decode_base64(s):
    k = len(s) % 4
    t64 = s + ('=' * (4 - k))
    return _b64decode(t64)


def timeit(f):
    """Timeit decorator

        Usage:
            @timeit
            def some_view_v1():
                ...

        Prints time in console
        """

    @FT.wraps(f)
    def wrapper(*args, **kwargs):

        ts = time.time()
        r = f(*args, **kwargs)
        interval = time.time() - ts

        print(f.__name__, interval)

        return r

    return wrapper


def flask_timeit(f):
    """Flask view Timeit decorator

       Usage:
           @route('/v1/some/route', methods=('some', 'methods')
           @flask_timeit
           def some_view_v1():
               ...

       Adds 'X-View-Took-Time-To-Proceed' header to view's response,
       that show interval in seconds that view took to evaluate
   """

    @FT.wraps(f)
    def wrapper(*args, **kwargs):

        ts = time.time()
        r = f(*args, **kwargs)
        interval = time.time() - ts

        r = make_response(r)
        r.headers['X-View-Took-Time-To-Proceed'] = interval

        return r

    return wrapper


def logged(file=None, mode='a'):

    from flask import request
    import json

    def wrapper_of_wrapper(f):

        @FT.wraps(f)
        def wrapper(*args, **kwargs):

            get_args = dict(request.args)
            headers = dict(request.headers)
            rjson = dict(request.get_json(silent=True, force=True) or {})

            out = json.dumps(dict(args=get_args, headers=headers, json=rjson, f=dict(name=f.__name__, args=args, kwargs=kwargs)), indent=2, ensure_ascii=False)

            if file is None:
                print('@utils.logged:', f.__name__, 'called', '\n', out)
            else:
                with open(file, ''.join(set(mode).union('b'))) as _f:
                    _f.write('@utils.logged: {} called\n'.format(f.__name__).encode())
                    _f.write(out.encode())
                    _f.write(b'\n')
            try:
                r = f(*args, **kwargs)
            except Exception as e:
                print('@utils.logged:', f.__name__, 'raised', type(e), e)
                raise e
            else:
                print('@utils.logged: {}'.format(f.__name__), 'response: {}'.format(r))
                return r

        return wrapper

    return wrapper_of_wrapper


import typing as T
from flask import Response


_Exc = BaseException


def exception_handled(exc: _Exc, handler: T.Callable[[_Exc], Response]) -> T.Callable[[T.Callable], T.Callable]:
    """Exception handler decorator

    Handles exception of 'exc' type
    and returns what handler returns instead of function return
    by passing exception object as handlers the only argument

    Usage:

        @app.route('/bla/bla/route')
        @exception_handled(SomeException, lambda e: HTTP_ERR(str(e), 400))
        def view_func():
            ...
    """
    def wow(f):
        @FT.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                r = f(*args, **kwargs)
            except exc as e:
                return handler(e)
            else:
                return r
        return wrapper

    return wow


exception_stringified_to_http_err_with_400 = FT.partial(exception_handled, handler=lambda e: http_err(str(e), 400))


from ..config import APP_REGION
import phonenumbers as PN


def validate_phone_number(phone, region=APP_REGION, output_format=PN.PhoneNumberFormat.E164) -> T.Optional[str]:
    if not isinstance(phone, str):
        return None
    try:
        n = PN.parse(phone, region=region)
    except PN.NumberParseException:
        return None
    else:
        if PN.is_valid_number(n):
            return PN.format_number(n, output_format)
        return None


class listofnamedtuples(list):

    def itemsasdict(self):
        return [i._asdict() for i in self]


def ntrow(*args, **kwargs):
    """Namedtuple class with json fields decorator

    After decorated class has `make` class method
        and `asrow` property method;

    Usage:
        @ntrow
        class Some(namedtuple('Some', 'f1 f2 f3 json payload')):
            _json_fields = ('json', 'payload')

        some = Some.make((1, 2, 3, 'null', '{"kek": true}'))

        assert some == (1, 2, 3, None, {'kek': True})

        # convert back to row
        row = some.asrow

        assert row == (1, 2, 3, 'null', '{"kek": true}')
    """

    def wrapper(cls: T.NamedTuple):

        json_fields = kwargs.get('json_fields')
        make_optional = kwargs.get('make_optional', False)

        import json

        cls_json_fields = getattr(cls, '_json_fields', None)
        assert cls_json_fields is None or json_fields is None, 'Pass json_fields keyword argument to decorator or set _json_fields arguments as class attributes in {}'.format(cls)

        _json_fields = tuple(cls_json_fields or json_fields or ())

        def make(cls, row: T.Iterable, start_index=0) -> cls:
            data = row[start_index:start_index + len(cls._fields)]
            if make_optional and (len(data) != len(cls._fields) or data.count(None) == len(cls._fields)):
                return None
            o = cls._make(data)
            return o._replace(**{
                f: json.loads(v)
                for f, v in map(lambda k: (k, getattr(o, k)), _json_fields) if isinstance(v, str)
            })

        def asrow(self):
            return self._replace(**{
                f: json.dumps(v)
                for f, v in map(lambda k: (k, getattr(self, k)), _json_fields)
            })

        cls.make = classmethod(make)
        cls.asrow = property(asrow)

        return cls

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return wrapper(args[0])

    return wrapper


from inobi.config import SQL_CONNECTION as _inobi_sql_connection_string
import psycopg2
from psycopg2.extensions import connection as _pg_connection


def connected(*args, **kwargs):
    conn_key = kwargs.get('conn_key', 'conn')
    sql_connection_string = kwargs.get('sql_connection_string', _inobi_sql_connection_string)

    def wow(f):
        @FT.wraps(f)
        def wrapper(*fargs, **fkwargs):
            conn = fkwargs.get('conn', None)
            if conn is None:
                conn = next(filter(lambda a: isinstance(a, _pg_connection), args), None)
            if conn is None:
                with psycopg2.connect(sql_connection_string) as conn:
                    return f(*fargs, **fkwargs, **{conn_key: conn})
            return f(*fargs, **fkwargs)

        return wrapper

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return wow(args[0])

    return wow


from datetime import timedelta


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from os.path import basename
import typing as T


def send_email(to_address: T.Union[str, list], subject: str, message: str,
               username, password, smtp, from_address=None, files: list = ()):

    # if from_address is None:
        # from_address = username
    from_address = username

    # msg = MIMEText(message)
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address if type(to_address) == str else ', '.join(to_address)
    msg['Subject'] = subject
    msg.attach(MIMEText(message))
    if files:
        for f in files or []:
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(f)
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(f))
            msg.attach(part)

    server = smtplib.SMTP_SSL(smtp)
    o = server.ehlo()
    # print(o)
    # print(o)
    server.login(username, password)
    # print(o)
    o = server.send_message(msg)
    # print(o)
    o = server.quit()
    # print(o)

import os
import hashlib


def get_md5(file_path):
    if not os.path.exists(file_path):
        return None
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        md5.update(f.read())
        return md5.hexdigest()


def wav_converter(source, destination):
    cmd = 'sox {source} -r 22050 -c 1 -b 16 --endian little -e signed-integer {destination}'.format(source=source,
                                                                                                    destination=destination)
    os.system(cmd)


def device_description_from_user_agent(ua: str) -> str:
    if isinstance(ua, str) and '(' in ua and ')' in ua:
        _obi = ua.index('(')+1
        try:
            _cbi = ua.index(')', _obi)
            return ua[_obi:_cbi]
        except ValueError:
            pass
    return ua


def _key_value_from(v: str) -> T.Tuple[str, str]:

    for s, t in (('->', 'r'), ('<-', '-'), (':', 'r'), ('>', 'r'), ('<', '-'), ('-', 'r'), ):
        if s in v:
            a, b = v.split(s)
            if type == 'r':
                return b, a
            return a, b

    return v, v


def _mapper_dict_from_fields(value: T.Union[T.Iterable[str], T.Dict[str, str]], default=None, default_factory=dict) -> T.Dict[str, str]:
    if not value:
        return default_factory() if default_factory else default
    if not isinstance(value, dict):
        value = dict(_key_value_from(f) for f in value)
    return value


class AsDictMixin:

    _asdict_fields = ()              # type: T.Union[T.Iterable[str], T.Dict[str, str]]
    """dict or iterable

    Example:
        a) as dict
        _asdict_fields = {'user': 'name', 'id': 'id', 'phone': 'contact'}
        .asdict() -> dict:
            {
                'user': self.name,
                'id': self.id,
                'phone': self.contact
            }

        b) as iterable
        _asdict_fields = 'id name phone registered'.split()  # type: list
        .asdict() -> dict:
            {
                'id': self.id,
                'name': self.name,
                'phone': self.phone,
                'registered': self.registered
            }

        c) as instructions iterable
        _asdict_fields = 'id user:name phone>contact registered'.split()  # type: list
        .asdict() -> dict:
            {
                'user': self.name,
                'id': self.id,
                'phone': self.contact
            }
    """

    def asdict(self) -> dict:
        fs = _mapper_dict_from_fields(self._asdict_fields)
        return {
            target_key: getattr(self, source_key)
            for source_key, target_key in fs.items()
        }


import datetime


base_undicitifiable_types = (int, bool, type(None), str, float, datetime.datetime, datetime.date, datetime.time)


def recursive_dictify(v, depth=None, base_types=base_undicitifiable_types, _d=0):
    if depth is not None and _d > depth:
        return v
    if isinstance(v, AsDictMixin):
        return recursive_dictify(v.asdict(), depth=depth, _d=_d + 1)
    elif isinstance(v, (list, tuple)):
        return [recursive_dictify(i, depth=depth, _d=_d + 1) for i in v]
    elif isinstance(v, dict):
        return {
            k: recursive_dictify(i, _d=_d + 1, depth=depth)
            for k, i in v.items()
        }
    elif isinstance(v, base_types):
        return v
    else:
        raise TypeError(v)


from sqlalchemy import types, String, JSON, cast, Column, Float


class LocatedMixin:

    lat = Column(Float(precision=15), nullable=True)
    lng = Column(Float(precision=15), nullable=True)

    @property
    def location(self) -> T.Optional[dict]:
        if self.lat is not None and self.lng is not None:
            return dict(lat=self.lat, lng=self.lng)

    @location.setter
    def location(self, value):
        if isinstance(value, dict) and len(value) >= 2 and all(isinstance(value.get(k), (int, float)) for k in ('lat', 'lng')):
            self.lat, self.lng = value['lat'], value['lng']
        elif value is None:
            self.lat, self.lng = None, None
        elif isinstance(value, (tuple, list)) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
            self.lat, self.lng = value
        else:
            raise ValueError(value)
        print(value)
        print(self.lat, self.lng)


class UpdateMixin:

    _update_fields = ()                 # type: T.Union[T.Iterable[str], T.Dict[str, str]]

    def update(self, values: dict, **kwargs) -> bool:
        fs = _mapper_dict_from_fields(self._update_fields)

        updated = False

        for input_field_key, target_field_key in fs.items():
            if input_field_key in values:
                setattr(self, target_field_key, values[input_field_key])
                updated = True

        for k, v in kwargs.items():
            setattr(self, k, v)

        return updated


def with_request_as_argument(*args):

    name = 'request'
    if len(args) == 1 and isinstance(args[0], str):
        (name, ) = args

    def wow(f):

        @FT.wraps(f)
        def wrapper(*args, **kwargs):

            from flask import request

            return f(*args, **{**kwargs, name: request})

        return wrapper

    if len(args) == 1 and callable(args[0]):
        return wow(args[0])
    else:
        return wow

