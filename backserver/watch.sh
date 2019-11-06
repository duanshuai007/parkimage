#!/bin/bash

SERVER_NAME="park_imagerecogn_server.py"
SERVER_MAIN_NAME="park_imagerecogn_c"
root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
PYTHON=`which python3`

stop() {

    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_NAME} pid: ${pid} kill" >> ${root_dir}/server.log
        kill -9 ${pid}
    else
        echo "${SERVER_NAME} already stop"
    fi

    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_MAIN_NAME} pid:${pid} kill" >> ${root_dir}/server.log
        kill -9 ${pid}
    else
        echo "${SERVER_MAIN_NAME} already stop"
    fi
}

start() {

    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        ${PYTHON} ${root_dir}/server_main.py &
    else
        echo "${SERVER_MAIN_NAME} already running"
    fi

    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        ${PYTHON} ${root_dir}/${SERVER_NAME} &
        #因为在ImageHandler里面判断tkinter启动用了一秒延时，所以这里必须大于1秒
        sleep 2
        pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v vi | grep -v grep | awk '{print $2}'`
        if [ ! -n "${pid}" ]
        then
            echo "${SERVER_NAME} start failed" >> ${root_dir}/server.log
            exit
        fi
    else
        echo "${SERVER_NAME} already running"
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
