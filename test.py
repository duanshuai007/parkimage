#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import websocket
import json
import time
import base64

image = ""
ws = websocket.WebSocket()
'''
{
"type": "request",
"content": {
"category": "login",
"token": "MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ="
}
}
'''

msg = {
    "type": "request",
    "content": {
        "category": "login",
        "token": "MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ="
    }
}

print(msg)
jsonmsg = json.dumps(msg)
print(jsonmsg)
ws.connect("ws://192.168.200.199:4000/park")
ws.send(jsonmsg)
time.sleep(1)

msg_head = {
	"type":"recogn",
    "identify":1234567890,
	"image":{
		"city":"shenyang",
		"park":"wanda",
		"carmerno":9,
		"time":"2019-06-28 09:24:33",
		"size":20,
        "md5":"e5bb31728693897d90fa2150e3269697"
	}
}

jsonmsg = json.dumps(msg_head)
ws.send(jsonmsg)

recvmsg = ws.recv()
if not recvmsg:
    mbinary = b'1234567890abcdeffdac'
    image = base64.urlsafe_b64encode(mbinary)
    #ws.send_binary(image)
    ws.send_binary(mbinary)
else:
    print("recv:")
    print(recvmsg)
    info = json.loads(recvmsg)
    if info["status"] == "recvimage":
        f = open("/home/duan/park/test.jpeg", 'rb')
        mbinary = f.read()
#mbinary = b'1234567890abcdeffdac'
#image = base64.urlsafe_b64encode(mbinary)
        ws.send_binary(mbinary)
