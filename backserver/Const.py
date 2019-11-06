import sys


class Const:
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't change const %s value!" % name)
        if not name.isupper():
            raise self.ConstCaseError("const %s is not all letters are capitalized" % name)
        self.__dict__[name] = value


sys.modules[__name__] = Const()

### 日志配置 ###

#Const.FORMATTER_FMT = '%(asctime)s.%(msecs)03d:[%(levelname)s][%(processName)s-%(threadName)s] %(message)s'
Const.FORMATTER_FMT = '%(asctime)s.%(msecs)03d:[%(levelname)s]:%(message)s'
#Const.FORMATTER_FMT = '%(asctime)s.%(msecs)03d [%(levelname)s][%(filename)s:%(lineno)d] %(message)s'
Const.FORMATTER_DATE_FMT = '%Y-%m-%d %H:%M:%S'
Const.WORK_LOGGER = 'work'

### 停车场前端配置 ###

Const.RUN_MODE = 'tcp'  # tcp: 通过TCP通讯方式接收图片；pull: 通过主动拉取方式获取图片
Const.CITY = 'beijing'  # 最大长度8位
Const.PARK = 'wanda'    # 最大长度8位
Const.SERVER = 1        # 取值范围0~255
Const.TOKEN = 'MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ='

Const.WS_LOGIN_REQUEST = 1
Const.WS_LOGIN_RESPONSE = 2
Const.WS_RECOGNITION_REQUEST = 3
Const.WS_RECOGNITION_RESPONSE = 4
Const.WS_MODE_NORMAL = 0
Const.WS_MODE_BZ2 = 1
Const.WS_STATUS_SUCCESS = 0
Const.WS_STATUS_FAILED = 1
Const.WS_STATUS_READY = 2
Const.WS_STATUS_REFUSE = 3
Const.WS_STATUS_GOON = 4
Const.WS_STATUS_STOP = 5

# WS登录消息
Const.LOGIN_JSON = {
    "type": "request",
    "content": {
        "category": "login",
        "token": "MTU5MzE2NjUyMC40OTM4NzM2OjYzMjA5NzNjYzRiYTgwOWJkNDhlYTMwMGI0YWQxYThiMWVmNjI1MzQ=",
        "city": Const.CITY,
        "park": Const.PARK,
        "server": Const.SERVER
    }
}

# WS发送照片消息
Const.SEND_PHONE_INFO = {
    "type": "",
    "image": {
        "camerano": "",
        "identify": "",
        "md5": "",
        "content": ""
    }
}

