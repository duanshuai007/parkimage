#!/bin/sh

SERVER_NAME="server.py"
SERVER_MAIN_NAME="main"

stop() {
    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_MAIN_NAME} pid:${pid}"
        kill -9 ${pid}
    else
        echo "${SERVER_MAIN_NAME} already stop"
    fi
    
    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v grep | awk '{print $2}'`
    if [ -n "${pid}" ]
    then
        echo "${SERVER_NAME} pid: ${pid}"
        kill -9 ${pid}
    else
        echo "${SERVER_NAME} already stop"
    fi
}

start() {
    pid=`ps -ef | grep -w ${SERVER_NAME} | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        /usr/bin/python3 /home/duan/backserver/server.py &
        sleep 1
    else
        echo "${SERVER_NAME} already running"
    fi

    pid=`ps -ef | grep -w ${SERVER_MAIN_NAME} | grep -v grep | awk '{print $2}'`
    if [ ! -n "${pid}" ]
    then
        /usr/bin/python3 /home/duan/backserver/server_main.py &
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
