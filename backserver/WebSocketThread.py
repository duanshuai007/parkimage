# 系统自带的模块
import json
import time
import base64
import hmac
import os
import queue
import threading
import copy
import bz2
import struct

# 第三方模块
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.options
import tornado.httpserver
from tornado import web, ioloop
#import numpy as np

# 自定义模块
import Image
import TokenDef
import TheQueue
import LoggingQueue
from strictly_func_check import strictly_func_check

KEY = "WM_GROUND_LOCK" # MTU1MTg2NTkzNi43NTkzMzE6NTNkNDJjY2YwMmU4OWQ0Mjg4M2RjZjViNzg2ODQ4MzUxMzZkYmQyMQ==
LOGIN_REQ = 1 
LOGIN_RESP = 2 
RECOGN_REQ = 3 
RECOGN_RESP = 4 

COMPRESS_MODE_NONE = 0 
COMPRESS_MODE_BZ2 = 1 

RET_FAILED              = 1
RET_RECOGNMSG_REFUSE    = 2
RET_RECOGNMSG_GENAME    = 3
RET_RECOGNMSG_SAVE      = 4

class WebSocketThread(tornado.websocket.WebSocketHandler):
    __isRegister = False
    '''
    车牌识别的消息队列，用于与车牌识别线程之间通信
    ImageReconQueue是socketClient.py用来接收websocket发送过去的等待识别的图片请求
    '''
    ImageReconQueue = None
    BackListQueue = None
    '''图片保存，校验md5的句柄'''
    ImageHandler = None
    
    '''当前有请求等待响应'''
    __bHasRequest = False
    __CameraIP = ''
    __count = 0
    
    __serverInfo = {
        "city" : '',
        "park" : '',
        "server" : '',
    }

    __status_dict = {
        "success" : 0,
        "failed" : 1,
        "ready" : 2,
        "refuse" : 3,
        "goon" : 4,
        "stop" : 5,
    }

    __errcode_dict = {
        "recogn" : 0,
        "timeout" : 1,
        "name" : 2,
        "save" : 3,
        "show" : 4,
        "recogn pthread" : 5,
        "format" : 6,
        "md5" : 7,
        "login" : 8,
    }

    ''' 
    所有的数据格式遵循以下原则:
    Type    1Byte   '1:login request 2:login response 2:recogn request 3:recogn response'
    Mode    1BYte   '0:未压缩 1:bz2 2...可扩展'
    Body    xByte   消息载体

    所有实际的消息都在Body段内:
    1.登陆信息的数据格式
    City    1Byte       城市编号,十六进制
    Park    1Byte       停车场编号,十六进制
    Server  1Byte       服务器编号,十六进制 
    Token   80String    对应的字符串

    2.登陆响应
    Status  1Byte       1:失败 0:成功

    3.识别请求
    CameraNo        1Byte       相机编号，十六进制
    Identify        19String    标识符字符串
    MD5             32String    md5字符串
    ImageLen        1Int(长度为4Byte)   图片的大小
    ImageContent    xxxString   图片数据信息

    4.识别响应
    CameraNo        1Byte
    Identify        19String
    Status          1Byte
    Color           8String
    Plate           16String
    '''
    '''
    struct数据对其方式：
    @ 凑够四个字节
    = 按原字节数对齐
    < 小端 按原字节数对齐
    > 大端 按原字节数对齐
    ! network(大端) 按原字节数对齐
    '''
    MsgSizeAlign = ">"
    MsgHeadStruct = "BB"
    LoginReqStruct = "8s8sB80s"
    LoginRespStruct = "B" 
    RecognReqStruct = "19s32sI"
    RecognRespString = "H19sB"
    RecognRespSuccessFmt = "8s16s"
    RecognRespFailedFmt = "B"

    client_info  = {
        "ClientIP" : '',
    }

    __log = None

    live_web_sockets = set()
    server_ioloop = None

    '''
    用来设置该模块能够被tornado server程序调用
    '''
    def check_origin(self, origin):
        return True

    @strictly_func_check
    def initialize(self:object, MsgQueue:dict, cameraip:str)->None:
        self.__log = LoggingQueue.LoggingProducer().getlogger()

        self.__log.info("---------- WebSocket Init Begin ----------")
        self.__log.info(f'WebSocketInit --> message queue : {MsgQueue}')
        #self.__log.info(f'WebSocketInit --> camera ip : {cameraip}')
    
        self.ImageReconQueue = MsgQueue["recv"]
        self.__CameraIP = cameraip
        self.__log.info(f'WebSocketInit --> remote ip : {self.request.remote_ip}')
        self.client_info["ClientIP"] = self.request.remote_ip
        self.BackListQueue = MsgQueue["blackList"]
        self.BackListQueue.put(self.client_info)

        self.server_ioloop = ioloop.IOLoop.current()
        self.__log.info(f'WebSocketInit --> ioloop: {self.server_ioloop}') 
        self.__log.info(f'WebSocketInit --> handler: {self}') 
        self.__log.info("---------- WebSocket Init End----------")

    def open(self):
        self.__log.info(f'WebSocketInit --> New Client has Connected {self}')
        self.ImageHandler = Image.CtrlImage()
        self.objPer = tornado.ioloop.PeriodicCallback(self.__RegisterEvent, 2000)
        self.objPer.start()
        self.pingObj = tornado.ioloop.PeriodicCallback(self.__pingMessage, 10000)
        self.pingObj.start()
        self.set_nodelay(True)
        self.live_web_sockets.add(self)
        self.__log.info(f'WebSocketInit --> self.live_web_sockets: {self.live_web_sockets}')
        pass

#    @strictly_func_check
    @classmethod
    def send_message(cls:object, clientHandler:object, message:bytes):
        removable = set()
        for ws in cls.live_web_sockets:
            if not ws.ws_connection or not ws.ws_connection.stream.socket:
                removable.add(ws)
            else:
                if ws == clientHandler:
                    ws.write_message(message, True)
        for ws in removable:
            cls.live_web_sockets.remove(ws)

    def on_close(self):
        self.objPer.stop()
        self.pingObj.stop()
        if self in self.live_web_sockets:
            self.live_web_sockets.remove(self)
        self.close()
        self.__log.info(f'WebSocketMessage --> Client:{self} Disconnected!')

    @strictly_func_check
    def on_message(self:object, message:bytes)->None:
        MsgType = message[0]
        CompressMode = message[1]
        CompressBody = message[2:]

        #self.__log.info(f'WebSocketMessage --> on message: type:{MsgType} compress:{CompressMode}')
        if MsgType in [LOGIN_REQ, RECOGN_REQ] and CompressMode in [COMPRESS_MODE_NONE, COMPRESS_MODE_BZ2]:
            DecompressBody = ''
            if CompressMode == COMPRESS_MODE_NONE:
                DecompressBody = CompressBody
            elif CompressMode == COMPRESS_MODE_BZ2:
                DecompressBody = bz2.decompress(CompressBody)
            else:
                #不会进入到这里，留作扩展
                pass

            if MsgType == LOGIN_REQ:
                '''对每一个新的节点，在连接之后都会建立一个新的websocket线程，在每个线程内，注册函数都是只调用一次'''
                self.__loginCertification(DecompressBody)
            elif MsgType == RECOGN_REQ:
                '''开启消息队列监视的loop，如果等待回复的消息数量是零，则关闭loop'''
                self.__ClientRecognRequest(DecompressBody)

    def on_pong(self, data):
        self.__count = 0

    def on_ping(self, data):
        pass

    @strictly_func_check
    def __do_unpackdata(self:object, rules:str, data:bytes)->tuple:
        try:
            buf = struct.unpack(rules, data)
            return buf
        except Exception as e:
            self.__log.info(f'__do_unpackdata has error: {e.args}')
            return ''

    @strictly_func_check
    def __generateLoginResp(self:object, mstatus:int)->bytes:
        try:
            fmt = "{}{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, self.LoginRespStruct)
            buf = struct.pack(fmt, LOGIN_RESP, COMPRESS_MODE_NONE, mstatus)
            return buf
        except Exception as e:
            self.__log.error(f'__generateLoginResp has error: {e.args}')
            return ''
        pass

    @strictly_func_check
    def __loginCertification(self:object, msgbytes:bytes)->None:
        fmt = "{}{}".format(self.MsgSizeAlign, self.LoginReqStruct)
        msg = self.__do_unpackdata(fmt, msgbytes)
        #self.__log.info(f'WebSocketMessage --> login message: {msg}')
        if msg:
            if len(msg) == 4:
                cityno = msg[0]
                parkno = msg[1]
                serverno = msg[2]
                token = msg[3]

                tokenret = TokenDef.certify_token(KEY, token)
                if tokenret == False:
                    self.__log.error("WebSocketMessage --> websocker login request:token error")
                    result = self.__generateLoginResp(self.__status_dict["failed"])
                    if result:
                        self.__write_bytes(result)
                    return

                if self.__isRegister == False:
                    sResp = self.__generateLoginResp(self.__status_dict["success"])
                    if sResp:
                        self.__isRegister = True
                        self.objPer.stop()
                        self.__write_bytes(sResp)
                        self.__log.info("WebSocketMessage --> Client login success")

                        citystr = str(cityno, encoding="utf-8")
                        citystr = citystr.replace('\x00', '')
                        citystr = citystr.strip()
                        self.__serverInfo["city"] = citystr

                        parkstr = str(parkno, encoding="utf-8")
                        parkstr = parkstr.replace('\x00', '')
                        parkstr = parkstr.strip()
                        self.__serverInfo["park"] = parkstr
                        
                        self.__serverInfo["server"] = serverno
                else:
                    citystr = str(cityno, encoding="utf-8")
                    citystr = citystr.replace('\x00', '')
                    citystr = citystr.strip()
                    parkstr = str(parkno, encoding="utf-8")
                    parkstr = parkstr.replace('\x00', '')
                    parkstr = parkstr.strip()

                    if self.__serverInfo["city"] == citystr and self.__serverInfo["park"] == parkstr and self.__serverInfo["server"] == serverno:
                        sResp2 = self.__generateLoginResp(self.__status_dict["success"])
                        self.__log.info(f'WebSocketMessage --> Client relogin success')
                    else:
                        if self in self.live_web_sockets:
                            self.live_web_sockets.remove(self)
                        self.close()
                        self.__isRegister = False
                        sResp2 = self.__generateLoginResp(self.__status_dict["failed"])
                        self.__log.info(f'WebSocketMessage --> Client relogin failed')
                    if sResp2:
                        self.__write_bytes(sResp2)
            else:
                sResp3 = self.__generateLoginResp(self.__status_dict["failed"])
                self.__log.info("WebSocketMessage --> Client login message format error")
                if sResp3:
                    self.__write_bytes(sResp3)
        pass 

    '''
    登陆定时函数，在时间内未发送正确的数据则断开连接
    '''
    def __RegisterEvent(self):
        self.objPer.stop()
        self.pingObj.stop()
        if self.__isRegister == False:
            self.__log.info("WebSocketMessage --> websocket client login failed:Timeout")
            if self in self.live_web_sockets:
                self.live_web_sockets.remove(self)
            self.close()

    def __pingMessage(self):
        #self.__log.info(f'send ping message ,count=: {self.__count},  {self}')
        if(self.__count == 5):
            self.pingObj.stop()
            if self in self.live_web_sockets:
                self.live_web_sockets.remove(self)
            self.close()
            return
        self.__count = self.__count + 1
        try:
            self.ping("hello ping")
        except Exception as e:
            self.__log.warn(f'__pingMessage : {e.args}')

    '''
    从本线程消息队列中提取等待处理的请求数据
    数据格式是 message 为 json字符串
    '''
    @strictly_func_check
    def __ClientRecognRequest(self:object, info:bytes)->None:
        #self.__log.info("WebSocketMessage --> Recv Client Data")
        #获取图片数据长度
        #第一个字节表示相机编号长度
        cameraNoLen = info[0]
        realdata = info[1:]
        #1->图片名长度值的说明数字 cameraNoLen->图片名长度具体值
        #19->identify 长度 32->md5长度
        #4->图片长度值的说明数字
        imgsize = len(info) - 1 - cameraNoLen - 19 - 32 - 4;
        #self.__log.info("image size = %d" % size)
        fmt = "{}{}s{}{}s".format(self.MsgSizeAlign, cameraNoLen, self.RecognReqStruct, imgsize)
        #self.__log.info("unpack fmt:%s" % fmt)
        dat = self.__do_unpackdata(fmt, realdata)
        if dat:
            if len(dat) == 5:
                camerano = dat[0]
                bIdentify = dat[1]
                md5str = str(dat[2], encoding="utf-8")
                imagecontent = dat[4]
                #self.__log.info(f'camerano:{camerano} identify:{bIdentify} md5str:{md5str} imgsize:{imgsize}')
                if self.__isRegister == True:
                    #self.__log.info(f'self.server_ioloop={self.server_ioloop}, self=f{self}')
                    self.__log.info(f'websocket send request:ip={self.__CameraIP},camera={camerano},identify={bIdentify},md5={md5str}')
                    sendMsgList = [self.server_ioloop, self, camerano, bIdentify, self.__CameraIP, self.__serverInfo, md5str, imagecontent]
                    self.ImageReconQueue.put(sendMsgList)
                else:
                    mresp5 = self.__genarateRecognRespMsg(camerano, bIdentify, "failed:login", 0, 0)
                    if mresp5:
                        self.__write_bytes(mresp5)
                return
        #如果出错则会走到这里
        #解析数据出现错误，说明数据格式有问题，返回错误信息
        err_camerano = info[1:cameraNoLen]
        err_bIdentify = info[cameraNoLen + 1:cameraNoLen + 1 + 19]
        mresp6 = self.__genarateRecognRespMsg(err_camerano, err_bIdentify, "failed:format", 0, 0)
        if mresp6:
            self.__write_bytes(mresp6)
        pass

    @strictly_func_check
    def __write_bytes(self:object, msg:bytes)->None:
        self.write_message(msg, True)

    @strictly_func_check
    def __genarateRecognRespMsg(self:object, bytecamerano:bytes, byteidentify:bytes, strstatus:str, bytecolor:bytes, byteplate:bytes)->str:
        try:
            if strstatus == "success":
                fmt = "{}{}B{}s{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, len(bytecamerano), self.RecognRespString, self.RecognRespSuccessFmt)
                bytestatus = self.__status_dict[strstatus] 
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, len(bytecamerano), bytecamerano, byteidentify, bytestatus, bytecolor, byteplate)
                return buf
            elif strstatus.startswith("failed:"):
                stalist = strstatus.split(':')
                errcode = self.__errcode_dict[stalist[1]]
                fmt = "{}{}B{}s{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, len(bytecamerano), self.RecognRespString, self.RecognRespFailedFmt)
                bytestatus = self.__status_dict["failed"]
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, len(bytecamerano), bytecamerano, byteidentify, bytestatus, errcode)
                return buf
            elif strstatus in self.__status_dict.keys():
                fmt = "{}{}B{}s{}".format(self.MsgSizeAlign, self.MsgHeadStruct, len(bytecamerano), self.RecognRespString)
                bytestatus = self.__status_dict[strstatus] 
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, len(bytecamerano), bytecamerano, byteidentify, bytestatus)
                return buf
            else:
                self.__log.info(f'__genarateRecognRespMsg: status error:{strstatus}')
                return ''
        except Exception as e:
            self.__log.error(f'__genarateRecognRespMsg: struct error:{e.args}')
            return ''
