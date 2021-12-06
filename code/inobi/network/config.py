import os
from decouple import config
from inobi.config import RESOURCES_DIRECTORY
from inobi.network.redis_list import RedisList
from inobi.network.redis_ttl_set import RedisTTLSet
from inobi.redis import getredis as _getredis

NAME = 'Network'
PREFIX = '/network'
FTP_REPORTS_DIR = "ARA_BOX"

FTP_SERVER = config('FTP_SERVER', cast=str)
FTP_PORT = config('FTP_PORT', cast=int)
FTP_USER = config('FTP_USER', cast=str)
FTP_PASS = config('FTP_PASS', cast=str)

SERVICE_NUMBER = 8
OPERATOR_NAME = "rightel"

FOLDER_DIRECTORY = os.path.join(RESOURCES_DIRECTORY, 'network/')

os.makedirs(FOLDER_DIRECTORY, exist_ok=True)

IPDR_KEY = "IPDR_LIST"
CDR_KEY = "CDR_LIST"

TTL = 300
ipdr_buffer = RedisTTLSet(IPDR_KEY, _getredis(), TTL)
cdr_buffer = RedisTTLSet(CDR_KEY, _getredis(), TTL)
