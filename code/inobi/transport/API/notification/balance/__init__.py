from inobi.transport.data_checker import TransportVariables as TV
from inobi.transport.configs import TONotificationSettingKeys

from inobi.transport.utils import send_email
from threading import Thread

from .parser import parse
from . import config
from ..config import PING_KEY
from time import time


def handle(current: dict, settings: dict):
    if not current.get(TV.BALANCE):
        return
    balance = parse(current[TV.BALANCE])
    current['balance'] = balance
    if not balance:
        return
    if not settings.get(TONotificationSettingKeys.BALANCE):
        return
    now = time()
    settings = settings[TONotificationSettingKeys.BALANCE]
    if balance <= settings['min_balance'] and not current[PING_KEY].get('balance'):
        current[PING_KEY]['balance'] = now
        Thread(target=send_email, kwargs={
            "to_address": settings['emails'],
            "subject": config.get_subject(current),
            "message": config.get_message(current),
        }, daemon=True).start()

    elif balance > settings['min_balance'] and current[PING_KEY].get('balance'):
        current[PING_KEY]['balance'] = None



