#!/bin/bash

root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

BASH=`which bash`

export DISPLAY=:0

while true
do
    tmp_time=`date +"%Y-%m-%d %H:%M:%S"`
    #图片同步上传到nas服务器端
    ${BASH} ${root_dir}/rsync_script.sh "${root_dir}" "${tmp_time}"

    #检查Python程序是否在运行,如果没能发现进程，就需要启动它
    ret=`ps -ef | grep -w "park_imagerecogn_server.py"  | grep -v vi | grep -v grep`
    if [ ! -n "${ret}" ]
    then
        echo "${tmp_time}:${root_dir} start server" >> ${root_dir}/server.log
        ${BASH} ${root_dir}/watch.sh start 
    else
        echo "find server running"
    fi

    #检查C程序是否在运行,C程序作为服务器需要运行于Python程序之前
    ret=`ps -ef | grep -w "park_imagerecogn_c" | grep -v vi | grep -v grep`
    if [ ! -n "${ret}" ]
    then
        echo "${tmp_time}:${root_dir} start server_main" >> ${root_dir}/server.log
        ${BASH} ${root_dir}/watch.sh restart
    else
        echo "find server main running"
    fi

    sleep 10

done
