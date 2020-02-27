#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import threading
import time
import copy
import Config
import LoggingQueue

class BlackList():
    
    recvQ = ''
    log = None

    ExistsIP = []
    DevList = []
    InfoDict = {
        "ip" : '',
        "timestamp" : 0,
        "count" : 0,
    }

    def __init__(self, MsgQueueList):
        self.log = LoggingQueue.LoggingProducer().getlogger()
        self.recvQ = MsgQueueList["blackList"]
        t = threading.Thread(target = self.Thread, args=[self.recvQ])
        t.setDaemon(False)
        t.start()
        pass

    def Thread(self, r):
        while True:
            if not r.empty():
                msgDict = r.get()
                self.log.info(f'BalckList ==> Recv Message : {msgDict}')
                ip = msgDict["ClientIP"]
                if ip not in self.ExistsIP:
                    self.ExistsIP.append(ip)
                    info = copy.deepcopy(self.InfoDict)
                    info["ip"] = ip
                    info["timestamp"] = int(time.time() * 1000)
                    self.DevList.append(info)
                else:
                    pass
                 
            time.sleep(0.01)
        pass
