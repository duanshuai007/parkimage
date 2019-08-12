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

class SerApplication(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/park", ParkHandler), ]
        settings = dict(debug=True, websocket_ping_interval=30)
        Application.__init__(self, handlers, **settings)

def main():
    logfile = Config.getConfigEnv("LOGFILE")
    websocket_port = Config.getConfigEnv("WEBSOCKET_PORT")

    if not logfile:
        logging.error("LogFile[%s] not define, please add to config.ini" % logfile)

    logging.basicConfig(filename=logfile, level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(filename)s[line:%(lineno)d]: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    tornado.options.parse_command_line()
    app = SerApplication()
#app.listen(websocket_port)

    '''
    ssl处理，
    privateKey.key 生成：openssl req -out CSR.csr -new -newkey rsa:2048 -nodes -keyout privateKey.key
    certificate.crt 生成：openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout privateKey.key -out certificate.crt
    '''
    rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    logging.info("rootdir:%s" % rootdir)
    try:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#ssl_ctx.load_cert_chain(os.path.join(rootdir + '/', "certificate.crt"),
#                      os.path.join(rootdir + '/', "privateKey.key"))

        ssl_ctx.load_cert_chain(rootdir + "/certificate.crt", rootdir + "/privateKey.key")
        httpServer = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
        httpServer.listen(websocket_port, "0.0.0.0")
    except Exception as e:
        logging.error(e.args)
        logging.error("ImageHandler Error!, SSL error")
        return

    TheQueue.init()
    dicts = TheQueue.get()
    
    imageHandler = ImageHandler.ImageHandler([dicts,])
    imageHandler.run()
    if imageHandler.isRunOK() == False:
        logging.error("ImageHandler Error!, Now Project exit")
        print("ImageHandler Error!, Now Project exit")
        return

    tornado.ioloop.IOLoop.instance().start()
    logging("main ioloop start down")

if __name__ == "__main__":
    main()
