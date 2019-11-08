
#/usr/bin/env python3
#-*- coding:utf-8 -*-

val=b'\x00'

print(type(val))
if type(val) is bytes:
    print("suce")

val=b'wanda\x00\x00\x00'
print(val)
print(str(val, encoding="utf-8"))

ll = ['1', 'had', 'duan', 'mama']

for val in ll:
    if val == 'had':
        ll.remove(val)
print(ll)
