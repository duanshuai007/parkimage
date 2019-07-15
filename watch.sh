#!/bin/bash

SERVER_NAME="server.py"
SERVER_MAIN_NAME="main"
DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

stop() {
    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_MAIN_NAME} pid:${pid}"
        kill -9 ${pid}
    else
        echo "${SERVER_MAIN_NAME} already stop"
    fi
    
    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_NAME} pid: ${pid}"
        kill -9 ${pid}
    else
        echo "${SERVER_NAME} already stop"
    fi
}

start() {
    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        python3 ${DIR_PATH}/server.py &
        sleep 1
    else
        echo "${SERVER_NAME} already running"
    fi

    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        python3 ${DIR_PATH}/server_main.py &
    else
        echo "${SERVER_MAIN_NAME} already running"
    fi
}

restart() {
    stop
    sleep 1
    start
}

cmd=$1

case "${cmd}" in
    start)
        echo "========================"
        echo "***   start server   ***"
        start
        echo "========================"
        ;;
    stop)
        echo "========================"
        echo "***    stop server   ***"
        stop
        echo "========================"
        ;;
    restart)
        echo "========================"
        echo "***   restart server ***"
        restart
        echo "========================"
        ;;
    *)
        echo "========================"
        echo "***   unknow cmd     ***"
        echo "========================"
        ;;
esac
