#!/bin/sh

path=$0
#echo "path=${path}"
ROOT_DIR=`echo ${path%/*}`
#echo "DIR=${ROOT_DIR}"

if [ -n "${ROOT_DIR}" ]
then
    echo "ROOT_DIR is NULL"
    ROOT_DIR=`pwd`
    echo "update ROOT_DIR:${ROOT_DIR}"
fi

CONFIG_FILE="config.ini"

if [ ! -e "${ROOT_DIR}/${CONFIG_FILE}" ] 
then
    echo "${ROOT_DIR}/${CONFIG_FILE} is not exist"
    return
fi

do_update_msgqueue_key() {
#echo "val=$1"
    filename="${ROOT_DIR}/$1"
    echo "filename=${filename}"
    sed -i "s,#define MSG_KEYFILE .*$,#define MSG_KEYFILE \"${filename}\",g" ${ROOT_DIR}/include/msgqueue.h
}

num=`cat ${ROOT_DIR}/${CONFIG_FILE} | wc -l`
curlineno=1
while true
do
    line=`sed -n ${curlineno}p ${ROOT_DIR}/${CONFIG_FILE}`
    curlineno=`expr ${curlineno} + 1`

    key=`echo ${line%:*}`
    echo "key=${key}"
    value=`echo ${line#*:}`
    echo "value=${value}"

    case ${key} in
    "MSGQUEUE_KEY")
        echo "find msgqueue key"
        if [ ! -e ${value} ]
        then
            echo "msgqueue file is not exist"
            echo "now create msgqueue"
            touch ${value}
            ifconfig >> ${value}
        fi
        do_update_msgqueue_key ${value}
    ;;
    "CAMERA_SOCKET_PORT")
        echo "CAMERA_SOCKET_PORT"

    ;;
    "CAMERA_PORT")
        echo "CAMERA_PORT"
    ;;
    "CAMERA_IP")
        echo "CAMERA_IP"
    ;;
    esac

    if [ ${curlineno} -gt ${num} ]
    then
        break
    fi
done
