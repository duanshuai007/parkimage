#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import random

'''
初始化websockt和图片处理线程之间的消息队列
该函数只允许被调用一次，多次调用会使消息队列
产生错误
'''
def init():
    global _global_unique_id_list
    _global_unique_id_list = []

def getUniqueID():
    while True:
        bIsExist = False
        uniqueid = "%s%s" % ("pid", random.randint(1000, 9999))
        for mid in _global_unique_id_list:
            if mid == uniqueid:
                bIsExist = True
                break
        if bIsExist == False:
            break
    _global_unique_id_list.append(uniqueid)
    print(_global_unique_id_list)
    return uniqueid

if __name__ == '__main__':
    init()
    print(getUniqueID())
    print(getUniqueID())
    print(getUniqueID())
    print(getUniqueID())
    print(getUniqueID())
