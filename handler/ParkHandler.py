# 系统自带的模块
import logging
import json
import time
import base64
import hmac

# 第三方模块
import redis
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
#import numpy as np

# 自定义模块
from HandleDB import ParkDB
from Image import CtrlImage
import TokenDef
import Constant
import TheQueue

KEY = "WM_GROUND_LOCK" # MTU1MTg2NTkzNi43NTkzMzE6NTNkNDJjY2YwMmU4OWQ0Mjg4M2RjZjViNzg2ODQ4MzUxMzZkYmQyMQ==

class ParkHandler(tornado.websocket.WebSocketHandler):
    #handleDB = ParkDB()
    isRegister = False
    start_recv_image = False
    rqueue = ""
    squeue = ""
    image_list = []

    resp_msg = {
        "type":"",
        "identify":"",
        "status":""
    }

    success_msg = {
        
    }

    '''
    用来设置该模块能够被tornado server程序调用
    '''
    def check_origin(self, origin):
        return True

    def open(self):
        logging.info("websocket has client connected!")
        self.isRegister = False
# TheQueue.initQueue()
        qlist = TheQueue.getQueue()
        '''
        图片处理线程的recv对应websocket 的send
        图片处理线程的send对应websocket 的recv
        '''
        self.rqueue = qlist["recv"]
        self.squeue = qlist["send"]
        logging.info(qlist)
        self.objPer = tornado.ioloop.PeriodicCallback(self.RegisterEvent, 3000)
        self.objPer.start()
        self.startTime = time.time()
        pass

    def on_close(self):
        self.objPer.stop()
        logging.info("park on_close(), A client disconnected")

    def on_message(self, message):
        if self.isRegister == False:
            '''
            对每一个新的节点，在连接之后都会建立一个新的websocket线程，在每个线程内，注册函数都是只调用一次
            '''
            self.loginCertification(message)
        else:
            '''
            if self.start_recv_image == True:
                self.imageHandler(message)
            else:
                self.messageHandler(message)
            '''
            self.rqueue.put(message)

    def on_pong(self, data):
        logging.info("park on_pong(), keep_alive,{}")

    def on_ping(self, data):
        logging.info("park on_ping(), data:" + str(data))

    '''
    处理登陆信息
    '''
    def loginCertification(self, message):
        #logging.info("message:" + str(message))
        info = json.loads(message)
        
        msgtype = ""
        msgcontent = ""
        for key in info:
            #logging.info("key="+key)
            if ( key == "type"):
                msgtype = info[key]
            if ( key == "content"):
                msgcontent = info[key]
        if not msgtype or not msgcontent:
            #logging.info("login message error")
            self.close()
        
        if msgtype != "request":
            self.close()

        category = ""
        token = ""
        for key in msgcontent:
            #logging.info("subkey="+key)
            if (key == "category"):
                category = msgcontent[key]
            if (key == "token"):
                token = msgcontent[key]
        if not category or not token:
            #logging.info("login content error")
            self.close()

        if category != "login":
            self.close()
        #logging.info("token:" + token)
        result = TokenDef.certify_token(KEY, token)
        if result == False:
            self.close()

        self.objPer.stop()
        self.isRegister = True
        logging.info("connect OK")
        

    '''
    检查接收到的json请求的格式 第一层
    '''
    def checkJsonRequestStepOne(self, minfo):
        mdict = {   "type":"", 
                    "identify":"", 
                    "image":""}
        for key in minfo:
            if (key == "type"):
                mdict[key] = minfo[key]
            if (key == "image"):
                mdict[key] = minfo[key]
            if (key == "identify"):
                mdict[key] = minfo[key]

        for item in mdict.keys():
            if not mdict[item]:
                logging.info("struct error")
                self.genarateRespMsg("sendimg", "head", "error")
                self.write_message(json.dumps(self.resp_msg))
                return False

        if mdict["type"] != "recogn":
            logging.info("key value error")
            self.genarateRespMsg("sendimg", mdict["identify"], "error")
            self.write_message(json.dumps(self.error_msg)) 
            return False

        self.image_list.append(mdict)
        #print(self.image_list)
        return True

    '''
    检查接收到的json请求的格式 第二层
    '''
    def checkJsonRequestStepTwo(self, info):
        minfo = info["image"]
        mdict = {   "city":"", 
                    "park":"", 
                    "carmerno":"",
                    "time":"",
                    "size":"",
                    "md5":""}
        for key in minfo:
            if (key == "city"):
                mdict[key] = minfo[key]
            if (key == "park"):
                mdict[key] = minfo[key]
            if (key == "carmerno"):
                mdict[key] = minfo[key]
            if (key == "time"):
                mdict[key] = minfo[key]
            if (key == "size"):
                mdict[key] = minfo[key]
            if (key == "md5"):
                mdict[key] = minfo[key]
        for item in mdict.keys():
            if not mdict[item]:
                logging.info("struct error")
                self.genarateRespMsg("sendimg", info["identify"], "error")
                self.write_message(json.dumps(self.resp_msg))
                return False

        self.image_list[0]["image"] = mdict
        #print(self.image_list)
        return True

    '''
    客户端的图片传输请求
    '''
    def messageHandler(self, message):
        #logging.info("message:" + str(message))
        info = json.loads(message)
        if self.checkJsonRequestStepOne(info) == False:
            return
        if self.checkJsonRequestStepTwo(info) == False:
            return

        self.genarateRespMsg("ready", self.image_list[0]["identify"], "recvimage")
        self.write_message(json.dumps(self.resp_msg))
        self.start_recv_image = True

    '''
    图片存储以及向main发送图片识别消息通知
    '''
    def imageHandler(self, message):
#       logging.info("imageHandler")
#logging.info(self.image_list)
#       logging.info("md5:%s" % self.image_list[0]["image"]["md5"])
        hand = CtrlImage()
        ret = hand.checkMd5(message, self.image_list[0]["image"]["md5"])
        if ret == False:
            logging.info("md5 error")
            self.genarateRespMsg("recv", self.image_list[0]["identify"], "md5 error")
            self.write_message(json.dumps(self.resp_msg))
            return
        
        name = self.genarateImageSaveName() 
        if hand.save(name, message) == False:
            self.genarateRespMsg("save", self.image_list[0]["identify"], "save error")
            self.write_message(json.dumps(self.resp_msg))
            return
        logging.info("save image done")
        del self.image_list[0]


    '''
    登陆定时函数，在时间内未发送正确的数据则断开连接
    '''
    def RegisterEvent(self):
        #logging.info("RegisterEvent")
        self.objPer.stop()
        if self.isRegister == False:
            self.close()
#logging.info("self.addNum:" + str(self.addNum))
#       self.addNum = self.addNum + 1
#       self.sendUpdateData()

    def genarateRespMsg(self, mtype, mid, mstatus):
        self.resp_msg["type"] = mtype
        self.resp_msg["identify"] = mid
        self.resp_msg["status"] = mstatus
        pass

    def genarateImageSaveName(self):
        name = '%s-%s-%d-%s.jpeg' % ( self.image_list[0]["image"]["city"], 
             self.image_list[0]["image"]["park"],
             self.image_list[0]["image"]["carmerno"],
             self.image_list[0]["image"]["time"])
        logging.info("name:%s" % name )
        return name
        pass
