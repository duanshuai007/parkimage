#!/usr/bin/python3
#-*- coding:utf-8 -*-

#b=isinstance("string", str)
#print(b)

#b=isinstance(None, None)
#print(b)
import time

s = time.strftime("%Y%m%d%H%M%S", time.localtime())
print(s)

s = s + str(int(time.time() * 1000000))[-6:]

#s = int(time.time() * 1000000)
print(s)

print(type(s))
s = time.localtime()
print(s)
print(type(s))
