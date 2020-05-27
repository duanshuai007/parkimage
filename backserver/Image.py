#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
from PIL import Image
import hashlib
import Config
import LoggingQueue
from strictly_func_check import strictly_func_check

class CtrlImage:
    
    saveImageDir = ""
    path = ""
    log = None
    #构造函数
    def __init__(self):
        c = Config.Config()
        self.saveImageDir = c.get("CONFIG", "SAVE_IMAGE_DIR")
        self.log = LoggingQueue.LoggingProducer().getlogger()
        pass

    #保存功能
    #name format: city-park-server-camerano-time.jpeg
    @strictly_func_check
    def save(self:object, name:str, data:bytes)->bool:
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

    def checkNameExists(self:object, name:str)->bool:
        dirname = name.split('-')
        if len(dirname) < 5:
            self.log.info("ImageHandler ==> image name format error, name:%s" % name)
            return False

        try:
            tmp = "%s/%s/%s/%s" % (dirname[0], dirname[1], dirname[2], dirname[3])
            self.path = self.saveImageDir + '/' + tmp
            if os.path.isfile(self.path + '/' + name):
                return False
            return True;
            
        except Exception as e:
            return False


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

    @strictly_func_check
    def checkMd5(self:object, data:bytes, md5str:str)->bool:
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
    x.save("city-park-server-camerano-time.jpeg", b'382912148217921382198392183921')
