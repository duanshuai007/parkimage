#!/bin/sh

time=`date +"%Y-%m-%d %H:%M:%S"`

ret=`ps -ef | grep -w server.py | grep -v grep`
#如果没能发现进程，就需要启动它
if [ ! -n "${ret}" ]
then
    echo "${time}: start server"
    echo "${time}: start server" >> /home/duan/server.log
    /bin/sh /home/duan/backserver/watch.sh restart 
    return
else
    echo "find server running"
fi

ret=`ps -ef | grep -w main | grep -v grep`
if [ ! -n "${ret}" ]
then
    echo "${time}: start server_main"
    echo "${time}: start server_main" >> /home/duan/server.log
    /bin/sh /home/duan/backserver/watch.sh start
else
    echo "find server main running"
fi
