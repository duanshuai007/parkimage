##BACK SERVER

> 该程序使用Python3.6

## 程序中涉及到的python库

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
>> PIL   
>> hashlib  
>> base64  
>> hmac  
>> websocket客户端所用的库是websocket_client


## 使用方法

> 在config.ini文件中配置各个参数，一般保持默认即可  
> 脚本watch.sh start启动程序,watch.sh stop停止程序,watch.sh restart重新启动程序.  `
> 在shell界面执行crontab -e，进入编辑页面，新开一行输入`*/1 * * * * export DISPLAY=:0 /bin/sh /home/duan/backserver/crontab_watch.sh`,该指令功能是每隔一分钟执行crontab_watch.sh脚本。
> 想要立即执行也可以在工程目录内执行`./crontab_watch.sh`
