#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import os
import sys
import logging
import logging.config
import logging.handlers
import multiprocessing
from functools import wraps
import Config
import Const

global_queue = multiprocessing.JoinableQueue(-1)

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return get_instance

@singleton
class LoggingConsumer(object):

    def __init__(self):
        formatter = logging.Formatter(Const.FORMATTER_FMT, Const.FORMATTER_DATE_FMT)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)

        c = Config.Config()
        filename = c.get('CONFIG', 'LOGFILE')
        file_handler = logging.handlers.TimedRotatingFileHandler(filename=filename, when='midnight', encoding='utf8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(stream_handler)
        root.propagate = 0

        work = logging.getLogger(Const.WORK_LOGGER)
        work.setLevel(logging.INFO)
        work.addHandler(file_handler)
        work.propagate = 1

    def process(self):
        while True:
            try:
                record = global_queue.get()
                if record is None:
                    continue
                logger = logging.getLogger()
                if record.name:
                    logger = logging.getLogger(record.name)
                logger.handle(record)
                global_queue.task_done()
            except Exception as exception:
                import sys, traceback
                print('Exception: ' + str(exception), file=sys.stderr)
                traceback.print_exc(file=sys.stderr)


@singleton
class LoggingProducer(object):

    def __init__(self):
        handler = logging.handlers.QueueHandler(global_queue)
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)

    def log(self, logger_name=Const.WORK_LOGGER, level=logging.INFO, message='', *args, **kwargs):
        logger = logging.getLogger(logger_name)
        logger.log(level, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        logger = logging.getLogger(Const.WORK_LOGGER)
        logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        logger = logging.getLogger(Const.WORK_LOGGER)
        logger.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        logger = logging.getLogger(Const.WORK_LOGGER)
        logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        logger = logging.getLogger(Const.WORK_LOGGER)
        logger.error(message, *args, **kwargs)


def start_logger_consumer():
    consumer = LoggingConsumer()
    consumer.process()


def terminate_logger_consumer():
    global_queue.put_nowait(None)


def start_logger_producer():
    produce = LoggingProducer()

    i = 0
    while i < 100:
        produce.info('i: %d, name: %s', i, multiprocessing.current_process().name)
        i += 1

