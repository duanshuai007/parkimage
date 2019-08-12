#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import logging
from os import PathLike
from PIL import Image
import hashlib
import Config

class CtrlImage:
    
    saveImageDir = ""
    path = ""
    #构造函数
    def __init__(self):
        self.saveImageDir = Config.getConfigEnv("SAVE_IMAGE_DIR")
        pass
    #保存功能
    #name format: city-park-server-camerano-time.jpeg
    def save(self, name, data):
        dirlist = name.split('-')
        if len(dirlist) < 5:
            logging.info("image name format error, name:%s" % name)
            return

        tmp = "%s/%s/%s/%s" % (dirlist[0], dirlist[1], dirlist[2], dirlist[3])
        self.path = self.saveImageDir + '/' + tmp
        logging.info("save:path=%s name=%s" % (self.path, name))
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if os.path.isfile(self.path + '/' + name):
            os.remove(self.path + '/' + name)
        dstfile = open(self.path + '/' + name, 'wb')
        dstfile.write(data)
        dstfile.close()
        pass

    def isVaildImage(self, name):
        bValid = True
        try:
            Image.open(name).load()
        except OSError:
            bValid = False
        return bValid 

    def delete(self, name):
        pass

    def show(self, name):
        pass

    def checkMd5(self, data, md5str):
        md5 = hashlib.md5()
        md5.update(data)
        md5hex = md5.hexdigest()
        logging.info("the image md5: %s" % md5hex)
        if md5str == md5hex:
            return True
        else:
            return False

if __name__ == '__main__':
    x = CtrlImage()
    x.save("pic.jpg", b'382912148217921382198392183921')
