
import json

from flask import request
from flask_socketio import Namespace, emit, send, join_room

from inobi.security import secured, scope
from inobi.utils.converter import converted, Modifier
from inobi.utils import getargs


class DebugNamespace(Namespace):

    def __str__(self):
        return 'DebugNamespace<{!r}>'.format(self.namespace)

    @secured([scope.Transport.ADMIN, scope.Transport.BOX, scope.Transport.UNKNOWN_BOX], else_answer=False)
    # @converted
    def on_connect(self, scopes, token_data):
        print(self, 'connected', '\n', request.sid, scopes, token_data)

        (device_id, name) = getargs(request, 'device_id', 'name')

        if device_id:
            join_room(device_id)

        if name:
            join_room(name)

        if 'device_id' in token_data:
            join_room(token_data['device_id'])

    def on_disconnect(self):
        print(self, 'disconnect', request.sid)

    def on_test(self):
        print(self, 'test', request.sid)
        print(json.dumps(self.server.manager.rooms, indent=2))

    def on_cmd(self, result):
        # print(self, '[cmd]', result)
        iss = result.pop('iss')
        result['from'] = request.sid
        emit('cmd_result', result, room=iss)

    def on_download(self, b64, bundle):
        iss = bundle.pop('iss')
        emit('download_result', (b64, bundle), room=iss)

    @secured([scope.Transport.INOBI], else_answer=None)
    def on_exec(self, cmd, instructions):
        print(self, '[exec]', cmd, instructions)

        d = dict(broadcast=True, include_self=False)

        if 'to' in instructions:
            d['room'] = instructions['to']
            del d['broadcast']

        emit('cmd', dict(iss=request.sid, cmd=cmd, instructions=instructions), **d)

    @secured([scope.Transport.INOBI], else_answer=None)
    def on_upload(self, base64, instructions):
        print(self, '[upload]', base64, instructions)

        d = dict(broadcast=True, include_self=False)

        if 'to' in instructions:
            d['room'] = instructions['to']
            del d['broadcast']

        emit('upload', dict(iss=request.sid, base64=base64, instructions=instructions), **d)

    @secured([scope.Transport.INOBI], else_answer=None)
    def on_exec_download(self, src, instructions):
        print(self, '[exec_download]', src, instructions)

        if 'to' not in instructions:
            print(self, 'broadcast exec_download is not supported yet')
            return

        d = dict(instructions=instructions, source=src, iss=request.sid)

        emit('download', d, room=instructions['to'])
