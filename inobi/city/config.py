
import enum

from os import makedirs, path
from inobi.config import RESOURCES_DIRECTORY
from inobi import add_prerun_hook
from decouple import config

NAME = 'Inobi Cities'

PREFIX = '/'

RESOURCES_CITIES = path.join(RESOURCES_DIRECTORY, 'city/')

RESOURCES_CITIES_UPGRADER = path.join(RESOURCES_CITIES, 'dbupgrader/')
add_prerun_hook(lambda: makedirs(RESOURCES_CITIES_UPGRADER, exist_ok=True))

CITY_UPGRADE_TEMPLATE = path.join(RESOURCES_CITIES_UPGRADER, '{name}.c{city}.to{organization}.u{user}.db{stage}')

UPGRADE_PROCESS_REDIS_KEY_TEMPLATE = 'city:bfs_extraction:{name}'


class CityUpgradeStage(enum.Enum):
    INIT = 'init'
    PROCESSING = 'processing'
    DONE = 'done'

    @property
    def withdot(self):
        return '.'+self.value


CITY_DB_TEMPLATE = path.join(RESOURCES_CITIES, '{city_id}/', 'data/', 'v{data_version}.zip')

DB_FILENAME_IN_ARCHIVE = 'data.db'

BFS_ROUTES_TABLE_NAME = config('BFS_ROUTES_TABLE_NAME', cast=str, default='user_routes')    # (user_routes, user_routes_v2, routes, etc)

assert BFS_ROUTES_TABLE_NAME in ('user_routes', 'user_routes_v2', 'routes')
