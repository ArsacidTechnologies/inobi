from flask_socketio import Namespace
from inobi.security import secured
from flask import request
from ..ws import logger


class DriverNamespace(Namespace):
    _conns = set()

    @secured('transport_viewer transport_driver', else_answer=False)
    def on_connect(self, token_data):
        transport = token_data.get('transport')
        if not transport:
            return False
        line_id = transport.get('line_id')
        if not line_id:
            return False
        self.enter_room(request.sid, line_id)
        logger.info('WS CONNECT {}'.format(self.__class__.__name__))
        return True

    def on_disconnect(self):
        logger.info('WS DISCONN {}'.format(self.__class__.__name__))
        return None

    def on_status(self, *args):
        if (request.sid, request.namespace) in self._conns:
            self._conns.remove((request.sid, request.namespace))

    def set_conn(self, conn, namespace):
        self._conns.add((conn, namespace))

    def del_crack_conns(self):
        arr = list(self._conns)
        for sid, namespace in self._conns:

            self.disconnect(sid, namespace)
        self._conns.clear()
        return arr



