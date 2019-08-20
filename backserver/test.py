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

class Client:
    '''图片识别请求格式'''
    msg_recogn_request = {
        "type":"",
        "image":{
            "camerano":0,
            "identify":"",
            "md5":"",
            "content":""
        }
    }
    '''图片识别请求应答信息格式'''
    msg_recogn_resp = {
    	"type":"recogn resp",
        "image":{
            "carmerno":3,
            "identify":"",
            "result":{
                "status":"success",
                "color":"xxx",
                "plate":"xxxx"
            }
        }
    }
    '''登陆请求格式'''
    msg_login = {
        "type": "request",
        "content": {
            "category": "login",
            "token": "MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ=",
            "city" : "shenyang",
            "park" : "hcwanxin",
            "server" : "98"
        }
    }
    '''登陆请求应答格式'''
    msg_login_resp = {
        "type": "response",
        "content": {
            "category": "login",
            "status": 1
        }
    }
    
#path = "/home/duan/Pictures"
    wss = ''

    def __init__(self, path):
        self.path = path
        logging.info("set path = %s" % path)
        pass

    def login(self):
        logging.info("login")
        self.wss = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        '''客户端首先需要登陆到服务器上'''        
        jsonmsg = json.dumps(self.msg_login)
        print(jsonmsg)
        self.wss.connect("wss://192.168.200.210:4000/park")
        self.wss.send(jsonmsg)
        '''
        验证登陆是否成功
        '''
        recv = self.wss.recv()
        print("recv login response:%s" % recv)
        info  = json.loads(recv)
        if info["content"]["status"] != "success":
            print("login failed")
            return False
        else:
            print("login success")
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
            recv = self.wss.recv()
            if recv:
                info = json.loads(recv)
                logging.info(info)
                logging.info("------------")
#logging.info(info)
                if info["type"] == "recogn resp" and info["image"]["result"]["status"] == "success":
                    print("wait for result") 
                    recv = self.wss.recv()
                    data = json.loads(recv)
                    logging.info(data)
                elif info["type"] == "recogn resp" and info["image"]["result"]["status"] == "ready":
                    logging.info("read recogn image") 
                else:
                    logging.info("server recogn image error:%s" % info["image"]["result"]["status"])

    def sendImagePthread(self):
        while True:
            file_list = os.listdir(self.path)
            for filename in file_list:
                '''读取内容'''
                if filename.startswith("upload"):
                    continue
                print("filename:%s" % filename) 
                f = open(self.path+'/'+filename, 'rb')
                mbinary = f.read()
                os.rename(self.path + '/' + filename, self.path + '/' + "upload" + filename)
                '''生成md5值'''
                md5 = hashlib.md5()
                md5.update(mbinary)
                md5str = md5.hexdigest()
                '''字典元素赋值 '''
                self.msg_recogn_request["type"] = "recogn req"
#self.msg_recogn_request["image"]["city"] = "sy"
#               self.msg_recogn_request["image"]["park"] = "wanda"
#               self.msg_recogn_request["image"]["server"] = 1
                self.msg_recogn_request["image"]["camerano"] = 9
                self.msg_recogn_request["image"]["identify"] = str(int(time.time() * 1000))
                self.msg_recogn_request["image"]["md5"] = md5str
                self.msg_recogn_request["image"]["content"] = base64.b64encode(mbinary).decode('utf-8')
                '''字典转换为json'''
                jsonmsg = json.dumps(self.msg_recogn_request)
                '''发送websocket请求数据'''
                self.wss.send(jsonmsg)
#logging.info("send : %s" % jsonmsg)
                '''等待接收数据'''
#                recvmsg = self.ws.recv()
#                if not recvmsg:
#                    '''如果没接收到数据，因为是阻塞接收，不可能走到这里'''
#                    logging.info("--------------------")
#                    self.ws.send_binary(mbinary)
#                else:
#                    print("test recv: %s" % recvmsg)
#                    info = json.loads(recvmsg)
#                    if info["type"] == "recogn resp" and info["image"]["result"]["status"] == "ready":
#                        continue
#                    else:
#                        logging.info("upload image error")

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
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d')
    logging.info("main")
    client = Client("/home/duan/Pictures")
    if client.login() == True:
        client.renameAllPicture()
        client.run()
