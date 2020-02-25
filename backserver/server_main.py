#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import Config
import LoggingHelper

def main():
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    c = Config.Config()
    port = int(c.get("CAMERA", "SOCKET_PORT"), 10)
    camera_port = int(c.get("CAMERA", "CAMERA_PORT"), 10)
    camera_ip_list = []
    rlist = c.get("CAMERA", "CAMERA_IP_AND_SCREEN").split(',')
    for item in rlist:
        rrlist = item.split('-')
        camera_ip_list.append(rrlist)
    
    logfile = c.get("CONFIG", "LOGFILE")
    log = LoggingHelper.LoggingProducer()

    if not logfile:
        log.error("LogFile not define, please add to config.ini")

    log.info(f'camera list: {camera_ip_list}')
    cmd = "{}/{} {}".format( path, "park_imagerecogn_c", port )
    cameranum = len(camera_ip_list)
    cmd = "{} {}".format(cmd, cameranum)
    for val in camera_ip_list:
        cmd = cmd + ' ' + str(val[0]) + ' ' + str(camera_port)
    cmd = "{} &".format(cmd)
    log.info("******************")
    log.info(cmd)
    print(cmd)
    log.info("******************")
    os.system(cmd)

if __name__ == '__main__':
    main()

