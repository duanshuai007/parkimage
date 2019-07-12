#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 系统自带的模块
import os
import ssl
import logging
import sys

# 第三方模块
#import redis
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado.web import Application

# 自定义模块
from handler.ParkHandler import ParkHandler
from Image import CtrlImage
import ImageHandler
import TheQueue 
import Config

class MyTest(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):
        print("open!")

    def on_close(self):
        print("close!")
    
    def on_message(self, message):
        print("message:" + message)
    
    def on_pong(self, data):
        print("pong")

    def on_ping(self, data):
        print("ping")

    def keep_alive(self):
        print("keep alive")

    def get_token(self):
        print("get token")


class SerApplication(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/park", ParkHandler), (r"/test", MyTest) ]
        settings = dict(debug=True, websocket_ping_interval=30)
        Application.__init__(self, handlers, **settings)


def main():
    websocket_port = 0
    logfile = ''
#path = os.path.dirname(os.path.abspath(sys.argv[0]))

    logfile = Config.getConfigEnv("LOGFILE")
    websocket_port = Config.getConfigEnv("WEBSOCKET_PORT")

    if not logfile:
        logging.err("LogFile not define, please add to config.ini")
    print("logfile name:%s" % logfile)
    logging.basicConfig(filename=logfile, level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d]: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    tornado.options.parse_command_line()
    app = SerApplication()
    app.listen(websocket_port)

    '''
    ssl处理，
    privateKey.key 生成：openssl req -out CSR.csr -new -newkey rsa:2048 -nodes -keyout privateKey.key
    certificate.crt 生成：openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout privateKey.key -out certificate.crt
    '''
    # ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_ctx.load_cert_chain(os.path.join("./", "certificate.crt"),
    #                    os.path.join("./", "privateKey.key"))
    # httpServer = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    # httpServer.listen(Constant.options.port, Constant.options.host)

    TheQueue.init()
    dicts = TheQueue.get()
    
    imageHandler = ImageHandler.ImageHandler([dicts,])
    imageHandler.run()

    tornado.ioloop.IOLoop.instance().start()
    logging("main ioloop start down")

if __name__ == "__main__":
    main()
