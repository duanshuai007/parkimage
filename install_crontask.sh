#!/bin/bash

EXPECT=`which expect`
add_cmd="sudo service cron restart"
SH=`which sh`
BASH=`which bash`
SU=`which su`
#password 为本机的root用户密码
password="123"

echo "*/1 * * * * export DISPLAY=:0 && /bin/bash /home/duan/backserver/crontab_task.sh" | crontab

#users=`whoami`
#if [ "${users}" = "root" ]
#then
#   ${SU} duan
#fi

${EXPECT}<<-EOF
set time 5
spawn ${add_cmd}
expect {
"*yes/no" { send "yes\r"; exp_continue }
"*Password:" { send "${password}\r" }
"*password:" { send "${password}\r" }
"密码" { send "${password}\r" }
}
EOF

cameraip=$1
if [ -n "${cameraip}" ]
then
    ${SH} /home/duan/backserver/modify_camera_ip.sh "${cameraip}"    
fi

while true
do
    check=`service cron status | grep "cron is running"`
    echo "runrunrun:${check}"
    if [ ! -n "${check}" ]
    then
        ${BASH} /home/duan/backserver/crontab_task.sh
    fi  
    sleep 30
done
