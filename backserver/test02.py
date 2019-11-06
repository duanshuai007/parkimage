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

msg = "{\"info\":{\"camera0\":{\"ip\":\"192.168.200.211\",\"port\":8080},\"camera1\":{\"ip\":\"192.168.200.213\",\"port\":8080}},\"apply\":2}\x00"

import json

print(msg)
msg = msg.replace('\x00', '')
msg = msg.strip()
msgjson = json.loads(msg)
print(msgjson)


import os
import subprocess

cmd = 'wmctrl -l | grep tk | awk -F \" \" \'{print $1}\''
#ret = os.system(cmd)
#ret = subprocess.run("wmctrl -l", shell=True)
#ret = subprocess.getstatusoutput("wmctrl -l")
ret = subprocess.getoutput(cmd).split('\n')
print("ret=")
print(ret)
