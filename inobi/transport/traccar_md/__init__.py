import logging
logger = logging.getLogger(__name__)
from inobi.middleWare import TransportMiddleware
from .requests import save_device, delete_device, update_device
from .db import get_group_by_line, save_transport, get_device_by_transport
from inobi.transport import traccar_dbpath
import sqlite3
from inobi.transport.configs import TRACCAR_SQL_CONNECTION, TRACCAR_SYNC_ACTIVE
import psycopg2
from inobi.utils.project_initializer import database
from inobi import add_prerun_hook


def before_init():
    with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
        database.initialize_for_module(name=__name__, db_connection=conn)


before_init.is_migration = True

if TRACCAR_SYNC_ACTIVE:
    add_prerun_hook(before_init)


class TraccarMiddleware(TransportMiddleware):
    def get_name(self):
        return self.__class__.__name__

    def on_saved(self, bus):
        # from ..configs import traccar_region
        # with sqlite3.connect(traccar_dbpath) as conn:
        #     group_id = get_group_by_line(conn, bus['line_id'])
        #     if bus.get('payload'):
        #         attrs = bus.get('payload')
        #         attrs.update(dict(region=traccar_region))
        #     else:
        #         attrs = dict(region=traccar_region)
        device = save_device(name=bus.get('name') or bus['device_id'],
                             unique_id=bus['device_id'],

                                 )
        # save_transport(conn, bus['id'], device['id'])
        return device

    def on_deleted(self, id):
        with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
            sql = 'select id from devices where uniqueId = %s'
            cursor = conn.cursor()
            cursor.execute(sql, (bus['device_id'],))
            DeviceId = cursor.fetchone()[0]
        # with sqlite3.connect(traccar_dbpath) as conn:
        #     device_id = get_device_by_transport(conn, id)
        deleted = delete_device(device_id)
        return deleted

    def on_updated(self, bus):
        # from ..configs import traccar_region
        with psycopg2.connect(TRACCAR_SQL_CONNECTION) as conn:
            sql = 'select id from devices where uniqueId = %s'
            cursor = conn.cursor()
            cursor.execute(sql, (bus['device_id'],))
            DeviceId = cursor.fetchone()[0]
        #     group_id = get_group_by_line(conn, bus['line_id'])
        #     if bus.get('payload'):
        #         attrs = bus.get('payload', {})
        #         attrs.update(dict(region=traccar_region))
        #     else:
        #         attrs = dict(region=traccar_region)
        device = update_device(id=DeviceId, name=bus.get('name'),
                             unique_id=bus['device_id'])
        return device