#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import websocket
import json
import time
import base64
import hashlib
import os
import sys
import logging
import threading
import random
import ssl
import bz2
import struct

class Client:
    
    wss = ''
    globalWait = False
    token = 'MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ='

    def __init__(self, path):
        self.path = path + '2'
        logging.info("set path = %s" % path)
        pass

    def login(self):
        logging.info("login")
        cityno = '10'
        parkno = '6'
        serverno = '5'
        self.wss = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        '''客户端首先需要登陆到服务器上'''        
        self.wss.connect("wss://192.168.200.210:4000/park1")
        citybytes = bytes('beijing', encoding="utf-8")
        parkbytes = bytes('wanda',encoding="utf-8")
        tokenbytes = bytes(self.token, encoding="utf-8")
        sendbuff = struct.pack( ">BB8s8sB80s", 1, 0,  citybytes, parkbytes, 6, tokenbytes)
        print("sendbuff:" , sendbuff)
        self.wss.send_binary(sendbuff)
        '''
        验证登陆是否成功
        '''
        recv = self.wss.recv_frame()
        print("recv login response:")
        print(recv)
        return True

    def run(self):
        sthread = threading.Thread(target = self.sendImagePthread, args = [])
        sthread.setDaemon(False)
        sthread.start()
        
        rthread = threading.Thread(target = self.recvRecognThread, args = [])
        rthread.setDaemon(False)
        rthread.start()

    def recvRecognThread(self):
        while True:
            recvdat = self.wss.recv()
            if recvdat:
                mtype = recvdat[0]
                compressmode = recvdat[1]
                print("msgtype:", mtype, " compress mode:", compressmode)
                if mtype == 2:
                    buf = struct.unpack("B", recvdat[2:])
                    print("recv body:", buf)
                    pass
                elif mtype == 4:
                    camerano_length = recvdat[2]
                    fmt = "{}s19s{}s".format(camerano_length, len(recvdat) - 3 - 19 - camerano_length)
                    print("fmt:", fmt)
                    buf = struct.unpack(fmt, recvdat[3:])
                    print("recv buf:", buf)
                    camerano = buf[0]
                    identify = buf[1]
                    statusinfo = buf[2]
                    print("camerano:", camerano)
                    print("identify", identify)
                    print("statusinfo", statusinfo)
                    '''
                    if status == 0:
                        buf = struct.unpack(">H19sB8s16s", recvdat[2:])
                        self.globalWait = False
                        print("result: ", buf[0], buf[1], buf[2], buf[3], buf[4])
                    elif status == 1:
                        buf = struct.unpack(">H19sBB", recvdat[2:])
                        self.globalWait = False
                        print("result: ", buf[0], buf[1], buf[2], buf[3])
                    else:
                        buf = struct.unpack(">H19sB", recvdat[2:])
                        print("result: ", buf[0], buf[1], buf[2])
                    '''
                    pass
                else:
                    print("mtype=", mtype)
                    print("type(mtype)=", type(mtype))

    def sendImagePthread(self):
        while True:
            file_list = os.listdir(self.path)
            time.sleep(1)
            for filename in file_list:
                '''读取内容'''
                if filename.startswith("upload"):
                    continue

                if self.globalWait == False:
                    print("filename:%s" % filename) 
                    f = open(self.path+'/'+filename, 'rb')
                    mbinary = f.read()
                    os.rename(self.path + '/' + filename, self.path + '/' + "upload" + filename)
                    '''生成md5值'''
                    md5 = hashlib.md5()
                    md5.update(mbinary)
                    md5str = md5.hexdigest()
                    
                    camerano_bytes = bytes("idontcarewhoareyoudoyouunderstand", encoding="utf-8")
                    cameranolength = len(camerano_bytes)
                
                    imagelen = len(mbinary)
                    id_bytes = bytes("1987020900123498769", encoding="utf-8")
                    md5_bytes = bytes(md5str, encoding="utf-8")

                    fmt = ">{}{}s{}{}s".format("B", cameranolength, "19s32sI", imagelen)
                    print("before fmt:%s" % fmt)
                    body = struct.pack(fmt, cameranolength, camerano_bytes, id_bytes, md5_bytes, imagelen, mbinary)
                    tmp = struct.unpack(fmt, body)
                    print("send body", tmp[0], tmp[1], tmp[2], tmp[3])
                    body_compressed = bz2.compress(bytes(body))
                    
                    bodylen = len(body_compressed)
                    fmt = ">{}{}s".format("BB", bodylen)
                    print("after fmt:%s" % fmt)
                    senddata = struct.pack(fmt, 3, 1, body_compressed)

                    print("imagelen = %d" % imagelen)
                    print("bodylen = %d" % len(body))

                    '''发送websocket请求数据'''
                    self.wss.send_binary(senddata)
                    self.globalWait = True
                else:
                    while self.globalWait == True:
                        time.sleep(0.01)
            pass

    def renameAllPicture(self):
        filelist = os.listdir(self.path)
        num = 0
        for val in filelist:
            slist = val.split('.')
            imagetype = slist[len(slist) - 1]
            oldname = "{}/{}".format(self.path, val)
            newname = "{}/{}{}.{}".format(self.path, "pic", num, imagetype)
            os.rename(oldname, newname)
            num = num + 1

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s.%(msecs)03d %(levelname)s:%(filename)s[line:%(lineno)d]: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("main")
    client = Client("/home/duan/Pictures")
    if client.login() == True:
        client.renameAllPicture()
        client.run()
