#!/bin/bash

tar -zcvf backserver.tar.gz backserver

docker build -t mypark:v20200225 .

rm backserver.tar.gz
