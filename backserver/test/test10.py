#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import configparser

config = configparser.ConfigParser()
print(config.sections())

print(config.read('config.ini'))
print(config.sections())

print(config['CONFIG']["SAVE_IMAGE_DIR"])

print(config['CAMERA']["CAMERA_PORT"])
print(config['CAMERA']["CAMERA_IP_AND_SCREEN"])
print(config['CAMERA']["CAMERA_APPLY_MODE"])
print(config['CAMERA']["CLIENT_CAMERA_MODE"])


print("result=", eval("5*8"))
