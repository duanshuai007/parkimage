#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import threading
import time
import json
import queue
import socket
import select
import os
import subprocess
import sys
import random
import tkinter as tk
import copy
import re
import struct

from PIL import Image, ImageTk
from tornado import ioloop, web

import Config
import TheQueue
import LoggingHelper
from Image import CtrlImage
from WebSocketThread import WebSocketThread

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

class ImageShow():
    '''用来接收websocket线程(handler/ParkHandler)发送过来的图片识别请求信息'''
    rqueue = ''
    '''保存的socket描述符'''
    server = ''
    __epoll = ''
    __connecttions = {}

    __applyCameraReq = {
        "type":"apply",
        "number":0,
    }

    __applyCameraResp = {
        "type" : "apply",
        "number" : 0,
        "info":{
            "camera0":{
                "ip":"",
                "port":0
            },
            "camera1":{
                "ip":"",
                "port":0
            },
        },
    }

    __RecognReq = {
        "type":"request",
        "info" : {
            "unicode" : "",
            "cameraip" : "",
        }
    }
    '''    
        RecognResp = {
            "type" : "response",
            "info" : {
                "unicode" : "",
                "cameraip" : "",
                "result" : {
                    "status" : "",
                    "color" : "",
                    "plate" : "",
                }
            }
        }
        
        heartReqResp = {
            "type":"heart",
            "cameraip":'',
    }'''
    
    __cameraList = []

    __cameraDictInfo = {
        "cameraip" : "",
        "inUse" : False,
        "Window" : {
            "no" : 0,
            "imageLabel" : None,
            "width" : 0,
            "height" : 0,
        },
        "city" : '',
        "park" : '',
        "server" : '',
        "camerano" : 0,
        "identify" : "",
        "unicode" : "",
        "webSocketIOLoop" : None,
        "webSocketHandler" : None,
        "threadLock" : None,
        "waitTimeCount" : 0,
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
    Status  1Byte       0:失败 1:成功

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
    RecognReqStruct = "H19s32sI"
    RecognRespString = "H19sB"
    RecognRespSuccessFmt = "8s16s"
    RecognRespFailedFmt = "B"

    '''
    该程序需要区分出上下两个屏幕与相机的对应关系
    '''
    __saveImagePath = ''
    __cameraCount = 0
    __mode = ''

    __DelayCameraDictList = []
    config = None

    __socket_port = 0
    __socket_ip = '127.0.0.1'
    __socket_connection_alive = False
    __socket_timer = 0

    __log = None 
    __ImageHandler = None

    def __init__(self, MsgQueue):

        self.__ImageHandler = CtrlImage()
        '''用来接收websocket线程发送过来的图片识别的请求信息'''
        self.rqueue = MsgQueue["recv"]
        self.config = Config.Config()

        logfile = self.config.get('CONFIG', 'LOGFILE')
        self.__log = LoggingHelper.LoggingProducer()

        self.__socket_port = int(self.config.get("CAMERA", "SOCKET_PORT"), 10)
        self.__socket_connection_alive = self.__connect_to_server()
        self.__saveImagePath = self.config.get("CONFIG", "SAVE_IMAGE_DIR")
        self.__mode = self.config.get("CAMERA", "CLIENT_CAMERA_MODE")

        self.__log.info(f'SocketInit ==> Apply Camera Mode:{self.__mode}')
        self.__log.info(f'SocketInit ==> ImagePath:{self.__saveImagePath}')
        self.__log.info(f'SocketInit ==> Camera Thread Socket Port:{self.__socket_port}')
        pass

    def __connect_to_server(self):
        ip_port = (self.__socket_ip, self.__socket_port)
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect(ip_port)
            return True
        except Exception as e:
            self.__log.error(f'SocketInit ==> __connect_to_server error:{e.args}')
            return False
    '''
    获取socket数据的有效部分
    这是python程序与C程序之间的socket数据格式
    数据格式<MessageHead>message<MessageTail>
    '''
    def __getMessageBody(self, msg):
        msg = msg.replace('\n', '')
        msg = msg.replace('\t', '')
        msg = msg.strip('\x00')
        reg = r'\<MessageHead\>([.*\S]*?)\<MessageTail\>'
        rules = re.compile(reg)
        realmsglist = re.findall(rules, msg)
        return realmsglist

    '''根据屏幕尺寸设置图片的大小'''
    def __resize(self, w, h, w_box, h_box, pil_image):
        '''
        __resize a pil_image object so it will fit into
        a box of size w_box times h_box, but retain aspect ratio
        对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例
        '''
        f1 = 1.0 * w_box / w # 1.0 forces float division in Python2
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)

    def __showImg(self, infodict):
        '''根据名字找到图片的位置'''
        try:
            name = self.__genarateImageSaveName(infodict)
            namestr = "{}/{}/{}/{}/{}/{}".format(self.__saveImagePath, infodict["city"], infodict["park"], infodict["server"], infodict["camerano"], name)
            #self.__log.info("Ready Show Image: %s" % namestr)

            img_open = Image.open(namestr)
            old_w, old_h = img_open.size
            width = int(infodict["Window"]["width"], 10)
            height = int(infodict["Window"]["height"], 10)
            image_resized = self.__resize(old_w, old_h, width, height, img_open)
            img_jpg = ImageTk.PhotoImage(image_resized)
            infodict["Window"]["imageLabel"].config(image = img_jpg)
            infodict["Window"]["imageLabel"].image = img_jpg
        except Exception as e:
            self.__log.error(f'SocketInit ==> __showImg has error:{e.args}')
    ''' 
    创建一个新的线程来专门显示图片
    '''
    def __WindowShowThread(self):
        try:
            '''创建根窗口并进行隐藏'''
            root = tk.Tk()
            root.withdraw()
            '''创建子窗口'''
            for camera in self.__cameraList:
                top = tk.Toplevel(root)
                top.attributes("-fullscreen", True)
                top.attributes("-topmost",True)
                width = int(camera["Window"]["width"], 10)
                height = int(camera["Window"]["width"], 10)
                pos = int(camera["Window"]["no"]) * width
                size = "{}x{}+{}+{}".format(width, height, pos, 0)
                top.geometry(size)
                img_label = tk.Label(top)
                img_label.pack()
                camera["Window"]["imageLabel"] = img_label
                self.__log.info("SocketInit ==> Create New TopLevel:Size = %s" % size)
            
            root.update()
            root.mainloop()
        except Exception as e:
            self.__log.error(f'SocketInit ==> __WindowShowThread error:{e.args}')

    '''
    每次使用前需要向服务器申请可以使用的相机数
    在申请到相机之后直接创建tkinter imagelabel
    '''
    def __applyCamera(self):
        try:
            self.__applyCameraReq["number"] = self.config.get("CAMERA", "CAMERA_APPLY_MODE")
            self.__log.info("SocketInit ==> Apply Camera Mode=%s" % self.__applyCameraReq["number"])
            msg = json.dumps(self.__applyCameraReq)
            self.server.send(bytes(msg, encoding="utf-8"))
            '''
            阻塞等待数据
            '''
            recbytes = self.server.recv(1024)
            recv_data = str(recbytes, encoding="utf-8")
            itemlist = self.__getMessageBody(recv_data)
            '''解析接收到的信息，将相机设备信息加入到列表中'''
            if itemlist:
                if itemlist[0]:
                    jsonmsg = json.loads(itemlist[0])

                    cameraConfigList = []
                    rlist = self.config.get("CAMERA", "CAMERA_IP_AND_SCREEN").split(',')
                    for item in rlist:
                        rrlist = item.split('-')
                        cameraConfigList.append(rrlist)
        
                    for val in jsonmsg["info"].keys():
                        dictmsg = copy.deepcopy(self.__cameraDictInfo)
                        dictmsg["cameraip"] = jsonmsg["info"][val]["ip"]
                        dictmsg["threadLock"] = threading.Lock()
                        dictmsg["inUse"] = False
                        for item in cameraConfigList:
                            if dictmsg["cameraip"] == item[0]:
                                dictmsg["Window"]["no"] = item[1]
                                Resolution = item[2].split('*')
                                dictmsg["Window"]["width"] = Resolution[0]
                                dictmsg["Window"]["height"] = Resolution[1]
                        self.__cameraList.append(dictmsg)

            self.__log.info(f'SocketInit ==> get camera:{self.__cameraList}')
            return len(self.__cameraList)
        except Exception as e:
            self.__log.error(f'SocketInit ==> __applyCamera error:{e.args}')
            return 0

    def __reApplyCamera(self):
        #服务端C程序重启后需要重新发送申请相机的命令
        try:
            self.__applyCameraReq["number"] = self.config.get("CAMERA", "CAMERA_APPLY_MODE")
            self.__log.info("SocketInit ==> reApply camera mode=%s" % self.__applyCameraReq["number"])
            msg = json.dumps(self.__applyCameraReq)
            self.server.send(bytes(msg, encoding="utf-8"))
            '''    阻塞等待数据   '''
            recbytes = self.server.recv(1024)
            recv_data = str(recbytes, encoding="utf-8")
            itemlist = self.__getMessageBody(recv_data)
            '''解析接收到的信息，将相机设备信息加入到列表中'''
            self.__log.info(f'SocketInit ==> reApply recv camera: {itemlist}')
            if itemlist:
                if itemlist[0]:
                    jsonmsg = json.loads(itemlist[0])
                    iplist = []
                    for key in jsonmsg["info"].keys():
                        iplist.append(jsonmsg["info"][key]["ip"])
                    for camera in self.__cameraList:
                        if camera["cameraip"] not in iplist:
                            self.__cameraList.remove(camera)
        except Exception as e:
            self.__log.error(f'SocketInit ==> __reApplyCamera error:{e.args}')
        pass

    def __getIdleCamera(self):
        result = []
        for item in self.__cameraList:
            if item["inUse"] == False and item["cameraip"] != '':
                result.append(item)
        if not result:
            return ''
        else:
            return random.choice(result)

    def __getMatchCamera(self, ip):
        for item in self.__cameraList:
            if item["cameraip"] == ip:
                if item["inUse"] == False and item["cameraip"] != '':
                    return item
        return ''

    def __ClientProcessData(self, recQueue, cameraDict, recognMsg) -> bool:
        
        WebSocketIOLoop = recognMsg[0]
        WebSocketHandler = recognMsg[1]
        camerano = recognMsg[2]
        identify_bytes = recognMsg[3]
        cameraip = recognMsg[4]
        serverinfo = recognMsg[5]
        md5_str  = recognMsg[6]
        imagecontent = recognMsg[7]
        
        cameraDict["threadLock"].acquire()
        try:
            cameraDict["webSocketHandler"] = WebSocketHandler
            cameraDict["webSocketIOLoop"] = WebSocketIOLoop
            cameraDict["city"] = serverinfo["city"]
            cameraDict["park"] = serverinfo["park"]
            cameraDict["server"] = serverinfo["server"]
            cameraDict["camerano"] = camerano
            cameraDict["identify"] = identify_bytes

            if self.__ImageHandler.checkMd5(imagecontent, md5_str) == False:
                self.__log.error(f'Camera:[{cameraDict["cameraip"]}] ==> Websockt Client Message: Md5 error')
                self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "failed:md5", '', '')
                return False

            name = self.__genarateImageSaveName(cameraDict)
            if not name:
                self.__log.error(f'Camera:[{cameraDict["cameraip"]}] ==> Websockt Client Message: Genarate Name Failed!')
                self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "failed:name", '', '')
                return False

            if self.__ImageHandler.save(name, imagecontent) == False:
                self.__log.error(f'Camera:[{cameraDict["cameraip"]}] ==> Websockt Client Message: Save Image Failed!')
                self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "failed:save", '', '')
                return False

            cameraDict["waitTimeCount"] = int(time.time() * 1000) + 5000
            cameraDict["inUse"] = True
            cameraDict["unicode"] = str(random.randint(100000, 999999))
        finally:
            cameraDict["threadLock"].release()

        self.__showImg(cameraDict)

        self.__RecognReq["info"]["cameraip"] = cameraDict["cameraip"]
        self.__RecognReq["info"]["unicode"] = cameraDict["unicode"]
        sendstring = json.dumps(self.__RecognReq)
        self.__log.info(f'Camera:[{cameraDict["cameraip"]}] ==> Send Recogn Request To CThread: {sendstring}')
        try:
            if self.__socket_connection_alive == True:
                self.server.send(bytes(sendstring, encoding="utf-8"))
                if self.__mode == "PREEMPTION":
                    tmp = self.__getIdleCamera()
                    if not tmp:
                        self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "stop", '', '')
                    else:
                        self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "goon", '', '')
                elif self.__mode == "MATCH":
                    self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "ready", '', '')
        except Exception as e:
            self.__DelayCameraDictList.append(recognMsg)
            self.__log.error(f'Camera:[{cameraDict["cameraip"]}] ==> __ClientProcessData error occurs:{e.args}')
            self.__WebSocketSendResp(WebSocketIOLoop, WebSocketHandler, camerano, identify_bytes, "failed:recogn pthread", '', '')
        pass


    '''
    查询是否有空闲的相机和显示器，如果有则查看是否有等待识别的图片
    进行显示，并向C程序发送相机触发信息
    '''
    def __ImageSendReqProcess(self, r):
        localTimer = 0
        while True:
            localTimer = int(time.time() * 1000)
            cameraDict = self.__getIdleCamera()
            if cameraDict:
                #查看这个延时列表中是否有等待识别的信息
                if len(self.__DelayCameraDictList) == 0:
                    if not r.empty():
                        msg = r.get()
                        cameraip = msg[4]
                         #抢占模式使用所有可以使用的设备
                        if self.__mode == "PREEMPTION":
                            self.__log.info(f'Camera:[{cameraip}] ==> mode:[PREEMPTION] send:{msg[0],msg[1],msg[2],msg[3],msg[4],msg[5]}')
                            self.__ClientProcessData(r, cameraDict, msg)
                       #匹配模式仅仅使用IP相同的设备
                        elif self.__mode == "MATCH":
                            self.__log.info(f'Camera:[{cameraip}] ==> mode:[MATCH] send:{msg[0],msg[1],msg[2],msg[3],msg[4],msg[5]}')
                            if cameraip == cameraDict["cameraip"]:
                                self.__ClientProcessData(r, cameraDict, msg)
                            else:
                                self.__DelayCameraDictList.append(msg)
                        del msg
                else:
                    #发现有等待识别的消息
                    msg = self.__DelayCameraDictList.pop(0)
                    cameraip = msg[4]
                    #发现有新的消息，返回拒绝，扔掉改消息
                    if not r.empty():
                        tmp = r.get()
                        if cameraip == tmp[4]:
                            self.__WebSocketSendResp(tmp[0], tmp[1], tmp[2], tmp[3], "refuse", '', '')
                            self.__log.warn(f'Camera:[{cameraip}] ==> __ImageSendReqProcess refuse[1]!')
                        else:
                            self.__DelayCameraDictList.append(tmp)
                        del tmp

                    #如果消息中的ip与当前设备ip一致，则进行处理，否则继续放回延时列表中
                    self.__log.info(f'Camera:[{cameraip}] ==> dev ip : {cameraDict["cameraip"]}')
                    camera = self.__getMatchCamera(cameraip)
                    if camera:
                        self.__ClientProcessData(r, cameraDict, msg)
                    else:
                        self.__WebSocketSendResp(msg[0], msg[1], msg[2], msg[3], "refuse", '', '')
                        self.__log.warn(f'Camera:[{cameraip}] ==> __ImageSendReqProcess refuse[2]!')
                    del msg
            else:
                #设备全忙，返回拒绝信息
                if not r.empty():
                    tmp = r.get()
                    self.__WebSocketSendResp(tmp[0], tmp[1], tmp[2], tmp[3], "refuse", '', '')
                    self.__log.warn(f'Camera:[{tmp[4]}] ==> __ImageSendReqProcess refuse[3]!')
                    del tmp

            for camera in self.__cameraList:
                if camera["inUse"] == True:
                    if camera["waitTimeCount"] < localTimer:
                        self.__log.warn(f'Camera:[{camera["cameraip"]}] ==> wait for recogn timeout:identify={camera["identify"]} unicode={camera["unicode"]}')
                        if self.__socket_connection_alive == True:
                            self.__WebSocketSendResp(camera["webSocketIOLoop"], camera["webSocketHandler"], camera["camerano"], camera["identify"], "failed:timeout", '', '')
                        else:
                            self.__WebSocketSendResp(camera["webSocketIOLoop"], camera["webSocketHandler"], camera["camerano"], camera["identify"], "failed:recogn pthread", '', '')
                        self.__modifyImageName(camera, '', '')
                        camera["threadLock"].acquire()
                        camera["inUse"] = False
                        camera["waitTimeCount"] = localTimer
                        camera["webSocketHandler"] = None
                        camera["identify"] = 0
                        camera["unicode"] = 0
                        camera["threadLock"].release()

            if self.__socket_connection_alive == False:
                if self.__socket_timer < localTimer:
                    self.__socket_timer = localTimer + 5000
                    if self.server:
                        self.server.close()
                        self.server = None
                    self.__connecttions = {}
                    self.__socket_connection_alive = self.__connect_to_server()
                    if self.__socket_connection_alive == True:
                        self.__reApplyCamera()
                        self.__log.info(f'SocketInit ==> reconnect camera list : {self.__cameraList}')
                        self.__epoll.register(self.server.fileno(), select.EPOLLIN | select.EPOLLRDHUP | select.EPOLLHUP)
                        self.__connecttions[self.server.fileno()] = self.server

            time.sleep(0.01)
        pass

    '''
    处理C程序发送过来的识别结果信息和心跳信息等等
    '''
    def __socketRecvThread(self):
        self.__epoll = select.epoll()
        self.__epoll.register(self.server.fileno(), select.EPOLLIN | select.EPOLLRDHUP | select.EPOLLHUP)
        self.__connecttions = {}
        '''
        epoll.modify(fileno, select.EPOLLOUT) 设置对应句柄可写
        epoll.modify(fileno, 0) 设置对应句柄不干任何事，一般后面会接connections[fileno].shutdown(socket.SHUT_RDWR)
        '''
        self.__connecttions[self.server.fileno()] = self.server
        try:
            while True:
                events = self.__epoll.poll(timeout=0.01)
                if not events:
                    pass
                for fileno, event in events:
                    if event & select.EPOLLRDHUP:
                        self.__log.error(f'EPOLL ERROR ==> EPOLLRDHUP')
                        self.__epoll.unregister(fileno)
                        self.__socket_timer = int(time.time() * 1000) + 5000
                        self.__socket_connection_alive = False
                        pass        
                    elif event & select.EPOLLIN:
                        try:
                            dat = self.__connecttions[fileno].recv(1024)
                            strdat = str(dat, encoding="utf-8")
                            itemlist = self.__getMessageBody(strdat)
                            if itemlist:
                                for item in itemlist:
                                    jsonmsg = json.loads(item)
                                    if jsonmsg["type"] == "heart":
                                        #self.__log.info("socketClient recv heart and send keep alive: %s" % item)
                                        self.__connecttions[fileno].send(bytes(item, encoding="utf-8"))
                                    elif jsonmsg["type"] == "response":
                                        ip = jsonmsg["info"]["cameraip"]
                                        self.__log.info(f'Camera:[{ip}] ==> socketClient Send RecognMessage to Client: {item}')
                                        '''根据相机ip找到对应的设备信息'''
                                        for camera in self.__cameraList:
                                            if ip == camera["cameraip"] and camera["inUse"] == True:
                                                '''对比uniconde是否相同'''
                                                if jsonmsg["info"]["unicode"] == camera["unicode"]:
                                                    if jsonmsg["info"]["result"]["status"] == "fail":
                                                        #modify picture name to xxx_xxxx
                                                        self.__modifyImageName(camera, '', '')
                                                    else:
                                                        #modify picture name to real name
                                                        self.__modifyImageName(camera, jsonmsg["info"]["result"]["color"], jsonmsg["info"]["result"]["plate"]) 
                                                    self.__WebSocketSendResp(camera["webSocketIOLoop"], camera["webSocketHandler"], camera["camerano"], camera["identify"], jsonmsg["info"]["result"]["status"], jsonmsg["info"]["result"]["color"], jsonmsg["info"]["result"]["plate"])
                                                else:
                                                    pass
                                                '''相机识别完成(不论成功还是失败),释放设备'''
                                                camera["threadLock"].acquire()
                                                camera["inUse"] = False
                                                camera["webSocketHandler"] = None
                                                camera["camerano"] = 0
                                                camera["identify"] = 0
                                                camera["unicode"] = 0
                                                camera["waitTimeCount"] = int(time.time() * 1000)
                                                camera["threadLock"].release()
                        except socket.error:
                            self.__log.error(f'EPOLL ERROR ==> except socket.error')
                            pass
                    elif event & select.EPOLLOUT:
                        self.__log.info(f'EPOLL ERROR ==> select.EPOLLOUT')
                        pass
                    elif event & select.EPOLLERR:
                        self.__log.info(f'EPOLL ERROR ==> select.EPOLLERR')
                        pass
                    elif event & select.EPOLLHUP:
                        self.__epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
                        self.__log.info(f'EPOLL ERROR ==> select.EPOLLHUP')
        except Exception as e:
            self.__log.error(f'EPOLL ERROR ==> except {e.args}')
        finally:
            self.__log.error("EPOLL ERROR ==> finally!!!!")
            self.__epoll.unregister(self.server.fileno())
        pass

    def run(self):
        '''
        首先需要申请相机，根据申请到的相机数量创建tkinter图片显示器
        '''        
        self.__cameraCount = self.__applyCamera()
        self.__log.info("SocketInit ==> we got %d camera!" % self.__cameraCount)
        if self.__cameraCount == 0:
            self.server.close()
            return             
        
        t = threading.Thread(target = self.__WindowShowThread, args = [])
        t.setDaemon(False)
        t.start()

        t = threading.Thread(target = self.__ImageSendReqProcess, args = [self.rqueue,])
        t.setDaemon(False)
        t.start()
    
        t = threading.Thread(target = self.__socketRecvThread, args = [])
        t.setDaemon(False)
        t.start()
        pass
    

    def __modifyImageName(self, cameraDict, color, plate):
        '''beijing-wanda-1-0-1565930712886.jpg'''
        try:
            imagepath = self.config.get("CONFIG", "SAVE_IMAGE_DIR")
            imagepath = "{}/{}/{}/{}/{}/".format(imagepath, cameraDict["city"], cameraDict["park"], cameraDict["server"], cameraDict["camerano"])
            name = self.__genarateImageSaveName(cameraDict)

            imagetype = 'jpg'
            strIdentify = str(cameraDict["identify"], encoding="utf-8")
            strIdentify = strIdentify[0:13]
            if not color and not plate:
                newname = "{}-{}-{}-{}-{}_{}_{}.{}".format(cameraDict["city"], cameraDict["park"], cameraDict["server"], cameraDict["camerano"], strIdentify, 'xxx', 'xxxxx', imagetype)
            else:
                newname = "{}-{}-{}-{}-{}_{}_{}.{}".format(cameraDict["city"], cameraDict["park"], cameraDict["server"], cameraDict["camerano"], strIdentify, color, plate, imagetype)
            #self.__log.info(f'__modifyImageName rename: oldname:{name}, newname:{newname}')
            os.rename(imagepath + name, imagepath + newname)
        except Exception as e:
            self.__log.error(f'__modifyImageName has error:{e.args}')


    def __WebSocketSendResp(self, websocketIOLoop, websocketHandler, bCameraNo, bIdentify, strStatus, byteColor, bytePlate):
        resp_bytes = self.__genarateRecognRespMsg(bCameraNo, bIdentify, strStatus, byteColor, bytePlate)
        if resp_bytes:
            websocketIOLoop.add_callback( WebSocketThread.send_message, websocketHandler, resp_bytes)
        pass


    '''生成发送给websocket client的响应数据'''
    def __genarateRecognRespMsg(self, bytecamerano, byteidentify, strstatus, color, plate):
        try:
            if strstatus == "success":
                fmt = "{}{}{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, self.RecognRespString, self.RecognRespSuccessFmt)
                bytestatus = self.__status_dict[strstatus]
                bytecolor = bytes(color, encoding="utf-8")
                byteplate = bytes(plate, encoding="utf-8")
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, bytecamerano, byteidentify, bytestatus, bytecolor, byteplate)
                return buf
            elif strstatus.startswith("failed:"):
                stalist = strstatus.split(':')
                errcode = self.__errcode_dict[stalist[1]]
                fmt = "{}{}{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, self.RecognRespString, self.RecognRespFailedFmt)
                bytestatus = self.__status_dict["failed"]
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, bytecamerano, byteidentify, bytestatus, errcode)
                return buf
            elif strstatus in self.__status_dict.keys():
                fmt = "{}{}{}".format(self.MsgSizeAlign, self.MsgHeadStruct, self.RecognRespString)
                bytestatus = self.__status_dict[strstatus]
                buf = struct.pack(fmt, RECOGN_RESP, COMPRESS_MODE_NONE, bytecamerano, byteidentify, bytestatus)
                return buf
            else:
                self.__log.info(f'__genarateRecognRespMsg: status error:{strstatus}')
                return ''
        except Exception as e:
            self.__log.error(f'__genarateRecognRespMsg: struct error:{e.args}')
            return ''

    def __genarateImageSaveName(self, cameraDict):
        #timestamp = int(time.time() * 1000)
        try:
            #这里不能加入编码格式，否则再Image中调用os.path.exists 时会抛出Embedded NUL character错误
            strIdentify = str(cameraDict["identify"], encoding="utf-8")
            name = "{}-{}-{}-{}-{}.jpg".format(cameraDict["city"], cameraDict["park"], cameraDict["server"], cameraDict["camerano"], strIdentify[0:13])
            return name
        except Exception as e:
            self.__log.error(f'__genarateImageSaveName:{e.args}')
            return ''

if __name__ == "__main__":
    TheQueue.init()
    dicts = TheQueue.get()
    client = ImageShow([dicts, ])
    client.run()

