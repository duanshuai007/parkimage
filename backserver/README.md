##BACK SERVER

> 该程序使用Python3.6

## 程序中涉及到的python库
 
> 安装pip3的方法  
>> sudo apt-get install python3-pip  

> 以下是程序中涉及到的系统库  
>> tornado  
>> logging  
>> threading   
>> time  
>> json  
>> queue  
>> socket  
>> select  
>> os  
>> PIL的模块名为Pillow，通过pip3工具安装  
>> hashlib  
>> base64  
>> hmac  
>> websocket客户端所用的库是websocket_client  
>> tkinter模块安装方法有些特殊，需要通过sudo apt-get install python3-tk指令来进行安装


## 使用方法

> 在config.ini文件中配置各个参数，除了相机地址和端口需要配置以外，一般保持默认即可
> 修改addTaskToCron.sh中的PASSWORD的值，与用户的sudo密码一致，然后执行./addTaskToCron.sh  
> 脚本watch.sh start启动程序,watch.sh stop停止程序,watch.sh restart重新启动程序.  
> 在shell界面执行crontab -e，进入编辑页面，新开一行输入`*/1 * * * * export DISPLAY=:0 && /bin/sh /home/duan/backserver/crontab_watch.sh`,该指令功能是每隔一分钟执行crontab_watch.sh脚本.  
> 想要立即执行也可以在工程目录内执行`./crontab_watch.sh`  
