#!/bin/bash

root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
tmp_time=`date +"%Y-%m-%d %H:%M:%S"`

BASH=`which bash`

${BASH} ${root_dir}/rsync_script.sh "${root_dir}" "${tmp_time}"

ret=`ps -ef | grep -w park_imagerecogn_server.py  | grep -v vi | grep -v grep`
#如果没能发现进程，就需要启动它
if [ ! -n "${ret}" ]
then
#echo "${tmp_time}: start server"
    echo "${tmp_time}:${root_dir} start server" >> ${root_dir}/server.log
    ${BASH} ${root_dir}/watch.sh restart 
    exit
else
    echo "find server running"
fi

ret=`ps -ef | grep -w park_imagerecogn_c | grep -v grep`
if [ ! -n "${ret}" ]
then
#   echo "${tmp_time}: start server_main"
    echo "${tmp_time}:${root_dir} start server_main" >> ${root_dir}/server.log
    ${BASH} ${root_dir}/watch.sh start
else
    echo "find server main running"
fi
