
from functools import wraps
from inspect import signature, Parameter
from typing import *

from flask import request, jsonify, make_response, abort as _abort
from validate_email import validate_email

from .. import getargs, validate_phone_number


tag = "@{}:".format(__name__)


_empty = Parameter.empty
Numeric = Union[int, float, complex]


def dualwrap(dec: Callable):
    """
    Wraps decorator to make it callable with or without arguments

    Example:
        @dualwrap
        def decorator(f, arg1='kek', arg2=123):
            # something
            ...

        @decorator
        def decorated(some, another):
            ...

        @decorator(arg1='lel', arg2=321):
        def decorated2():
            ...

    Warning: this forces function to have wrapped function as its first argument,
             thereby change its signtures, which then (will!) can confuse its users

    """

    @wraps(dec)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return dec(args[0])
        else:
            return lambda func: dec(func, *args, **kwargs)

    return new_dec


def abort(status, msg='Bad request', **kwargs):
    data = {
        'status': status,
        'message': msg,
        **kwargs
    }
    return _abort(make_response(jsonify(data), status))


def _type_converter(_type, value, default=None):
    if _type is _empty:
        return value if value is not None else default
    if hasattr(_type, '__union_params__'):
        if type(value) in _type.__union_params__:
            return value
        for _t in _type.__union_params__:
            try:
                return _t(value)
            except:
                pass
        return default
    else:
        # almost all objects are string convertible, so str is special case
        if _type is str and not isinstance(value, str):
            return default
        # classes are callable, checking if it is a type, but not function
        if type(_type) == type:
            if isinstance(value, _type):
                return value
            else:
                try:
                    return _type(value)
                except:
                    return default
        # converter function
        elif callable(_type):
            try:
                return _type(value)
            except:
                return default
        # todo: wtf! revise!
        else:
            raise Exception('Unknown case')


def converted(*dec_args, **dec_kwargs):

    verbose = dec_kwargs.pop('verbose', False)

    rest_key = dec_kwargs.pop('rest_key', None)

    exclude_keys = dec_kwargs.pop('exclude', [])
    exclude_keys.append(rest_key)

    assert isinstance(rest_key, str) or rest_key is None, "rest_key parameter must be string"

    silent = dec_kwargs.pop('silent', False)            # type: bool
    reject_code = dec_kwargs.pop('reject_code', 400)    # type: int

    descriptions_for_keys = {}
    for k, v in dec_kwargs.items():
        if k.startswith('description_for__'):
            descriptions_for_keys[k[17:]] = v

    def wow(f):  # Wrapper Of Wrapper

        params = signature(f).parameters  # type: Dict[str, Parameter]

        __kwargs_key = None
        for k, v in params.items():

            if v.kind == Parameter.VAR_KEYWORD:
                __kwargs_key = k
                exclude_keys.append(k)
            elif v.kind == Parameter.POSITIONAL_ONLY:
                exclude_keys.append(k)

        if rest_key:
            assert rest_key in params, 'Rest Key given, but no keyword argument in view function'

        @wraps(f)
        def wrapper(*flask_args, **flask_kwargs):

            *rargs, rest = getargs(request, *params.keys(), _rest=True)

            __kwargs = rest

            view_kwargs = {}
            for value, param in zip(rargs, params.values()):
                pname = param.name
                arg = None

                if pname in exclude_keys:
                    continue

                if pname in flask_kwargs:
                    arg = flask_kwargs[pname]
                elif value is None:
                    if (not silent) and param.default is _empty:
                        return abort(reject_code, "'{}' Parameter Required".format(pname))
                    arg = param.default
                else:
                    if param.annotation is not _empty:

                        # todo: case when annotation is string

                        arg = _type_converter(_type=param.annotation, value=value)
                        if arg is None:
                            if param.default is _empty and not silent:
                                desc = "'{}' Parameter's Type Required To Be {}".format(
                                    pname,
                                    descriptions_for_keys.get(pname) or Modifier.description_for(param.annotation) or param.annotation
                                )
                                return abort(
                                    reject_code,
                                    desc,
                                    given=dict(name=pname, value=value, type=repr(type(value))),
                                )
                            arg = param.default
                    # todo: revise case later
                    # elif param.default is not _empty:
                    #     arg = _type_converter(type(param.default), value)
                    #     arg = ...
                    else:
                        arg = value

                # print(tag, pname, arg, value)

                view_kwargs[pname] = arg

            if rest_key:
                f_res = f(*flask_args, **{**view_kwargs, rest_key: __kwargs})
            elif __kwargs_key:
                f_res = f(*flask_args, **{**view_kwargs, **__kwargs})
            else:
                f_res = f(*flask_args, **view_kwargs)

            return f_res

        return wrapper

    if len(dec_args) == 1 and len(dec_kwargs) == 0 and callable(dec_args[0]):
        return wow(dec_args[0])
    else:
        return wow


from datetime import datetime, timezone
from dateutil import parser


class Modifier:

    @staticmethod
    def convert_bool(arg) -> Optional[bool]:
        """A Boolean"""
        if isinstance(arg, bool):
            return arg
        if isinstance(arg, str):
            al = arg.lower()
            if al in {'false', 'f', 'off', 'no', 'n', '0', 'none', }:
                return False
            if al in {'true', 't', 'on', 'yes', 'y', '1', 'ok'}:
                return True

        return None

    BOOL = convert_bool

    @staticmethod
    def generate_collection(*values):
        set_of_values = set(values)

        def converter(x):
            if x in set_of_values:
                return x
            else:
                raise Exception('{} is not in collection'.format(x))

        converter.__doc__ = "A One of ({}) Values".format(', '.join(map(repr, set_of_values)))
        return converter

    COLLECTION = generate_collection

    @staticmethod
    def string_with_minimumlength(length: int):
        def converter(x):
            if isinstance(x, str) and len(x) >= length:
                return x
            raise Exception('{} is not {}-length string'.format(x, length))

        converter.__doc__ = "A String With At Least {} Characters".format(length)
        return converter

    MINIMUM_SIZED_STRING = string_with_minimumlength

    @staticmethod
    def email(x):
        """A Valid Email Address"""
        if isinstance(x, str):
            return x if validate_email(x) else None
        return None

    EMAIL = email

    @staticmethod
    def description_for(f) -> Optional[str]:
        if callable(f):
            return getattr(f, '__doc__', None)
        return None

    @staticmethod
    def phone(x):
        """A Valid Phone Number"""
        return validate_phone_number(x)

    PHONE = phone

    @staticmethod
    def arrayof(*types):
        set_of_types = set(types)

        def converter(x):
            if not isinstance(x, (list, tuple)):
                raise Exception('Argument Is Not Iterable')

            for i in x:
                if type(i) not in set_of_types:
                    raise Exception("Element ({}) Is Not Type Of {}".format(i, set_of_types))
            return x

        converter.__doc__ = 'A List Of Elements Of {} Types'.format(set_of_types)
        return converter

    ARRAY_OF = arrayof

    @staticmethod
    def datetime(x) -> datetime:
        """An ISO 8601 format datetime string"""
        try:
            return parser.parse(x)
        except (ValueError, TypeError):
            pass

        try:
            return datetime.fromtimestamp(float(x), tz=timezone.utc)
        except ValueError:
            raise Exception('Argument misunderstood')

    DATETIME = datetime

    @staticmethod
    def union_of(*types):
        set_of_types = set(types)

        def converter(x):
            if type(x) not in set_of_types:
                raise Exception("Element Is Type Of {}".format(set_of_types))
            return x

        converter.__doc__ = 'Element Of {} Type'.format(set_of_types)
        return converter

    UNION = union_of



# @dualwrap
# def converted(f: Callable, silent=False, reject_code=400):
#
#     params = signature(f).parameters    # type: Dict[str, Parameter]
#
#     @wraps(f)
#     def wrapper(*flask_args, **flask_kwargs):
#
#         rargs = getargs(request, *params.keys())
#
#         view_kwargs = {}
#         for value, param in zip(rargs, params.values()):
#             pname = param.name
#             arg = None
#
#             if pname in flask_kwargs:
#                 arg = flask_kwargs[pname]
#             elif value is None:
#                 if (not silent) and param.default is _empty:
#                     return abort(reject_code, "'{}' Parameter Required".format(pname))
#                 arg = param.default
#             else:
#                 if param.annotation is not _empty:
#
#                     # todo: case when annotation is string
#
#                     arg = _type_converter(_type=param.annotation, value=value)
#                     if arg is None:
#                         if param.default is _empty and not silent:
#                             return abort(
#                                 reject_code,
#                                 "'{}' Parameter's Type Required To Be {}".format(pname, param.annotation),
#                                 given=dict(name=pname, value=value, type=repr(type(value))),
#                             )
#                         arg = param.default
#                 # todo: revise case later
#                 # elif param.default is not _empty:
#                 #     arg = _type_converter(type(param.default), value)
#                 #     arg = ...
#                 else:
#                     arg = value
#
#             # print(tag, pname, arg, value)
#
#             view_kwargs[pname] = arg
#
#         return f(*flask_args, **view_kwargs)
#
#     return wrapper
