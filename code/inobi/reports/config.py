from inobi.config import RESOURCES_DIRECTORY
import os

NAME = 'Report'
PREFIX = '/reports'

FOLDER_DIRECTORY = os.path.join(RESOURCES_DIRECTORY, 'reports/')

os.makedirs(FOLDER_DIRECTORY, exist_ok=True)
