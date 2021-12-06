
from . import speed, balance, config


def check_for_notification(prev: dict, current: dict, organization: dict):
    individual = (current.get('payload') or {}).get('notification')
    settings = (organization.get('settings') or {}).get('notification')
    if not settings:
        settings = dict()
    if not individual:
        individual = dict()
    if config.PING_KEY not in current:
        current[config.PING_KEY] = {}

    settings.update(individual)

    # fix when speed violation checks organization in ping
    to_in_ping = 'organization' in current
    prev_transport_organization = current.get('organization')
    current['organization'] = organization

    speed.handle(current, settings)
    balance.handle(current, settings)

    if to_in_ping:
        current['organization'] = prev_transport_organization
