#!/bin/bash

tar -zcvf backserver.tar.gz backserver

docker build -t mypark:v0.5 .

rm backserver.tar.gz
