from flask import Blueprint
from inobi.network.config import NAME


from inobi.network.redis_list import RedisList
# import inobi.network.scheduler


bp = Blueprint(NAME, __name__)
route = bp.route


from . import views
