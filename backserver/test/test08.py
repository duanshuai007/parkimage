#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import bz2
import binascii
import zlib

with open("/home/duan/Pictures2/pic4.jpg", "rb") as f:
    msg = f.read()
#print(msg)
    
    print('Original 1:' +  str(len(msg)))

#original_data = bytes(msg,encoding="utf-8")
    original_data = msg
    print('Original 2:' +  str(len(original_data)))

    bz2_compressed = bz2.compress(original_data, compresslevel=9)
    print('BZ2 Compressed 3:' +  str(len(bz2_compressed)))
#print(binascii.hexlify(compressed))

    zlib_compressed = zlib.compress(original_data)
    print('zlib Compressed 3:' +  str(len(zlib_compressed)))


#decompressed = bz2.decompress(compressed)
#   print('Decompressed 4:' +  str(len(decompressed)))
#print(decompressed)
