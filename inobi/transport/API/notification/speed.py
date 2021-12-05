from flask_socketio import emit
from inobi.transport.configs import Event, Room, WS_ADMIN_NAMESPACE, TONotificationSettingKeys as SettingsVar
import time
from inobi.transport.organization.db.notifications import Notification
from inobi.transport.notification_configs import transport_speed_violation as SV
from .config import PING_KEY


def handle(current: dict, settings: dict):
    if current.get('speed'):
        if settings.get(SettingsVar.MAX_SPEED):
            if settings[SettingsVar.MAX_SPEED] <= current['speed'] <= SV.SHADOW_SPEED_LIMIT:
                over_speed(current, settings[SettingsVar.MAX_SPEED])


def over_speed(ping: dict, max_speed: int):
    now = time.time()
    if ping[PING_KEY].get('speed'):
        if now - ping[PING_KEY]['speed'] < SV.SILENT_PERIOD:
            return

    ping[PING_KEY]['speed'] = now
    organization = ping.get('organization')
    if isinstance(organization, dict):
        organization_id = organization['id']
    else:
        organization_id = organization

    extras = dict(
        id=ping['id'],
        line_id=ping['line_id'],
        device_id=ping['device_id'],
        driver=ping['driver'],
        location=ping['location'],
        time=ping['time']
    )
    notification = Notification.add(to_id=organization_id,
                                    type=SV.TYPE,
                                    domain=SV.DOMAIN,
                                    title=SV.TITLE,
                                    content='{} transport accelerated aver max speed {}'.format(ping['name'], max_speed),
                                    attributes={
                                        SV.Attributes.SPEED: ping['speed'],
                                        SV.Attributes.NUMBER: ping['number'],
                                        SV.Attributes.TYPE: ping['type'],
                                        SV.Attributes.NAME: ping['name']
                                    },
                                    payload=extras)
    payload = dict(
        type=Event.NotificationType.ADD,
        payload=notification._asdict()
    )
    ws_emit(payload, organization_id)


def ws_emit(payload: dict, organization_id: int):
    emit(Event.NOTIFICATION, payload, room=Room.notification(organization_id),
         namespace=WS_ADMIN_NAMESPACE)

