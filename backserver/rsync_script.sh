#!/bin/bash

root_dir=$1
tmp_time=$2

#tmp_time=`date +"%Y-%m-%d %H:%M:%S"`

nas_username="duanshuai"
nas_password="19870209"
nas_addr="192.168.200.239"
nas_port="5000"
nas_userdir="/var/services/homes/duanshuai"

BASH=`which bash`
EXPECT=`which expect`
GREP=`which grep`
AWK=`which awk`
#root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
rsyncimagedir="image_rsync"

#echo "${BASH} ${root_dir}/moveImage.sh" >> ${root_dir}/debug.log
${BASH} ${root_dir}/moveImage.sh "${root_dir}" "${tmp_time}"
#ifconfig不能使用which获取到正确的绝对位置，不知道问题出在哪
server_ip=`/sbin/ifconfig eth0 | ${GREP} -w inet | ${AWK} -F" " '{print $2}'`
updatecmd="rsync -rvazpt --progress ${root_dir}/${rsyncimagedir}/ --remove-source-files ${nas_username}@${nas_addr}:${nas_userdir}/${server_ip}"
echo "${tmp_time}:${updatecmd}" >> ${root_dir}/debug.log

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
