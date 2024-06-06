#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 @desc:
 @author:
 @software: PyCharm  on 2018/8/21
"""
import os
import logging
from logging import config
from pathlib import Path
import yaml

env = os.environ.get('APP_ENV') or 'dev'
assert env in ['dev', 'prod']
logging_config_yaml_path = Path(__file__).parent / f'logging_config.yaml'


class LoggingFilter(logging.Filter):
    def __init__(self):
        super(LoggingFilter, self).__init__()

    def filter(self, record):
        black_list = []
        white_list = []
        for word in black_list:
            # 日志的来源文件名不能为黑名单中的词
            if word in record.name:
                return False
        if len(white_list) > 0:
            for word in white_list:
                # 日志消息中至少包含一个白名单中的词
                if word in record.msg:
                    return True
        else:
            return True


class MyFormatter(logging.Formatter):
    """
    重写format方法，将日志转为json格式,替换换行符以及value中的英文双引号
    """

    def formatMessage(self, record):
        record.message = record.message.replace("\n", "\\n").replace('\t', '\\t')
        return super().formatMessage(record)


class FinalLogger:
    """
    if log_path is not empty,info_file_handler is set
    if log_path is empty and env is not 'prod', info_handler is set
    """
    def __init__(self, log_path='', level=None):
        self.final_log_path = None
        log_config = yaml.safe_load(open(logging_config_yaml_path.as_posix(), encoding="utf-8"))

        if log_path:
            if not Path(log_path).is_absolute():
                log_dir = Path(__file__).parent.parent/'logs'
                log_dir.mkdir(exist_ok=True)
                log_path = (log_dir / log_path).as_posix()
            log_config['root']['handlers'] = ['info_file_handler', 'info_handler']
            log_config["handlers"]["info_file_handler"]["filename"] = log_path

            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        logging.config.dictConfig(log_config)
        logger = logging.getLogger()
        if level is not None:
            logger.setLevel(level)
        logger.warning('final logger initialized')
