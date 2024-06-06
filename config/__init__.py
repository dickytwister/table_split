from .config import logger
from .config import setting

logger.setLevel('INFO')
logger.warning('日志模块初始化')
logger.warning('{} 配置初始化'.format(setting.API_DESCRIPTION))
