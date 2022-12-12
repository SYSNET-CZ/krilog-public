import os

VERSION = os.getenv('KRILOG_VERSION', '1.0.0-rc4')
APP_NAME = os.getenv('KRILOG_NAME', 'KRILOG')
APP_SECRET_KEY = os.getenv('APP_SECRET_KEY', 'app_key')
DEBUG = os.getenv("DEBUG", 'True').lower() in ('true', '1', 't')
TZ = os.getenv('TZ', 'Europe/Prague')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s in %(module)s: %(message)s')
LOG_DATE_FORMAT = os.getenv('LOG_DATE_FORMAT', '%d.%m.%Y %H:%M:%S')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root
LOG_DIR = os.getenv('KRILOG_LOG_DIR', os.path.join(ROOT_DIR, 'logs'))
DATA_DIR = os.getenv('KRILOG_DATA_DIRECTORY', os.path.join(ROOT_DIR, 'data'))
