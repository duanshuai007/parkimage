#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import logging

def getConfigEnv(str):
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    value = ""
    with open(path + '/config.ini', 'r') as conf:
        lines = conf.readlines()
        for line in lines:
            if line.startswith(str):
                linelist = line.split(':')
                value = linelist[1].strip()
                break

    if str in ["SAVE_IMAGE_DIR", "MSGQUEUE_KEY", "LOGFILE"]:
        value = path + '/' + value
    elif str in ["CAMERA_SOCKET_PORT", "CAMERA_PORT", "WEBSOCKET_PORT"]:
        value = int(value, 10)
    return value

if __name__ == '__main__':
    pass
