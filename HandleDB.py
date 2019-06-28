import logging
import redis
import json

import Constant

class HandleLoginDB(object):

    def __init__(self):
        self.cache = redis.StrictRedis(Constant.options.host_db, 6379)  # 缓存换成redis了
        self.key = "userInfo"

    def store(self, token, state = "1"):
        s = self.cache.hget(self.key, str(token))  # 用hash结构保存计算结果
        logging.info("s:" + str(s))
        if s is None:
            logging.info("is none")
            self.cache.hset(self.key, str(token), str("1"))
            return True
        else:
            logging.info("s result:" + str(s.decode('utf-8')))
            if(s.decode('utf-8') == "1"):
                return False
            self.update(token, 1)
            return True
    def delete(self, token):
        self.cache.hdel(self.key, str(token))
    def update(self, token, state):
        self.cache.hset(self.key, str(token), str(state))
    def deleteAll(self):
        result = self.cache.hgetall(self.key)
        for keys, values in result.items():
            self.delete((keys.decode('utf-8')))

class ParkDB(object):
    def __init__(self):
        self.cache = redis.StrictRedis(Constant.options.host_db, 6379)  # 缓存换成redis了
        self.key = "parkInfo"

    def store(self, token, state = "1"):
        s = self.cache.hget(self.key, str(token))  # 用hash结构保存计算结果
        logging.info("s:" + str(s))
        if s is None:
            logging.info("is none")
            self.cache.hset(self.key, str(token), str("1"))
            return True
        else:
            logging.info("s result:" + str(s.decode('utf-8')))
            if(s.decode('utf-8') == "1"):
                return False
            self.update(token, 1)
            return True
    def delete(self, token):
        self.cache.hdel(self.key, str(token))
    def update(self, token, state):
        self.cache.hset(self.key, str(token), str(state))

    def deleteAll(self):
        result = self.cache.hgetall(self.key)
        for keys, values in result.items():
            self.delete((keys.decode('utf-8')))
        