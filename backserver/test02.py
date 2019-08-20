#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#import subprocess

#ret = subprocess.getoutput('rsync -rvazpt --progress Picture/ --remove-source-files duanshuai@192.168.200.239:/var/services/homes/duanshuai/192.168.200.210')
#print(ret)

import time

t=time.time()
print(t)
print(int(round(t*1000)))
print(int(time.time() * 1000))
print(time.localtime())
print(time.strftime("%Y%m%d_%H%M%S_%A", time.localtime()))
