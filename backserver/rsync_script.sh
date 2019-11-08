#!/bin/bash

root_dir=$1
tmp_time=$2

#tmp_time=`date +"%Y-%m-%d %H:%M:%S"`

nas_username=`cat ${root_dir}/config.ini | grep USERNAME | awk -F"=" '{print $2}'`
#nas_username=`echo ${line#*:}`
nas_password=`cat ${root_dir}/config.ini | grep PASSWORD | awk -F"=" '{print $2}'`
#nas_password=`echo ${line#*:}`
nas_addr=`cat ${root_dir}/config.ini | grep ADDRESS | awk -F"=" '{print $2}'`
#nas_addr=`echo ${line#*:}`
nas_port=`cat ${root_dir}/config.ini | grep PORT | awk -F"=" '{print $2}'`
#nas_port=`echo ${line#*:}`
nas_userdir=`cat ${root_dir}/config.ini | grep USERDIR | awk -F"=" '{print $2}'`
#nas_userdir=`echo ${line#*:}`

#nas_username="duanshuai"
#nas_password="19870209"
#nas_addr="192.168.200.239"
#nas_port="5000"
#nas_userdir="/var/services/homes/duanshuai"

DEBUG=$(cat ${root_dir}/config.ini | grep DEBUGLOGFILE | awk -F"=" '{print $2}')

BASH=`which bash`
EXPECT=`which expect`
GREP=`which grep`
AWK=`which awk`
#root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
rsyncimagedir="image_rsync"

#echo "${BASH} ${root_dir}/moveImage.sh" >> ${root_dir}/${DEBUG}
${BASH} ${root_dir}/moveImage.sh "${root_dir}" "${tmp_time}"
#ifconfig不能使用which获取到正确的绝对位置，不知道问题出在哪
server_ip=`/sbin/ifconfig eth0 | ${GREP} -w inet | ${AWK} -F" " '{print $2}'`
updatecmd="rsync -rvazpt --progress ${root_dir}/${rsyncimagedir}/ --remove-source-files ${nas_username}@${nas_addr}:${nas_userdir}/${server_ip}"
echo "${tmp_time}:${updatecmd}" >> ${root_dir}/${DEBUG}

${EXPECT}<<-EOF
set time 5
spawn ${updatecmd}
expect {
"*yes/no" { send "yes\r"; exp_continue }
"*Password" { send "${nas_password}\r" }
"*password" { send "${nas_password}\r" }
"密码" { send "${nas_password}\r" }
}
expect eof 
EOF
