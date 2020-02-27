# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018-06-26 9:10
# @Author  : Jackadam
# @Email   :jackadam@sina.com
# @File    : logging_conf.py
# @Software: PyCharm

import logging.config, logging, os
import queue
import threading
import time
import multiprocessing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True  # 标记是否在开发环境
LOGGERNAME = "park"

# 给过滤器使用的判断
class RequireDebugTrue(logging.Filter):
    # 实现filter方法
    def filter(self, record):
        return DEBUG


LOGGING = {
    # 基本设置
    'version': 1,  # 日志级别
    'disable_existing_loggers': False,  # 是否禁用现有的记录器

    # 日志格式集合
    'formatters': {
        # 标准输出格式
        'standard': {
            # [具体时间][线程名:线程ID][日志名字:日志级别名称(日志级别ID)] [输出的模块:输出的函数]:日志内容
            'format': '[%(asctime)s][%(threadName)s:%(thread)d][%(name)s:%(levelname)s(%(lineno)d)][%(module)s:%(funcName)s]:%(message)s'
        }
    },

    # 过滤器
    'filters': {
        'require_debug_true': {
            '()': RequireDebugTrue,
        }
    },

    # 处理器集合
    'handlers': {
        # 输出到控制台
        'console': {
            'level': 'DEBUG',  # 输出信息的最低级别
            'class': 'logging.StreamHandler',
            'formatter': 'standard',  # 使用standard格式
            'filters': ['require_debug_true', ],  # 仅当 DEBUG = True 该处理器才生效
        },
        # 输出到文件
        'log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(BASE_DIR, 'debug.log'),  # 输出位置
            'maxBytes': 1024 * 1024 * 5,  # 文件大小 5M
            'backupCount': 5,  # 备份份数
            'encoding': 'utf8',  # 文件编码
        },
    },

    # 日志管理器集合
    'loggers': {
        # 管理器
        'default': {
            'handlers': ['console', 'log'],
            'level': 'DEBUG',
            'propagate': True,  # 是否传递给父记录器
        },
        # 管理器
        "park" : {
            'handlers': ['console', 'log'],
            'level': 'DEBUG',
            'propagate': True,  # 是否传递给父记录器
        },

    }
}

#global_queue = multiprocessing.JoinableQueue(-1)
logQueue = queue.Queue(1024)

class LoggingConsumer():
    def __init__(self):
        logging.config.dictConfig(LOGGING)
'''
    def process(self):
        while True:
            try:
                record = global_queue.get()
                print("in process get msg")
                print(record)
                global_queue.task_done()
            except Exception as e:
                print(e)
'''
    def run(self):
        t = threading.Thread(target=self.task, args=[])
        t.setDaemon(False)
        t.start()

    def task(self):
        try:
            while True:
                if not logQueue.empty():
                    msg = logQueue.get()
                    print("in LoggingConsumer get msg")
                    print(msg)
        except Exception as e:
            print(e)

#print(msg)

class LoggingProducer():
    def __init__(self):
        print("LoggingProducer init")
        handler = logging.handlers.QueueHandler(logQueue)
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)

    def log(self, logger_name=LOGGERNAME, level=logging.INFO, message='', *args, **kwargs):
        logger = logging.getLogger(logger_name)
        logger.log(level, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        logger = logging.getLogger(LOGGERNAME)
        logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        logger = logging.getLogger(LOGGERNAME)
        logger.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        logger = logging.getLogger(LOGGERNAME)
        logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        logger = logging.getLogger(LOGGERNAME)
        logger.error(message, *args, **kwargs)

'''
def log_main():
    # 加载前面的标准配置
    logging.config.dictConfig(LOGGING)

    # 获取loggers其中的一个日志管理器
    logger = logging.getLogger("shoujitiku")
    return logger

loger = log_main()
loger.debug('hello')
'''
if __name__ == "__main__":
    print("11111111111111")
    xiaofei = LoggingConsumer()
    xiaofei.run()
    print("2222222222222222")
    worker = LoggingProducer()
    print("3333333333333333")
    worker.info("helloworld")
    while True:
        time.sleep(1)
        worker.info("helloworld")
        print("ddddddddddddddddddd")
