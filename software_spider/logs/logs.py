#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from logging import handlers
import configparser

"""
################################################################
# description: 日志记录模块
# author: zhengzongwei@foxmail.com
################################################################
"""


class LoggerBase(object):
    """
    Log Baase class
    """

    def __init__(self, logger_name) -> None:
        # 是否控制台输出
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = None
        self.logger_name = logger_name
        self.LOG_LEVEL = None
        self.LOG_FORMAT = None
        self.console_log_status = True
        self.stacklevel = 2

        self.config_log()

    @staticmethod
    def check_log_dir(path) -> bool:
        """
        检查日志目录是否存在，不存在则创建
        :return:
        """
        return os.path.exists(path)

    @staticmethod
    def mkdir_log_dir(path) -> None:
        """
        创建日志目录
        :return:
        """
        if os.path.isfile(path):
            path = os.path.abspath(path)
        return os.makedirs(path)

    def parse_log_level(self, log_level):
        match log_level:
            case 'debug':
                self.LOG_LEVEL = logging.DEBUG
            case 'info':
                self.LOG_LEVEL = logging.INFO
            case 'warning':
                self.LOG_LEVEL = logging.WARNING
            case 'error':
                self.LOG_LEVEL = logging.ERROR
            case 'critical':
                self.LOG_LEVEL = logging.CRITICAL
            case _:
                self.LOG_LEVEL = logging.INFO

    def parse_config(self):
        cf = configparser.RawConfigParser()
        cf.read("./log.conf")
        options = cf.options("logs")
        if 'log_format' in options:
            self.LOG_FORMAT = cf.get("logs", "log_format")
        if self.LOG_FORMAT is None:
            self.LOG_FORMAT = "%(asctime)s - %(name)s[func: %(funcName)s line:%(lineno)d] - %(levelname)s: %(message)s"
        if 'log_level' in options:
            log_level = cf.get("logs", "log_level")
            if log_level not in ['debug', 'info']:
                self.console_log_status = False
            self.parse_log_level(log_level)
        if 'log_dir' in options:
            log_dir = cf.get("logs", "log_dir")
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '')

    def config_log(self):
        """
        配置日志
        :return:
        """
        self.parse_config()

        # chekc exists
        if not self.check_log_dir(self.log_dir):
            self.mkdir_log_dir(self.log_dir)

        # self.init_log(log_path=self.log_dir, log_format=self.LOG_FORMAT)

        log_path = f'{self.log_dir}/{self.logger_name}_logs.log'
        self.init_log(log_path=log_path, log_format=self.LOG_FORMAT)

    def init_log(self, log_path=None, log_format=None):
        """
        初始化日志
        :param
        """
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.LOG_LEVEL)
        self.logger.propagate = True

        if log_path is None:
            log_path = os.path.join()

        if self.LOG_LEVEL in [logging.DEBUG, logging.INFO]:
            self.console_log_status = True

        if log_format is None:
            log_format = "%(asctime)s - %(name)s[func: %(funcName)s line:%(lineno)d] - %(levelname)s: %(message)s"
        format_str = logging.Formatter(log_format)

        if self.console_log_status:
            console_handle = logging.StreamHandler()
            console_handle.setFormatter(format_str)
            self.logger.addHandler(console_handle)

        file_handle = handlers.TimedRotatingFileHandler(filename=log_path, when='D', backupCount=3,
                                                        encoding='utf-8')
        file_handle.setFormatter(format_str)
        self.logger.addHandler(file_handle)

    def debug(self, msg):
        self.logger.debug(msg, stacklevel=self.stacklevel)

    def info(self, msg):
        self.logger.info(msg, stacklevel=self.stacklevel)

    def warn(self, msg):
        self.logger.warning(msg, stacklevel=self.stacklevel)

    def error(self, msg):
        self.logger.error(msg, stacklevel=self.stacklevel)

    def critical(self, msg):
        self.logger.critical(msg, stacklevel=self.stacklevel)


if __name__ == '__main__':
    LoggerBase("ss")
