from tornado.options import define, options

define("port", default=4000, help="run on the given port", type=int)
# define("host", default="ws.weixinxk.com", help="run on the given host") #连接的host，正式
define("host", default="", help="run on the given host") #连接的host，测试
define("host_db", default="127.0.0.1", help="run on the given host_db") #db的host, redis

CONNECT_TIMEOUT = 5 #单位秒, 超时时间