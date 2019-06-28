#!/usr/bin/env python3
#-*- coding:utf-8 -*-



import threading
import time
import logging

import server

class ImageHandler:
    rqueue = ""
    squeue = ""
    def __init__(self, qdict):
        if len(qdict) < 2:
            return 
        self.rqueue = qdict["recv"]
        self.squeue = qdict["send"]
        logging.info(qdict)

    def run(self):
        thread = threading.Thread(target = self.ImageProcess, args = [self.rqueue, self.squeue,])
        thread.setDaemon(True)
        thread.start()

    def ImageProcess(self, r, s):
        while True:
            while not r.empty():
                msg = r.get()
                logging.info(msg)
            logging.info("run in ImageProcess")
            time.sleep(1)
