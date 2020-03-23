#!/bin/bash

tar -zcvf backserver.tar.gz backserver

docker build -t mypark:v5 .

rm backserver.tar.gz
