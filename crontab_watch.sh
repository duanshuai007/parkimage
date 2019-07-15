#!/bin/bash

DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
time=`date +"%Y-%m-%d %H:%M:%S"`

ret=`ps -ef | grep -w server.py | grep -v vi | grep -v grep`
#如果没能发现进程，就需要启动它
if [ ! -n "${ret}" ]
then
    echo "${time}: start server"
    echo "${time}: start server" >> ${DIR_PATH}/server.log
    /bin/bash ${DIR_PATH}/watch.sh restart 
    return
else
    echo "find server running"
fi

ret=`ps -ef | grep -w main | grep -v grep`
if [ ! -n "${ret}" ]
then
    echo "${time}: start server_main"
    echo "${time}: start server_main" >> ${DIR_PATH}/server.log
    /bin/bash ${DIR_PATH}/watch.sh start
else
    echo "find server main running"
fi
