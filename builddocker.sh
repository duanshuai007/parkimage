#!/bin/bash

tar -zcvf backserver.tar.gz backserver

docker build -t mypark:v3 .

rm backserver.tar.gz
