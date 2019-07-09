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


## 使用方法

> 在Image.py中设置PATH宏定义，这个宏定义了websocket接收到的图片以及相机识别图片保存的根目录，注意PATH不能以'\'为结尾字符。  

> 在shell界面执行crontab -e，进入编辑页面，新开一行输入`*/1 * * * * /bin/sh /home/duan/backserver/crontab_watch.sh`,该指令功能是每隔一分钟执行crontab_watch.sh脚本。
> 想要立即执行也可以在工程目录内执行`./crontab_watch.sh`
