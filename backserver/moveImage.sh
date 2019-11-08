#!/bin/bash
MKDIR=$(which mkdir)
MV=$(which mv)
FIND=$(which find)
UPLOAD_PATH="image_rsync"


root_dir=$1
tmp_time=$2

DEBUG=$(cat ${root_dir}/config.ini | grep DEBUGLOGFILE | awk -F"=" '{print $2}')
ImageSavePath=$(cat ${root_dir}/config.ini | grep -w "SAVE_IMAGE_DIR" | awk -F":" '{print $2}')

#root_dir="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
#echo "root_dir=${root_dir}" >> ${root_dir}/${DEBUG}
dirlist=$(${FIND} ${root_dir}/${ImageSavePath} -name *.jpg | grep -E ".+[0-9]{14}\_.+\.jpg$")
#echo "dirlist=${dirlist}" >> ${root_dir}/${DEBUG}

if [ ! -d "${root_dir}/${UPLOAD_PATH}" ]
then
    ${MKDIR} -p ${root_dir}/${UPLOAD_PATH}
fi

for val in ${dirlist}
do
    #echo ${val}
    #截取从右侧最先匹配到的/左边的内容
    dir=`echo ${val%/*}`
    #截取从左侧最先匹配到的ImageSavePath/右边的内容
    dir=`echo ${dir#*${ImageSavePath}/}`
    imagename=`echo ${val##*/}`
    #echo "dir=${dir}, name=${imagename}"
    
    if [ ! -d "${root_dir}/${UPLOAD_PATH}/${dir}" ]
    then
        ${MKDIR} -p ${root_dir}/${UPLOAD_PATH}/${dir}
    fi

    echo "${tmp_time}: ${MV} ${val} ${root_dir}/${UPLOAD_PATH}/${dir}" >> ${root_dir}/${DEBUG}
    ${MV} ${val} ${root_dir}/${UPLOAD_PATH}/${dir}
    #sy-wanda-1-9-20190730_180017-696_xxx_xxxxx.jpg 已识别
    #sy-wanda-1-9-20190730_180017-696.jpg   未识别
done
