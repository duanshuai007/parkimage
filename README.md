## BACK SERVER

* 该程序运行在docker中。  

> 执行`builddocker.sh`脚本文件就能自动生成docker镜像。  
> 使用`docker ps` 查看运行中的容器。  
> 使用`docker ps -a` 查看所有容器。  
> 使用`docker image ls` 查看所有镜像。  
> 使用`docker run -dit --name park --network=host [docker image id] /bin/bash -c "bash /home/duan/backserver/polltask.sh"`来启动一个容器。  
> 使用`docker exec -ti park bash`进入运行中的容器中。  
> 使用`docker stop park`来停止运行中的容器  
> 使用`docker rm park`删除停止的容器。  
> 使用`docker image rm xxxxxx`删除对应的镜像。

## ubuntu18.04 增加开机启动任务

> 
step1:  
vi /lib/systemd/system/rc.local.service  
在文件末尾添加    
[Install]  
WantedBy=multi-user.target  
Alias=rc-local.service

>
step2:  
ln -s /lib/systemd/system/rc.local.service /etc/systemd/system/rc.local.service

>
step3:  
vi /etc/rc.local  
`#!/bin/bash`     
`echo "hello" > /etc/test.log`  
`exit 0`

>
step4:
chmod +x /etc/rc.loca


## 使用service方式执行开机启动任务

> 1.将backserver.service文件复制到/lib/systemd/system目录下

> 2.执行sudo systemctl enable backserver.service设置开机启动


