


import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # filename=LOGS_DIRECTORY + 'transport.log',
                    level=logging.INFO)

from inobi import add_prerun_hook
from inobi.transport.configs import traccar_dbpath
from flask import Blueprint


transport_middlewares = []


def append_transport_md(c):
    transport_middlewares.append(c)


transport_bp = Blueprint('Transport', __name__)
route = transport_bp.route


from inobi.utils.project_initializer import database
from .traccar_md.run import sync_traccar_md

tag = "@{}: ".format(__name__)

from .configs import TRACCAR_SYNC_ACTIVE


def migration():
    database.initialize_for_module(name=__name__, execute=['00_utils.sql',
                                                           '01_lines.sql',
                                                           '02_transports.sql',
                                                           'bus_info.sql',
                                                           '03_transport_organizations.sql',
                                                           '04_views.sql'])
migration.is_migration = True


def traccar_hook():
    import os
    exists = os.path.isfile(traccar_dbpath)
    if exists:
        os.remove(traccar_dbpath)
    if TRACCAR_SYNC_ACTIVE:
        # from threading import Thread
        # Thread(target=traccar_sync).start()
        from .configs import traccar_force_update_line, traccar_region, traccar_url
        try:
            logger.info("STARTING INITIALIZATION OF TRACCAR MIDDLEWARE")
            logger.info("traccar url {}".format(traccar_url))
            logger.warning("WARNING traccar syncing for {} region".format(traccar_region))
            logger.warning("WARNING traccar force update line is {}".format(traccar_force_update_line))
            sync_traccar_md(traccar_force_update_line)
            logger.info("TRACCAR INITIALIZATION COMPLETED")
        except Exception as e:
            # logger.exception(str(e))
            logger.info("TRACCAR INITIALIZATION FAILED")
            raise


add_prerun_hook(migration)
add_prerun_hook(traccar_hook)


# SOCKET IO INIT #
###########################################################
from inobi import socketio
from inobi.transport.ws import AdminNamespace, TransportNamespace, BaseNamespace, DriverNamespace, TransportV2Namespace
from inobi.transport.configs import WS_ADMIN_NAMESPACE, WS_TRANSPORT_NAMESPACE, WS_BASE_NAMESPACE, WS_DRIVER_NAMESPACE, \
    WS_TRANSPORT_V2_NAMESPACE

admin_namespace = AdminNamespace(WS_ADMIN_NAMESPACE)
transport_namespace = TransportNamespace(WS_TRANSPORT_NAMESPACE)
base_namespace = BaseNamespace(WS_BASE_NAMESPACE)
driver_namespace = DriverNamespace(WS_DRIVER_NAMESPACE)
transport_v2_namespace = TransportV2Namespace(WS_TRANSPORT_V2_NAMESPACE)

socketio.on_namespace(base_namespace)
socketio.on_namespace(transport_namespace)
socketio.on_namespace(driver_namespace)
socketio.on_namespace(admin_namespace)
socketio.on_namespace(transport_v2_namespace)


from inobi.security import SecurityException


@socketio.on_error_default
def default_error_handler(e):
    if isinstance(e, SecurityException):
        return False
    logger.exception("SocketIO default {}: {}".format(type(e), e))

#############################################################

from .views import *
from . import DataBase


if TRACCAR_SYNC_ACTIVE:
    from .traccar_md import TraccarMiddleware
    traccar_md = TraccarMiddleware()
    append_transport_md(traccar_md)

