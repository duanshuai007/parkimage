#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import os
path="/home/duan/backserver/Picture/beijing/wanda/6/10"
name="beijing-wanda-6-10-1567763993771.jpg"

data="dsadsadasdsa"

if not os.path.exists(path):
    os.makedirs(path)

if os.path.isfile(path + '/' + name):
    os.remove(path + '/' + name)

dstfile = open(path + '/' + name, 'wb')
dstfile.write(data)
dstfile.close()
