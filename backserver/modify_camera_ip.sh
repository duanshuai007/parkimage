#!/bin/sh

if [ ! -n "$1" ]
then
    exit
else
    #CAMERA_IP:192.168.200.198
    sed -i "s/CAMERA_IP:.*/CAMERA_IP:$1/" /home/duan/backserver/config.ini
fi
