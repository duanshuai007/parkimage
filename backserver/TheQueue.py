#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import queue
import Config
import LoggingHelper
'''
初始化websockt和图片处理线程之间的消息队列
该函数只允许被调用一次，多次调用会使消息队列
产生错误
'''
def init():
    global _global_dict
    c = Config.Config()
    constr = c.get("CAMERA", "CAMERA_IP_AND_SCREEN")
    rlist = constr.split(',')
    cameraNum = len(rlist)
    mode = c.get("CAMERA", "CLIENT_CAMERA_MODE")
    logfile = c.get('CONFIG', 'LOGFILE')
    log = LoggingHelper.LoggingProducer()

    log.info("TheQueue ==> find %d camera, create Queue len:%d" % (cameraNum,cameraNum))
    if mode == "PREEMPTION":
        _global_dict = {"recv":queue.Queue(cameraNum), "blackList":queue.Queue(10)}
    elif mode == "MATCH":
        _global_dict = {"recv":queue.Queue(4), "blackList":queue.Queue(10)}
        
    log.info("TheQueue ==> queue init")

def get():
    return _global_dict 
