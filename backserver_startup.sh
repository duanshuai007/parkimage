#!/bin/sh


while true
do
    docker_contain_name=$(docker ps -a | grep -w park | awk -F" " '{print $NF}')
    if [ -n "${docker_contain_name}" ];then
        ret=$(docker start ${docker_contain_name})
        #-z 为检测字符串长度是否为0,为0时返回true
        if [ -z "${ret}" ];then
            echo "docker[${docker_contain_name}] start failed!" >> /home/duan/boot.log
        fi
    fi

    sleep 20
done

exit 0
