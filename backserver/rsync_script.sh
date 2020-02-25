#!/bin/bash

root_dir=$1
tmp_time=$2

#tmp_time=`date +"%Y-%m-%d %H:%M:%S"`

nas_username=$(awk -F"=" '{if($1=="USERNAME") print$2}' ${root_dir}/config.ini)
nas_password=$(awk -F"=" '{if($1=="PASSWORD") print$2}' ${root_dir}/config.ini)
nas_addr=$(awk -F"=" '{if($1=="ADDRESS") print$2}' ${root_dir}/config.ini)
nas_port=$(awk -F"=" '{if($1=="PORT") print$2}' ${root_dir}/config.ini)
nas_userdir=$(awk -F"=" '{if($1=="USERDIR") print$2}' ${root_dir}/config.ini)

#nas_username="duanshuai"
#nas_password="19870209"
#nas_addr="192.168.200.239"
#nas_port="5000"
#nas_userdir="/var/services/homes/duanshuai"

DEBUG=$(awk -F"=" '{if($1=="DEBUGLOGFILE") print $2}' ${root_dir}/config.ini)

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
