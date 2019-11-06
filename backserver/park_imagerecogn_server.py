#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 系统自带的模块
import os
import ssl
import sys
import threading 

# 第三方模块
#import redis
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado.web import Application

from multiprocessing import Process

# 自定义模块
#from LoggingHelper import LoggingProducer, start_logger_consumer, terminate_logger_consumer
from WebSocketThread import WebSocketThread 
from Image import CtrlImage
#import socketClient 
from socketClient import ImageShow
import BlackListThread
import TheQueue 
import Config
from LoggingHelper import LoggingProducer, start_logger_consumer, terminate_logger_consumer

def start_log_process() -> None:
    global logger_process
    logger_process = Process(target=start_logger_consumer)
    logger_process.start()

def end_log_process() -> None:
    global logger_process
    terminate_logger_consumer()
    if logger_process is not None:
        logger_process.join()

class SerApplication(tornado.web.Application):
    def __init__(self, QueueList) :
        handlers = [(r"/park1", WebSocketThread, {"MsgQueue":QueueList, "cameraip":"192.168.200.211"}), (r"/park2", WebSocketThread, {"MsgQueue":QueueList, "cameraip":"192.168.200.213"})]
        settings = dict(debug=True, websocket_ping_interval=30)
        Application.__init__(self, handlers, **settings)

def main():
    c = Config.Config()
    logfile = c.get("CONFIG", "LOGFILE")
    websocket_port = c.get("WEBSKCKET", "PORT")

    start_log_process()
    logger = LoggingProducer()

    TheQueue.init()
    dicts = TheQueue.get()

    tornado.options.parse_command_line()

    if not logfile:
        print("LogFile[%s] not define, please add to config.ini" % logfile)
    print("logfile:%s" % logfile)
    '''
    ssl处理，
    privateKey.key 生成：openssl req -out CSR.csr -new -newkey rsa:2048 -nodes -keyout privateKey.key
    certificate.crt 生成：openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout privateKey.key -out certificate.crt
    '''
    rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    logger.info(f'rootdir:{rootdir}')
    try:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(rootdir + "/certificate.crt", rootdir + "/privateKey.key")
        
        app = SerApplication(dicts)
        httpServer = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
        httpServer.listen(websocket_port, "0.0.0.0")
    except Exception as e:
        logger.error(f'socketClient Error!, SSL error:{e.args}')
        return
    
    transferStation = ImageShow(dicts)
    transferStation.run()

    BlackListThread.BlackList(dicts)

    tornado.ioloop.IOLoop.instance().start()
    end_log_process()

if __name__ == "__main__":
    main()
