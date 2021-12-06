from flask.blueprints import Blueprint
from .config import NAME, API_KEY
from .iauth import Auth
from . import error_codes as ec


bp = Blueprint(NAME, __name__)

route = bp.route

from .iauth.exceptions import BaseCommunicationException as BaseAuthException
