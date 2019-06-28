#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import logging
from os import PathLike
from PIL import Image
import hashlib

class CtrlImage:
    #构造函数
    def __init__(self):
        pass
    #保存功能
    def save(self, name, data):
#logging.info("save")
        dstfile = open(name, 'wb')
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
        if md5str == md5hex:
#           logging.info("right")
            return True
        else:
#           logging.info("error")
            return False

if __name__ == '__main__':
    x = CtrlImage()
#ret = x.isVaildImage('/home/duan/park/timg.jpeg')
#   print(ret)
    x.save("pic.jpg", b'382912148217921382198392183921')
