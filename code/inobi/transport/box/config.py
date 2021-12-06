
import os

from inobi.config import RESOURCES_DIRECTORY
from inobi import add_prerun_hook

PREFIX = '/transport/box'

BOX_UPDATE_FILE = 'update'

ALLOW_INTERNET_OPTIONS = frozenset(('true', 'on', 'allow', True))


class CKeys:
    VERSION = 'transport:box:version'
    INTERNET = 'transport:box:internet'


TRANSPORT_RESOURCES = os.path.join(RESOURCES_DIRECTORY, 'transport')
BOX_RESOURCES = os.path.join(TRANSPORT_RESOURCES, 'box')
BOX_UPDATES_DIRECTORY = os.path.join(BOX_RESOURCES, 'updates')

add_prerun_hook(lambda: os.makedirs(BOX_UPDATES_DIRECTORY, exist_ok=True))
