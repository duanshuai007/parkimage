#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import threading
import time
import logging
import json
import queue
import socket
import select
import os

import server
from Image import CtrlImage

class ImageHandler:
    rqueue = ''
    server = ''
    socketconn = ''
    resp_msg = {"name":"","recogn":{"status":"","color":"","plate":""}}
    '''与websocket进程之间发送图像识别消息的'''
    mid = ""
    def __init__(self, qdict):
        if len(qdict) != 1:
            return 
        '''用来接收websocket线程发送过来的图片识别的请求信息'''
        self.rqueue = qdict["recv"]
        logging.info(qdict)
        self.SocketInit()

    def run(self):
        thread = threading.Thread(target = self.ImageProcess, args = [self.rqueue,])
        thread.setDaemon(True)
        thread.start()

    def SocketInit(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ipport = ('127.0.0.1', 9876)
        self.server.bind(ipport)
        self.server.listen(5)
        return server

    def genarateResp(self, mstatus, color, plate):
        self.resp_msg["recogn"]["status"] = mstatus
        self.resp_msg["recogn"]["color"] = color 
        self.resp_msg["recogn"]["plate"] = plate
        return json.dumps(self.resp_msg)

    '''
    循环从消息队列中提取等待处理的信息
    此处等待c程序图片识别完成
    识别成功后/超时后返回成功或失败消息，然后继续下一循环
    '''
    def ImageProcess(self, r):
        
        inputs = [self.server, ]
        outputs = []
        waitForImagePlateQueue = ''
        isWaitForResult = False
        WaitTime = 0

        while True:
            if isWaitForResult == False:
                if not r.empty():   
                    msg = r.get()
                    waitForImagePlateQueue = msg[0]
                    self.resp_msg["name"] = msg[1]
                    logging.info("recv image name:%s" % self.resp_msg["name"] )

                    if self.socketconn:    
                        dirlist = self.resp_msg["name"].split('-')
                        path = "Picture/%s/%s/%s/%s/" % (dirlist[0], dirlist[1], dirlist[2], dirlist[3])
                        '''将图片显示在屏幕上'''
                        cmd = "eog %s%s -f -w &" % (path, self.resp_msg["name"])
                        os.system(cmd)

                        try:
                            self.socketconn.send(bytes(self.resp_msg["name"], encoding="utf8"))
                            isWaitForResult = True
                            WaitTime = 0
                        except Exception as e:
                            '''发现图片识别socket连接异常，将该消息重新放回队列中'''
                            r.put(msg)
                            logging.warn(e.args)
                            try:
                                waitForImagePlateQueue.put(self.genarateResp("recogn pthread connect abnormal", "", ""))
                            except Exception as e:
                                logging.warn(e.args)
                    else:
                        try:
                            '''发现图片识别socket没连接，将该消息重新放回队列'''
                            logging.info("reput msg[%s] into queue!")
                            logging.info(msg)
                            if r.full() == True:
                                logging.info("queue is full")
                            else:
                                r.put(msg)
                            waitForImagePlateQueue.put(self.genarateResp("recogn pthread no connected", "", ""))
                        except Exception as e:
                            logging.warn("this is error")
                            logging.warn(e.args)
                else:
                    '''logging.info("queue is empty")'''
                    pass
                        
            readable,writeable,exceptional = select.select(inputs, outputs, inputs, 1)
            if not (readable or writeable or exceptional):
                if isWaitForResult == True:
                    logging.info("wait for %d..." % WaitTime)
                    WaitTime = WaitTime + 1
                    if WaitTime > 15:
                        isWaitForResult = False
                        WaitTime = 0
                        try:
                            waitForImagePlateQueue.put(self.genarateResp("timeout", "", ""))
                        except Exception as e:
                            logging.warn(e.args)
                continue
            for readsocket in readable:
                #读取从C程序发来过来的车辆进出的信息
                if readsocket is self.server:
                    conn,addr = self.server.accept()
                    self.socketconn = conn
                    logging.info('localhost socket has new connect')
                    conn.setblocking(False)
                    inputs.append(conn)
                else:
                    try:
                        recv_data = readsocket.recv(1024)
                        '''logging.info('recv %s' % recv_data)'''
                    except Exception as e:
                        logging.error(e.args)
                    else:
                        if recv_data:
                            #接收到c程序发来的消息，进行处理
                            '''识别完成
                            接收到的socket data数据格式
                            "Color:黄,Plate:辽A12345" 数据类型为bytes 需要转换为str
                            返回的信息的数据格式
                            {
                                "name":"imagename",
                                "recogn":{
                                    "status":"success",
                                    "color":"黄",
                                    "plate":"辽A12345",
                                }
                            }
                            '''
                            status = ""
                            color = ""
                            plate = ""
                            try:
                                recv_data = str(recv_data, encoding="utf-8")
                                logging.info("中文:%s" % recv_data)
                                '''failed表示识别失败'''
                                if  recv_data == "Recogn Failed":   
                                    status = "failed"
                                else:
                                    status = "success"
                                    reclist = recv_data.split(',')
                                    colorlist = reclist[0].split(':')
                                    color = colorlist[1]
                                    platelist = reclist[1].split(':')
                                    plate = platelist[1]
                            except Exception as e:
                                logging.warn(e.args)
                                status = "recogn socket error"

                            try:
                                waitForImagePlateQueue.put(self.genarateResp(status, color, plate)) #or failed
                            except Exception as e:
                                logging.warn(e.args)
                            isWaitForResult = False
                        else:
                            logging.warn('Client Close!')
                            inputs.remove(conn)
        
