#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import queue
import logging 

'''
初始化websockt和图片处理线程之间的消息队列
该函数只允许被调用一次，多次调用会使消息队列
产生错误
'''
def init():
    global _global_dict
    _global_dict = {"recv":queue.Queue(128),}
    logging.info("queue init")

def get():
    return _global_dict 
