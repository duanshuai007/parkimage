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
import sys
import tkinter as tk
from PIL import Image, ImageTk

import server
from Image import CtrlImage
import Config

class ImageHandler:
    rqueue = ''
    server = ''
    socketconn = ''
    resp_msg = {"name":"","recogn":{"status":"","color":"","plate":""}}
    saveImagePath = ""

    root = 0
    img_label = 0
    win_w = 0
    win_h = 0
    local_port = 0
    '''与websocket进程之间发送图像识别消息的'''
    mid = ""
    def __init__(self, msglist):
        qdict = msglist[0]
        '''用来接收websocket线程发送过来的图片识别的请求信息'''
        self.rqueue = qdict["recv"]
        logging.info(qdict)
        self.local_port = Config.getConfigEnv("CAMERA_SOCKET_PORT")
        self.saveImagePath = Config.getConfigEnv("SAVE_IMAGE_DIR")
        self.SocketInit()

    '''
    创建一个新的线程来专门显示图片
    '''
    def ImageShowProcess(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost",True)
        self.root.update()
        self.win_w = self.root.winfo_screenwidth()
        self.win_h = self.root.winfo_screenheight()
        self.img_label = tk.Label(self.root)
        self.img_label.pack()

        self.root.mainloop()

    def run(self):
        thread = threading.Thread(target = self.ImageProcess, args = [self.rqueue,])
        thread.setDaemon(True)
        thread.start()

        imgThread = threading.Thread(target = self.ImageShowProcess, args = [])
        imgThread.setDaemon(True)
        imgThread.start()

    '''根据屏幕尺寸设置图片的大小'''
    def resize(self, w, h, w_box, h_box, pil_image):
        '''
        resize a pil_image object so it will fit into
        a box of size w_box times h_box, but retain aspect ratio
        对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例
        '''
        f1 = 1.0 * w_box / w # 1.0 forces float division in Python2
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)

    def showImg(self, namestr):
        logging.info("show img name:%s" % namestr)
        img_open = Image.open(namestr)
        old_w, old_h = img_open.size
        logging.info("windows width=%d, height=%d" % (self.win_w, self.win_h))
        image_resized = self.resize(old_w, old_h, self.win_w, self.win_h, img_open)
        img_jpg = ImageTk.PhotoImage(image_resized)
        self.img_label.config(image = img_jpg)
        self.img_label.image = img_jpg

    def SocketInit(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ipport = ('127.0.0.1', self.local_port)
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
                    logging.info("The name of the image waiting to be identified: %s" % self.resp_msg["name"] )

                    if self.socketconn:    
                        dirlist = self.resp_msg["name"].split('-')
                        path = "%s/%s/%s/%s/%s/" % (self.saveImagePath, dirlist[0], dirlist[1], dirlist[2], dirlist[3])
                        '''将图片显示在屏幕上'''
                        logging.info("dispay image in screen!")
                        #cmd = "eog %s%s -f -w 2>>displayerr.log &" % (path, self.resp_msg["name"])
                        #os.system(cmd)
                        self.showImg(path + self.resp_msg["name"])

                        try:
                            self.socketconn.send(bytes(self.resp_msg["name"], encoding="utf8"))
                            isWaitForResult = True
                            WaitTime = 0
                        except Exception as e:
                            '''发现图片识别socket连接异常，将该消息重新放回队列中'''
                            r.put(msg)
                            logging.warn("locale socket connect error")
                            logging.warn(e.args)
                            try:
                                waitForImagePlateQueue.put(self.genarateResp("recogn pthread connect abnormal", "", ""))
                            except Exception as e:
                                logging.warn(e.args)
                    else:
                        try:
                            '''发现图片识别socket没连接，将该消息重新放回队列'''
                            '''logging.info("reput msg[%s] into queue!")
                            logging.info(msg)
                            '''
                            logging.info("the locale socket conn is null, no client connect")
                            if r.full() == True:
                                logging.info("queue is full")
                            else:
                                r.put(msg)
                            waitForImagePlateQueue.put(self.genarateResp("recogn pthread no connected", "", ""))
                        except Exception as e:
                            logging.warn("waitForImagePlateQueue error")
                            logging.warn(e.args)
                        
            readable,writeable,exceptional = select.select(inputs, outputs, inputs, 1)
            if not (readable or writeable or exceptional):
                if isWaitForResult == True:
                    logging.info("wait for recogn image: %ds..." % WaitTime)
                    WaitTime = WaitTime + 1
                    if WaitTime > 3:
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
                                logging.warn("locale socket connect error")
                                status = "recogn socket error"

                            try:
                                logging.info("Image Recognition OK, send result to ParkHandler thread")
                                waitForImagePlateQueue.put(self.genarateResp(status, color, plate)) #or failed
                            except Exception as e:
                                logging.warn("waitForImagePlateQueue error")
                            isWaitForResult = False
                        else:
                            self.socketconn = ''
                            logging.warn('main socket Client Close!')
                            inputs.remove(conn)
        
