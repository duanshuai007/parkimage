#!/bin/bash

SERVER_MAIN_NAME="park_imagerecogn_c"
#DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
fullname=$0
DIR_PATH=`echo ${fullname%/*}`
#echo "${fullname} ${DIR_PATH}"
PYTHON=`which python3`

stop() {
    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_MAIN_NAME} pid:${pid} kill" >> ${DIR_PATH}/server.log
        kill -9 ${pid}
    else
        echo "${SERVER_MAIN_NAME} already stop"
    fi
}

start() {
    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        ${PYTHON} ${DIR_PATH}/server_main.py &
    else
        echo "${SERVER_MAIN_NAME} already running"
    fi
}

restart() {
    stop
    sleep 1
    start
}

restart
