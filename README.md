##BACK SERVER

* 该程序运行在docker中。  

> 执行`builddocker.sh`脚本文件就能自动生成docker镜像。  
> 使用`docker ps` 查看运行中的容器。  
> 使用`docker ps -a` 查看所有容器。  
> 使用`docker image ls` 查看所有镜像。  
> 使用`docker run -dit --name park --network=host 69993c294529 /bin/bash -c "bash /home/duan/backserver/install_crontask.sh 192.168.1.123"`来启动一个容器，容器名为park，IP地址为对应的服务器所连接的相机IP地址。  
> 使用`docker exec -ti park bash`进入运行中的容器中。  
> 使用`docker stop park`来停止运行中的容器  
> 使用`docker rm park`删除停止的容器。  
> 使用`docker image rm xxxxxx`删除对应的镜像。
