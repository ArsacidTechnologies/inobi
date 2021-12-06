from flask_socketio import Namespace
from inobi.security import secured
from flask import request
from ..ws import logger


class BaseNamespace(Namespace):
    _conns = set()

    @secured(else_answer=False)
    def on_connect(self):
        logger.info('WS CONNECT {}'.format(self.__class__.__name__))
        return True

    def on_disconnect(self):
        logger.info('WS DISCONN {}'.format(self.__class__.__name__))
        return None

    def on_join(self, *args):
        for room in args:
            if isinstance(room, (list, tuple)):
                for subroom in room:
                    self.enter_room(request.sid, subroom)
            else:
                self.enter_room(request.sid, room)
        self.emit('join', {'status': 200, 'message': 'successfully joined', 'room': args}, room=request.sid)
        return {'status': 200, 'message': 'successfully joined', 'room': args}

    def on_leave(self, *args):
        for room in args:
            if isinstance(room, (list, tuple)):
                for subroom in room:
                    self.leave_room(request.sid, subroom)
            else:
                self.leave_room(request.sid, room)
        self.emit('leave', {'status': 200, 'message': 'successfully leaved', 'room': args}, room=request.sid)
        return {'status': 200, 'message': 'successfully leaved', 'room': args}

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



