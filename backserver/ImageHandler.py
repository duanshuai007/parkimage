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
import random
import tkinter as tk
from PIL import Image, ImageTk

import park_imagerecogn_server 
from Image import CtrlImage
import Config

class ImageHandler:
    '''用来接收websocket线程(handler/ParkHandler)发送过来的图片识别请求信息'''
    rqueue = ''
    '''保存的socket描述符'''
    server = ''
    '''保存的socket连接符'''
    socketconn = ''
    resp_msg = {
        "name" : "",
        "identify" : '',
        "recogn" : {
            "status" : "",
            "color" : "",
            "plate" : ""
        }
    }

    saveImagePath = ""
    curImageUnicode = ''
    waitForImagePlateQueue = ''
    isWaitForResult = False
    WaitTime = 0

    '''图片显示的窗口句柄'''
    root = 0
    '''图片显示窗口上用来显示图片的label'''
    img_label = 0
    '''窗口的尺寸'''
    win_w = 0
    win_h = 0
    '''从配置文件中读取到的本地端口号'''
    local_port = 0
    '''
    图片显示进程运行正常，root_win_flag变为True,否则是False
    '''
    root_win_flag = False
    '''
    Socket线程创建成功，该值变为True
    '''
    socket_flag = False
    '''C 线程与本程序的socket连接已建立标志'''
    socket_connected = False
    '''与websocket进程之间发送图像识别消息的'''
    def __init__(self, msglist):
        qdict = msglist[0]
        '''用来接收websocket线程发送过来的图片识别的请求信息'''
        self.rqueue = qdict["recv"]
        logging.info("ImageHandler recveive image recogn queue:") 
        logging.info(qdict)
        self.local_port = Config.getConfigEnv("CAMERA_SOCKET_PORT")
        self.saveImagePath = Config.getConfigEnv("SAVE_IMAGE_DIR")
        self.socket_flag = self.SocketInit()

    '''
    创建一个新的线程来专门显示图片
    '''
    def ImageShowProcess(self):
        try:
            self.root = tk.Tk()
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost",True)
            self.root.update()
            self.win_w = self.root.winfo_screenwidth()
            self.win_h = self.root.winfo_screenheight()
            self.img_label = tk.Label(self.root)
            self.img_label.pack()
            self.root_win_flag = True

            self.root.mainloop()
        except Exception as e:
            logging.error("no $DISPLAY find, please 'export DISPLAY=:0'")


    def run(self):
        thread = threading.Thread(target = self.ImageRecvRecognProcess, args = [])
        thread.setDaemon(True)
        thread.start()

        thread = threading.Thread(target = self.ImageSendReqProcess, args = [self.rqueue,])
        thread.setDaemon(True)
        thread.start()

        imgThread = threading.Thread(target = self.ImageShowProcess, args = [])
        imgThread.setDaemon(True)
        imgThread.start()

    
    def isRunOK(self):
        time.sleep(1)
        return self.root_win_flag and self.socket_flag


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
        image_resized = self.resize(old_w, old_h, self.win_w, self.win_h, img_open)
        img_jpg = ImageTk.PhotoImage(image_resized)
        self.img_label.config(image = img_jpg)
        self.img_label.image = img_jpg


    def SocketInit(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ipport = ('127.0.0.1', self.local_port)
            self.server.bind(ipport)
            self.server.listen(5)
            return True
        except Exception as e:
            logging.error("locale socket error")
        return False


    def genarateResp(self, mstatus, color, plate):
        self.resp_msg["recogn"]["status"] = mstatus
        self.resp_msg["recogn"]["color"] = color 
        self.resp_msg["recogn"]["plate"] = plate
#return json.dumps(self.resp_msg)
        return self.resp_msg

    def modifyImageName(self, name, color, plate):
        '''sy-wanda-1-1-20190734312.jpg'''
        pathlist = name.split('-')
        rootpath = Config.getConfigEnv("SAVE_IMAGE_DIR")
        imagepath = "{}/{}/{}/{}/{}/".format(rootpath, pathlist[0], pathlist[1], pathlist[2], pathlist[3])

        namelist = name.split('.')
        namehead = namelist[0]
        imagetype = namelist[1]
        if not color and not plate:
            newname = "{}_{}_{}.{}".format(namehead, 'xxx', 'xxxxx', imagetype)
        else:
            newname = "{}_{}_{}.{}".format(namehead, color, plate, imagetype)
        os.rename(imagepath + name, imagepath + newname)

    def modifyImageName(self, name, color, plate):
        '''beijing-wanda-1-0-1565930712886.jpg'''
        pathlist = name.split('-')
        rootpath = Config.getConfigEnv("SAVE_IMAGE_DIR")
        imagepath = "{}/{}/{}/{}/{}/".format(rootpath, pathlist[0], pathlist[1], pathlist[2], pathlist[3])

        namelist = name.split('.')
        namehead = namelist[0]
        imagetype = namelist[1]
        if not color and not plate:
            newname = "{}_{}_{}.{}".format(namehead, 'xxx', 'xxxxx', imagetype)
        else:
            newname = "{}_{}_{}.{}".format(namehead, color, plate, imagetype)
        os.rename(imagepath + name, imagepath + newname)


    def ImageSendReqProcess(self, r):
        while True:
            if self.isWaitForResult == False and self.socket_connected == True:
                if not r.empty():   
                    msg = r.get()
                    self.waitForImagePlateQueue = msg[0]
                    self.resp_msg["name"] = msg[1]
                    self.resp_msg["identify"] = msg[2]
                    self.curImageUnicode = str(random.randint(100000, 999999))
                    logging.info("The name of the image waiting to be recogntion: %s" % self.resp_msg["name"] )

                    if self.socketconn:    
                        #name=city-park-server-camera-time.jpg
                        dirlist = self.resp_msg["name"].split('-')
                        path = "%s/%s/%s/%s/%s/" % (self.saveImagePath, dirlist[0], dirlist[1], dirlist[2], dirlist[3])
                        '''将图片显示在屏幕上'''
                        #logging.info("dispay image in screen!")
                        #cmd = "eog %s%s -f -w 2>>displayerr.log &" % (path, self.resp_msg["name"])
                        #os.system(cmd)
                        try:
                            self.showImg(path + self.resp_msg["name"])
                            '''
                            向C语言程序发送一条触发信息，用来触发程序控制相机开始识别
                            '''
                            #self.socketconn.send(bytes(self.resp_msg["name"], encoding="utf8"))
                            self.socketconn.send(bytes(self.curImageUnicode, encoding="utf8"))
                            self.isWaitForResult = True
                            self.WaitTime = 0
                        except Exception as e:
                            '''发现图片识别socket连接异常，将该消息重新放回队列中'''
                            r.put(msg)
                            logging.warn("locale socket connect error")
                            logging.warn(e.args)
                            try:
                                self.waitForImagePlateQueue.put(self.genarateResp("recogn pthread connect abnormal", "", ""))
                            except Exception as e:
                                logging.warn(e.args)
                    else:
                        try:
                            '''发现图片识别socket没连接，将该消息重新放回队列'''
                            logging.info("the locale socket conn is null, no client connect")
                            if r.full() == True:
                                logging.info("queue is full")
                            else:
                                r.put(msg)
                            '''
                            致命错误，出现该错误需要服务器重新启动
                            '''
                            self.socket_connected = False
                            self.waitForImagePlateQueue.put(self.genarateResp("recogn pthread no connected", "", ""))
                            tmpdir = os.path.dirname(os.path.abspath(sys.argv[0]))
                            cmd = "/bin/bash %s/cThreadRestart.sh" % tmpdir
                            os.system(cmd)
                        except Exception as e:
                            logging.warn("waitForImagePlateQueue error")
                            logging.warn(e.args)
            time.sleep(0.05)
        
    '''
    循环从消息队列中提取等待处理的信息
    此处等待c程序图片识别完成
    识别成功后/超时后返回成功或失败消息，然后继续下一循环
    '''
    def ImageRecvRecognProcess(self):
        inputs = [self.server, ]
        outputs = []
        while True:
            readable,writeable,exceptional = select.select(inputs, outputs, inputs, 1)
            if not (readable or writeable or exceptional):
                if self.isWaitForResult == True:
                    self.WaitTime = self.WaitTime + 1
                    if self.WaitTime > 5:
                        logging.info("wait for recogn image: %ds...timeout" % self.WaitTime)
                        self.isWaitForResult = False
                        self.WaitTime = 0
                        try:
                            self.waitForImagePlateQueue.put(self.genarateResp("timeout", "", ""))
                            self.modifyImageName(self.resp_msg["name"], '', '')
                            self.curImageUnicode = ""
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
                    self.socket_connected = True
                else:
                    try:
                        recv_data = readsocket.recv(128)
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
                                "identify" : '899id999dsa8d9s8a9',
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
                                '''
                                数据格式：
                                    {
                                        "id":"unicode",
                                        "status":"Ok", //or Failed
                                        "result":"Color:黄,Plate:辽A12345",
                                    }
                                '''
                                recv_data = str(recv_data, encoding="utf-8")
                                #logging.info("recvdata:%s" % recv_data)
                                recvjson = json.loads(recv_data)
                                '''3秒识别失败，5秒识别超时(对应C线程挂了的情况)'''
                                if recvjson["id"] == self.curImageUnicode:
                                    #logging.info("中文:%s" % recv_data)
                                    '''failed表示识别失败'''
                                    if  recvjson["status"] == "fail":
                                        status = "failed"
                                        self.modifyImageName(self.resp_msg["name"], '', '')
                                    else:
                                        status = "success"
                                        reclist = recvjson["result"].split(',')
                                        colorlist = reclist[0].split(':')
                                        color = colorlist[1]
                                        platelist = reclist[1].split(':')
                                        plate = platelist[1]
                                        self.modifyImageName(self.resp_msg["name"], color, plate)
                                    try:
                                        logging.info("Image Recogn has Result, send result to ParkHandler thread")
                                        self.waitForImagePlateQueue.put(self.genarateResp(status, color, plate)) #or failed
                                    except Exception as e:
                                        logging.error("waitForImagePlateQueue error")
                            except Exception as e:
                                logging.error("locale socket connect error")
                                logging.error(e.args)
                                status = "recogn socket error"
                            self.isWaitForResult = False
                        else:
                            self.socketconn = ''
                            self.socket_connected = False
                            logging.error('main socket Client Close!')
                            inputs.remove(conn)
