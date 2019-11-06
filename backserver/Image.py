#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
from PIL import Image
import hashlib
import Config
import LoggingHelper

class CtrlImage:
    
    saveImageDir = ""
    path = ""
    log = None
    #构造函数
    def __init__(self):
        c = Config.Config()
        self.saveImageDir = c.get("CONFIG", "SAVE_IMAGE_DIR")
        logfile = c.get('CONFIG', 'LOGFILE')
        self.log = LoggingHelper.LoggingProducer()

        pass
    #保存功能
    #name format: city-park-server-camerano-time.jpeg
    def save(self, name, data):
        dirname = name.split('-')
        if len(dirname) < 5:
            self.log.info("ImageHandler ==> image name format error, name:%s" % name)
            return False

        try:
            tmp = "%s/%s/%s/%s" % (dirname[0], dirname[1], dirname[2], dirname[3])
            self.path = self.saveImageDir + '/' + tmp
            self.log.info("ImageHandler ==> image save: path=%s name=%s imagesize=%d" % (self.path, name, len(data)))
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            if os.path.isfile(self.path + '/' + name):
                os.remove(self.path + '/' + name)
            dstfile = open(self.path + '/' + name, 'wb')
            dstfile.write(data)
            dstfile.close()
            return True
        except Exception as e:
            logging.error(f'ImageHandler ==> image save error:{e.args}')
            return False
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
        self.log.info("ImageHandler ==> the image md5: %s" % md5hex)
        if md5str == md5hex:
            return True
        else:
            return False

if __name__ == '__main__':
    x = CtrlImage()
    x.save("pic.jpg", b'382912148217921382198392183921')
