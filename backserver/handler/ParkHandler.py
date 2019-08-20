# 系统自带的模块
import logging
import json
import time
import base64
import hmac
import os
import queue
import threading

# 第三方模块
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
#import numpy as np

# 自定义模块
from Image import CtrlImage
import TokenDef
import TheQueue

KEY = "WM_GROUND_LOCK" # MTU1MTg2NTkzNi43NTkzMzE6NTNkNDJjY2YwMmU4OWQ0Mjg4M2RjZjViNzg2ODQ4MzUxMzZkYmQyMQ==
RECOGN_REQ = "recogn req"
RECOGN_RESP = "recogn resp"
KEY_TYPE    = "type"
KEY_IMAGE   = "image"
CHILD_KEY_CITY   = "city"
CHILD_KEY_PARK   = "park"
CHILD_KEY_SERVER = "server"
CHILD_KEY_CAMERANO   = "camerano"
CHILD_KEY_IDENTIFY   = "identify"
CHILD_KEY_MD5   = "md5"
CHILD_KEY_CONTENT   = "content"
CHILD_KEY_RESULT   = "result"
CHILD_CHILD_KEY_STATUS   = "status"
CHILD_CHILD_KEY_COLOR   = "color"
CHILD_CHILD_KEY_PLATE   = "plate"

LOGIN_KEY_TYPE  = "type"
LOGIN_KEY_REQ_TYPE  = "request"
LOGIN_KEY_RESP_TYPE = "response"
LOGIN_KEY_CONTENT = "content"
LOGIN_CHILD_KEY_CATEGORY = "category"
LOGIN_CHILD_KEY_CATEGORY_VALUE = "login"
LOGIN_CHILD_KEY_TOKEN = "token"
LOGIN_CHILD_KEY_RESP_STATUS = "status"
LOGIN_CHILD_KEY_CITY = "city"
LOGIN_CHILD_KEY_PARK = "park"
LOGIN_CHILD_KEY_SERVER = "server"

class ParkHandler(tornado.websocket.WebSocketHandler):
    isRegister = False
    '''
    车牌识别的消息队列，用于与车牌识别线程之间通信
    ImageReconQueue是ImageHandler.py用来接收websocket发送过去的等待识别的图片请求
    ImageSeconQueue是ImageHandler.py接收到图片识别数据后向改消息队列发送识别信息的消息队列
    '''
    ImageReconQueue = ""
    ImageSeconQueue = ""
    DelayImageRecognQueue = ""
    '''
    处理请求信息的消息队列,用于本线程内部通信
    ReqQueue是在本程序内部的接收到websocket数据后将数据请求信息放入消息队列中等待处理的消息队列
    '''
    ReqQueue = ""
    '''当前有请求等待响应'''
    bHasRequest = False
    count = 0

    
    serverInfo = {
        "city" : '',
        "park" : '',
        "server" : '',
    }

    msg_login_request = {
        LOGIN_KEY_TYPE : LOGIN_KEY_REQ_TYPE,
        LOGIN_KEY_CONTENT : {
            LOGIN_CHILD_KEY_CATEGORY : LOGIN_CHILD_KEY_CATEGORY_VALUE,
            LOGIN_CHILD_KEY_TOKEN : "MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ=",
            LOGIN_CHILD_KEY_CITY : '',
            LOGIN_CHILD_KEY_PARK : '',
            LOGIN_CHILD_KEY_SERVER : ''
        }
    }

    msg_login_response = {
        LOGIN_KEY_TYPE : LOGIN_KEY_RESP_TYPE,
	    LOGIN_KEY_CONTENT : {
		    LOGIN_CHILD_KEY_CATEGORY : LOGIN_CHILD_KEY_CATEGORY_VALUE,
		    LOGIN_CHILD_KEY_RESP_STATUS : "" 
	    }
    }

    msg_recogn_request = {
        KEY_TYPE : "",
        KEY_IMAGE:{
            CHILD_KEY_CAMERANO : 0,
            CHILD_KEY_IDENTIFY: "",
            CHILD_KEY_MD5 : "",
            CHILD_KEY_CONTENT : ""
        }
    }

    msg_recogn_response = {
        KEY_TYPE : "",
        KEY_IMAGE : {
            CHILD_KEY_CAMERANO : 0,
            CHILD_KEY_IDENTIFY: "",
            CHILD_KEY_RESULT : {
                CHILD_CHILD_KEY_STATUS : "",
                CHILD_CHILD_KEY_COLOR : "",
                CHILD_CHILD_KEY_PLATE : ""
            }
        }
    }


    '''
    用来设置该模块能够被tornado server程序调用
    '''
    def check_origin(self, origin):
        return True

    def open(self):
        logging.info("websocket has client connected!")
        self.isRegister = False
        
        qlist = TheQueue.get()
        
        '''
        图片处理线程的recv对应websocket 的send
        图片处理线程的send对应websocket 的recv
        '''
        self.ReqQueue = queue.Queue(64)
        self.ImageSeconQueue = queue.Queue(10)
        self.DelayImageRecognQueue = queue.Queue(20)
        self.ImageReconQueue = qlist["recv"]
        logging.info(qlist)
    
        self.objPer = tornado.ioloop.PeriodicCallback(self.RegisterEvent, 2000)
        self.objPer.start()

        self.pingObj = tornado.ioloop.PeriodicCallback(self.pingMessage, 5000)
        self.pingObj.start()

        self.startTime = time.time()
        
        self.loopRdReqQueue = tornado.ioloop.PeriodicCallback(self.ReadQueueThreadHandler, 50)
        self.loopRecRegconResultQueueevent = tornado.ioloop.PeriodicCallback(self.RecRegconResEvent, 50)
        self.loopRecRegconResultQueueevent.start()
        pass

    def on_close(self):
        self.objPer.stop()
        self.pingObj.stop()
        logging.info("park on_close(), A client disconnected")

    def on_message(self, message):
        if self.isRegister == False:
            '''
            对每一个新的节点，在连接之后都会建立一个新的websocket线程，在每个线程内，注册函数都是只调用一次
            '''
            self.loginCertification(message)
        else:
            '''logging.info(message)'''
            self.ReqQueue.put(message)
            '''
            开启消息队列监视的loop，如果等待回复的消息数量是零，则关闭loop
            '''
            if self.bHasRequest == False:
                self.bHasRequest = True
                self.loopRdReqQueue.start()

    def on_pong(self, data):
        #logging.info("park on_pong(), keep_alive,{%d}" % self.count)
        self.count = 0

    def on_ping(self, data):
        #logging.info("park on_ping(), data:" + str(data))
        pass

    '''
    处理登陆信息
    '''
    def generateLoginResp(self, mstatus):
        self.msg_login_response[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_RESP_STATUS] = mstatus
        return json.dumps(self.msg_login_response)
        pass

    def loginCertification(self, message):
        #logging.info("message:" + str(message))
        info = json.loads(message)
        
        if self.msg_login_request.keys() ^ info.keys():
            self.write_message(self.generateLoginResp("failed:key"))
            logging.error("websocket login request:key error")
            self.close()
            return

        if self.msg_login_request[LOGIN_KEY_CONTENT].keys() ^ info[LOGIN_KEY_CONTENT].keys():
            self.write_message(self.generateLoginResp("failed:child key"))
            logging.error("websocket login request:child key error")
            self.close()
            return

        if info[LOGIN_KEY_TYPE] != LOGIN_KEY_REQ_TYPE:
            self.write_message(self.generateLoginResp("failed:key type"))
            logging.error("websocket login request:key:type error")
            self.close()
            return

        if info[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_CATEGORY] != LOGIN_CHILD_KEY_CATEGORY_VALUE:
            self.write_message(self.generateLoginResp("failed:key category"))
            logging.error("websocket login request:key:category error")
            self.close()
            return

        token = info[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_TOKEN]
        result = TokenDef.certify_token(KEY, token)
        if result == False:
            self.write_message(self.generateLoginResp("failed:token"))
            logging.error("websocker login request:token error")
            self.close()
            return

        try:
            self.objPer.stop()
            self.isRegister = True
            self.write_message(self.generateLoginResp("success"))
            self.serverInfo[LOGIN_CHILD_KEY_CITY] = info[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_CITY]
            self.serverInfo[LOGIN_CHILD_KEY_PARK] = info[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_PARK]
            self.serverInfo[LOGIN_CHILD_KEY_SERVER] = info[LOGIN_KEY_CONTENT][LOGIN_CHILD_KEY_SERVER]
            logging.info("websockt login request:connect OK")
        except Exception as e:
            logging.warn(e.args)
 

    '''
    登陆定时函数，在时间内未发送正确的数据则断开连接
    '''
    def RegisterEvent(self):
        self.objPer.stop()
        if self.isRegister == False:
            logging.info("websocket login request:timeout")
            self.close()

    def pingMessage(self):
        if(self.count == 5):
            self.close()
            return
        self.count = self.count + 1
        self.ping("hello ping")
    

    '''
    从本线程消息队列中提取等待处理的请求数据
    数据格式是 message 为 json字符串
    '''
    def ReadQueueThreadHandler(self):
        if not self.ReqQueue.empty():
            info = self.ReqQueue.get()
            '''
            接收到的请求信息
            格式
            {
                "type":"recogn req",
                "image":{
                    "city":"shenyang",
                    "park":"wanda",
                    "server":0,
                    "carmerno":3,
                    "time":"1563950307428", #时间戳，精度ms
                    "md5":"xxxxxxxxxx", 
                    "content":"图片的数据"
                }
            }
            '''
            logging.info("recv websocket client data")
            #logging.info(info)
            self.doRequestHandler(info)
        else:
            self.loopRdReqQueue.stop()
            self.bHasRequest = False
        pass


    def doRequestHandler(self, msgjson):
        info = json.loads(msgjson)
        try:
            '''
            检查字典格式是否一致
            '''
            ret = self.msg_recogn_request.keys() ^ info.keys()
            if ret:
                self.write_message(self.genarateRespMsg(info, "failed:key", "", ""))
                logging.error("websocket recogn request:key error")
                return
        
            ret = self.msg_recogn_request[KEY_IMAGE].keys() ^ info[KEY_IMAGE].keys()
            if ret:
                self.write_message(self.genarateRespMsg(info, "failed:child key", "", ""))
                logging.error("websocket recogn request:child key error")
                return
            '''
            检查是否有空的值
            '''
            for key in info.keys():
                if not info[key]:
                    self.write_message(self.genarateRespMsg(info, "failed:%s is null" % key, "", ""))
                    logging.error("websocket recogn request:%s is null" % key)
                    return

            for key in info[KEY_IMAGE].keys():
                if not info[KEY_IMAGE][key]:
                    self.write_message(self.genarateRespMsg(info, "failed:%s is null" % key, "", ""))
                    logging.error("websocket recogn request:%s is null" % key)
                    return
            '''
            检查关键key值是否正确
            '''
            if info[KEY_TYPE] != RECOGN_REQ:
                self.write_message(self.genarateRespMsg(info, "failed:type error", "", ""))
                logging.error("websocket recogn request:type error")
                return
            
            self.doImageHandler(info)
        except Exception as e:
            logging.warn(e.args)

    
    '''
    图片存储以及向main发送图片识别消息通知
    '''
    def doImageHandler(self, dictinfo):
        try:
            hand = CtrlImage()
            
            imagestr = dictinfo[KEY_IMAGE][CHILD_KEY_CONTENT].encode('utf-8')
            imagedata = base64.b64decode(imagestr)
            identify = dictinfo[KEY_IMAGE][CHILD_KEY_IDENTIFY]

            if hand.checkMd5(imagedata, dictinfo[KEY_IMAGE][CHILD_KEY_MD5]) == False:
                self.write_message(self.genarateRespMsg(dictinfo, "failed:md5", "", ""))
                return

            name = self.genarateImageSaveName(dictinfo)
            if not name:
                self.write_message(self.genarateRespMsg(dictinfo, "failed:generate name", "", ""))
                return

            if hand.save(name, imagedata) == False:
                self.write_message(self.genarateRespMsg(dictinfo, "failed:save", "", ""))
                return

            '''logging.info("save image done")
                向图像识别的消息队列发送识别请求
                数据格式是[queue, picname]
                queue是本线程接收图片识别信息的消息队列
                picname为图片名，能够根据图片名定位到图片的位置
            '''
            if self.ImageReconQueue.full():
                '''
                如果图片识别进程的消息队列已经满了，那么这几条消息就会被存放起来
                客户端收到该响应后应该避免再向服务器发送请求，保存在延时处理队列中
                的消息被处理完成后会向服务器发送正常处理结束的响应，接收到响应后，
                服务器才应该进行接下来的识别请求的发送
                '''
                self.write_message(self.genarateRespMsg(dictinfo, "failed:queue full", "", ""))
                self.DelayImageRecognQueue.put([self.ImageSeconQueue, name, identify])
            else:
                self.write_message(self.genarateRespMsg(dictinfo, "ready", "", ""))
                self.ImageReconQueue.put([self.ImageSeconQueue, name, identify])
        except Exception as e:
            logging.info(e.args)
        pass

    '''
    用来接收图片识别结果的消息队列
    接收到的图片识别的信息
    {
        "name":"imagename", 
        "identify" : '',
        "recogn":{
            "status":"success"
            "color":"黄",
            "plate":"辽A12345",
        }
    }
    将识别结果发送给客户端
    {
        "type":"recogn",
        "image":{
            "carmerno":"03",
            "identify":"",
            "result":{
                "status":"success",
                "color":"xxx",
                "plate":"xxxx"
            }
        }
    }
    '''
    def RecRegconResEvent(self) :
        if not self.ImageSeconQueue.empty():
            msgdict = self.ImageSeconQueue.get()
 
            logging.info("Recogn Message, ImageName: %s" % msgdict["name"])
            mresp = self.genarateRecognRespMsg(msgdict)

            try:
                logging.info("send Recogn Message to Client: Status = %s, Color=%s, Plate=%s!" 
                        % (msgdict["recogn"]["status"], msgdict["recogn"]["color"], msgdict["recogn"]["plate"]))
                self.write_message(mresp)
            except Exception as e:
                logging.warn("client connect error")
        '''
        如果延迟识别队列非空，则会先判断图片识别队列是不是满的
        不是满的，则从延迟队列中提取一条消息，发送到识别队列中
        '''
        if not self.DelayImageRecognQueue.empty():
            if not self.ImageReconQueue.full():
                msg = self.DelayImageRecognQueue.get()
                try:
                    self.ImageReconQueue.put(msg)
                except Exception as e:
                    self.DelayImageRecognQueue.put(msg)
                    logging.info("DelayRecognQueue to ImageRecognQueue failed, beacuse ImageQueue is full")
                    logging.info(e.args)
        pass

    def genarateImageSaveName(self, dictinfo):
        timestamp = int(time.time() * 1000)
        name = "%s-%s-%s-%s-%d.jpg" % ( self.serverInfo[CHILD_KEY_CITY], 
                                        self.serverInfo[CHILD_KEY_PARK], 
                                        self.serverInfo[CHILD_KEY_SERVER],
                                        dictinfo[KEY_IMAGE][CHILD_KEY_CAMERANO], 
                                        timestamp)
        return name


    '''
    name format: city-park-server-carmerno-timestr.jpeg
    '''
    def genarateRecognRespMsg(self, msgDict):
        name = msgDict["name"]
        namelist = name.split('-')
        camerano = namelist[3]

        self.msg_recogn_response[KEY_TYPE] = RECOGN_RESP
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_CAMERANO] = camerano
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_IDENTIFY] = msgDict["identify"]
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_STATUS] = msgDict["recogn"]["status"]
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_COLOR] = msgDict["recogn"]["color"]
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_PLATE] = msgDict["recogn"]["plate"]

        return json.dumps(self.msg_recogn_response)


    '''
    生成resp信息
    '''
    def genarateRespMsg(self, dictinfo, mstatus, color, plate):
        self.msg_recogn_response[KEY_TYPE] = RECOGN_RESP
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_CAMERANO] = dictinfo[KEY_IMAGE][CHILD_KEY_CAMERANO]
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_IDENTIFY] = dictinfo[KEY_IMAGE][CHILD_KEY_IDENTIFY]
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_STATUS] = mstatus
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_COLOR] = color
        self.msg_recogn_response[KEY_IMAGE][CHILD_KEY_RESULT][CHILD_CHILD_KEY_PLATE] = plate
        
        return json.dumps(self.msg_recogn_response)
