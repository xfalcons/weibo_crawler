#!/bin/bash

cd /home/kevin_luo/dev/weibo_crawler
source ./bin/activate
export LANG=en_US.UTF8
./weibo_topic.py --debug --page 10
./weibo_hot.py --debug
./weibo_search.py --debug
deactive