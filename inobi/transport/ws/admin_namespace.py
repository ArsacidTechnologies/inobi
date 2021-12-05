from flask_socketio import Namespace
from inobi.security import secured
from flask import request, session
from ..ws import logger
from inobi.transport.DataBase.line_v2 import get_transport_organization_lines
from inobi.transport.configs import Room
from flask_socketio import join_room


class AdminNamespace(Namespace):
    _conns = set()

    @secured('transport_viewer', else_answer=False)
    def on_connect(self, token_data):
        organization = token_data.get('transport_organization')
        if not organization:
            return False
        organization_id = organization.get('id')
        if not organization_id:
            return False
        session['organization_id'] = organization_id
        organization_lines = get_transport_organization_lines(organization_id)
        organization_lines = set(organization_lines)

        join_room(Room.notification(organization_id))

        session['lines'] = organization_lines
        logger.info('WS CONNECT {}'.format(self.__class__.__name__))
        return True

    def on_disconnect(self):
        logger.info('WS DISCONN {}'.format(self.__class__.__name__))
        return None

    def __enter_room(self, room):
        if isinstance(room, int):
            if room in session['lines']:
                self.enter_room(request.sid, room)
        elif isinstance(room, str):
            if room.lower() == 'all':
                self.enter_room(request.sid, Room.organization_subscribe(session['organization_id']))

    def __leave_room(self, room):
        if isinstance(room, str):
            if room.lower() == 'all':
                self.leave_room(request.sid, Room.organization_subscribe(session['organization_id']))
        else:
            self.leave_room(request.sid, room)

    def on_join(self, *args):
        for room in args:
            if isinstance(room, (list, tuple)):
                for subroom in room:
                    self.__enter_room(subroom)
            else:
                self.__enter_room(room)
        self.emit('join', {'status': 200, 'message': 'successfully joined', 'room': args}, room=request.sid)
        return {'status': 200, 'message': 'successfully joined', 'room': args}

    def on_leave(self, *args):
        for room in args:
            if isinstance(room, (list, tuple)):
                for subroom in room:
                    self.__leave_room(subroom)
            else:
                self.__leave_room(room)
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