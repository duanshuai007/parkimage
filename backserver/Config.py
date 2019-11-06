#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import configparser

class Config():
    rootdir = ''
    config = None

    def __init__(self):
        self.rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config = configparser.ConfigParser()
        self.config.read(self.rootdir + "/config.ini")
        pass

    def get(self, string, substring):
        try:
            ret = self.config[string][substring]
            if string == "CONFIG":
                ret = self.rootdir + '/' + ret
            return ret
        except Exception as e:
            print("Config get error")
            print(e.args)
            return ''

if __name__ == '__main__':
    c = Config()
    r = c.get("NAS", "USERNAME")
    print(r)
    pass
