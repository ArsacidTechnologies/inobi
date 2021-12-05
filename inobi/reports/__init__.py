

from flask import Blueprint
from inobi.reports.config import NAME

bp = Blueprint(NAME, __name__)
route = bp.route

from . import views