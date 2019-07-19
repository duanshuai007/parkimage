#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import logging
import sys
from Image import CtrlImage 
import Config

def main():
    ctrlImage = CtrlImage()
    
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    port = Config.getConfigEnv("CAMERA_SOCKET_PORT")
    camera_port = Config.getConfigEnv("CAMERA_PORT")
    camera_ip = Config.getConfigEnv("CAMERA_IP")
    keyfile = Config.getConfigEnv("MSGQUEUE_KEY")
    saveImgPath = Config.getConfigEnv("SAVE_IMAGE_DIR")
    logfile =  Config.getConfigEnv("LOGFILE")

    if not logfile:
        logging.error("LogFile not define, please add to config.ini")
     
    logging.basicConfig(filename=logfile, level=logging.DEBUG,format='%(asctime)s %(levelname)s:%(filename)s[line:%(lineno)d]: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

    logging.info("------------------------");
    logging.info("---server_main.py start---")
    #expamle: ./main   saveimagedir   local_socket_port   camera_ip   camera_port   keyfile_path_name
    cmd = "%s/%s %s/ %s %s %s %s &" % (  path, "park_imagerecogn_c", saveImgPath, port, camera_ip, camera_port, keyfile)
    logging.info("******************")
    logging.info(cmd)
    logging.info("******************")
    os.system(cmd)

if __name__ == '__main__':
    main()

