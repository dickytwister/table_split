# -*- coding: UTF-8 -*-
import sys
import os
import logging
from log_config import FinalLogger

sys.path.append(os.path.dirname(__file__))

APP_ENV = (os.environ.get('APP_ENV') or 'dev').lower()
assert APP_ENV in ['dev', 'prod']
MAP = {
    "dev": "测试环境",
    "prod": "生产环境"
}


class DefaultSetting(object):
    """Default configuration.
    Flask-Restplus settings,see more:https://flask-restx.readthedocs.io/en/latest/configuration.html
    Flask settings,see more:https://flask.palletsprojects.com/en/2.0.x/
    """
    FLASK_ENV = APP_ENV
    FLASK_API_URL_PREFIX = '/model'
    SWAGGER_UI_DOC_EXPANSION = 'list'
    RESTX_VALIDATE = False
    RESTX_MASK_SWAGGER = True
    ERROR_404_HELP = False
    API_VERSION = '1.0'
    API_TITLE = 'ha-extract-service'
    API_DESCRIPTION = f'{API_TITLE}-{MAP.get(APP_ENV)}'
    API_LOG_PATH = 'application.log'


class DevSetting(DefaultSetting):
    table_head_url = 'http://10.106.0.57:10051/model/table_extract/table_header_analyse?key=111&bussid=111'
    gilner_url = 'http://10.3.12.7:9396/predictions/gilner/1'


class ProdSetting(DefaultSetting):
    pass


if APP_ENV == 'prod':
    setting = ProdSetting()
elif APP_ENV == 'dev':
    setting = DevSetting()
else:
    raise Exception('unkown environment:{}'.format(APP_ENV))

FinalLogger(setting.API_LOG_PATH)
logger = logging.getLogger()

