#!/bin/sh

docker_contain_name=$(docker ps -a | grep mypark | awk -F" " '{print $NF}')
echo "docker_contain_name=${docker_contain_name}" >> /home/duan/boot.log

while true
do
    ret=$(docker start ${docker_contain_name})
    #-z 为检测字符串长度是否为0,为0时返回true
    if [ -z "${ret}" ]
    then
        echo "docker[${docker_contain_name}] start failed!" >> /home/duan/boot.log
    fi

    sleep 30
done

exit 0
