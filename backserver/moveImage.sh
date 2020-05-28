#!/bin/bash
MKDIR=$(which mkdir)
MV=$(which mv)
FIND=$(which find)
UPLOAD_PATH="image_rsync"

root_dir=$1
tmp_time=$2

DEBUG=$(awk -F"=" '{if($1=="DEBUGLOGFILE") print $2}' ${root_dir}/config.ini)
ImageSavePath=$(awk -F"=" '{if($1=="SAVE_IMAGE_DIR") print $2}' ${root_dir}/config.ini)

#root_dir="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
dirlist=$(${FIND} ${root_dir}/${ImageSavePath} -name "*.jpg" | grep -E ".+[0-9]{14}\_.+\.jpg$")

#echo "root_dir=$root_dir ImageSavePath=$ImageSavePath" >>  ${root_dir}/${DEBUG}
#echo "dirlist=$dirlist " >> ${root_dir}/${DEBUG}
#echo $root_dir

if [ ! -d "${root_dir}/${UPLOAD_PATH}" ]
then
    ${MKDIR} -p ${root_dir}/${UPLOAD_PATH}
fi
#echo "Imagesavepath:$ImageSavePath"
for val in ${dirlist}
do
    #echo ${val}
    #截取从右侧最先匹配到的/左边的内容
    dir=`echo ${val%/*}`
    #截取从左侧最先匹配到的ImageSavePath/右边的内容
    dir=`echo ${dir#*${ImageSavePath}/}`
    imagename=`echo ${val##*/}`
    #echo "dir=${dir}, name=${imagename}" >> ${root_dir}/${DEBUG}
    
    ymd=$(echo $imagename | awk -F"-" '{print $5}')   
    #echo "ymd=$ymd" >> ${root_dir}/${DEBUG}
    ymd=${ymd%%_*}
    #echo "ymd=$ymd" >> ${root_dir}/${DEBUG}
    ymd=${ymd:0:8}
    #echo "ymd=$ymd" >> ${root_dir}/${DEBUG}
    year=${ymd:0:4}
    month=${ymd:4:2}
    day=${ymd:6:2}
    #echo "year=$year, month=$month, day=$day" >> ${root_dir}/${DEBUG}

    if [ ! -d "${root_dir}/${UPLOAD_PATH}/${dir}/${year}/${month}/${day}" ]
    then
        ${MKDIR} -p ${root_dir}/${UPLOAD_PATH}/${dir}/${year}/${month}/${day}
    fi

    echo "${tmp_time}: ${MV} ${val} ${root_dir}/${UPLOAD_PATH}/${dir}/${year}/${month}/${day}" >> ${root_dir}/${DEBUG}
    ${MV} ${val} ${root_dir}/${UPLOAD_PATH}/${dir}/${year}/${month}/${day}
    #sy-wanda-1-9-20190730_180017-696_xxx_xxxxx.jpg 已识别
    #sy-wanda-1-9-20190730_180017-696.jpg   未识别
done
