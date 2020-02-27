#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import tkinter as tk
import threading
from PIL import Image, ImageTk
import time
from strictly_func_check import strictly_func_check
import LoggingQueue

import Config

class DisplayClass():
    def __init__(self:object, cameraList:list)->None:
        self.__cameraList = cameraList
        self.__windowOK = False
        self.__log = LoggingQueue.LoggingProducer().getlogger()
        
        config = Config.Config()
        self.__saveImagePath = config.get("CONFIG", "SAVE_IMAGE_DIR")

        t = threading.Thread(target = self.__WindowShowThread, args = [])
        t.setDaemon(False)
        t.start()
       
    '''根据屏幕尺寸设置图片的大小'''
    @strictly_func_check
    def __resize(self:object, w:int, h:int, w_box:int, h_box:int, pil_image:object)->object:
        '''
        __resize a pil_image object so it will fit into
        a box of size w_box times h_box, but retain aspect ratio
        对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例
        '''
        f1 = 1.0 * w_box / w # 1.0 forces float division in Python2
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)

    @strictly_func_check
    def show(self:object, infodict:dict, imgName:str)->None:
        '''根据名字找到图片的位置'''
        try:
            namestr = "{}/{}/{}/{}/{}/{}".format(self.__saveImagePath, infodict["city"], infodict["park"], infodict["server"], infodict["camerano"], imgName)
            #self.__log.info("Ready Show Image: %s" % namestr)

            img_open = Image.open(namestr)
            old_w, old_h = img_open.size
            width = int(infodict["Window"]["width"], 10) 
            height = int(infodict["Window"]["height"], 10) 
            image_resized = self.__resize(old_w, old_h, width, height, img_open)
            img_jpg = ImageTk.PhotoImage(image_resized)
            infodict["Window"]["imageLabel"].config(image = img_jpg)
            infodict["Window"]["imageLabel"].image = img_jpg
        except Exception as e:
            self.__log.error(f'Display ==> __showImg has error:{e.args}')

    ''' 
    创建一个新的线程来专门显示图片
    '''
    def __WindowShowThread(self):
        try:
            '''创建根窗口并进行隐藏'''
            self.__windowOK = False
            root = tk.Tk()
            root.withdraw()
            '''创建子窗口'''
            for camera in self.__cameraList:
                top = tk.Toplevel(root)
                top.attributes("-fullscreen", True)
                top.attributes("-topmost",True)
                width = int(camera["Window"]["width"], 10)
                height = int(camera["Window"]["height"], 10)
                pos = int(camera["Window"]["no"]) * width
                size = "{}x{}+{}+{}".format(width, height, pos, 0)
                top.geometry(size)
                img_label = tk.Label(top)
                img_label.pack()
                camera["Window"]["imageLabel"] = img_label
                self.__log.info("f'Display ==> Create New TopLevel:Size = %s" % size)
            self.__windowOK = True
            root.update()
            root.mainloop()
        except Exception as e:
            self.__log.error(f'Display ==> __WindowShowThread error:{e.args}')
            self.__windowOK = False

    @strictly_func_check
    def check(self:object)->bool:
        count = 0
        while True:
            time.sleep(1)
            if self.__windowOK == True:
                return True
            else:
                count = count + 1
            if count > 5:
                return False

