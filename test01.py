#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import os
import sys
import Config

def modifyImageName(name, color, plate):
    '''sy-wanda-1-1-20190730_094312-036.jpg'''
    pathlist = name.split('-')
    rootpath = Config.getConfigEnv("SAVE_IMAGE_DIR")
    imagepath = "{}/{}/{}/{}/{}/".format(rootpath, pathlist[0], pathlist[1], pathlist[2], pathlist[3])

    namelist = name.split('.')
    namehead = namelist[0]
    imagetype = namelist[1]
    if not color and not plate:
        newname = "{}_{}_{}.{}".format(namehead, 'xxx', 'xxxxx', imagetype)
    else:
        newname = "{}_{}_{}.{}".format(namehead, color, plate, imagetype)
    os.rename(imagepath + name, imagepath + newname)

modifyImageName("sy-wanda-1-1-20190730_094408-786.jpg", '黄', '辽A98753')
