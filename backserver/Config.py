#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import configparser
from functools import wraps
from strictly_func_check import strictly_func_check
'''
def positive_paramters(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        #print(f'args={args}')
        #print(f'args[1]={args[1]}')
        exception = None
        try:
            result = func(*args, **kwargs)
            assert type(args[1]) == str, "paramter 1 must be string type"
            assert type(args[2]) == str, "paramter 2 must be string type"
            return result
        except Exception as e:
            exception = e
            print(e)
        finally:
            if exception is not None:
                raise exception
                pass
    return wrapper
'''

class Config():
    rootdir = ''
    config = None

    def __init__(self):
        self.rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config = configparser.ConfigParser()
        self.config.read(self.rootdir + "/config.ini")
        pass

    #self:<class '__main__.Config'>
    @strictly_func_check
    def get(self:object, string:str, substring:str)->str:
        try:
            ret = self.config[string][substring]
            if string == "CONFIG":
                ret = self.rootdir + '/' + ret
            return ret
        except Exception as e:
            print("Config get error")
            #print(e.args)
            return ''

if __name__ == '__main__':
    c = Config()
    r = c.get("NAS", "USERNAME")
    print(r)
    pass
