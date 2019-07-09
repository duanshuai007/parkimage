#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import logging
from Image import CtrlImage 

def main():
    ctrlImage = CtrlImage()
    path = ctrlImage.getSaveImageDir()

    cmd = "%s %s &" % ("/home/duan/backserver/main", path)
    os.system(cmd)

if __name__ == '__main__':
    main()

