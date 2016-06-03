#!/bin/bash

host=`hostname`
if [ "$host" = "a01.spider.logstat.qingdao.youku" ]; then
	cd /home/kevin_luo/dev/weibo_crawler
	echo "Running on beta env"
else
	cd /home/up/weibo_crawler
	source ./bin/activate
	cd weibo_crawler
	export LANG=en_US.UTF8
	echo "Running on production env"
fi

./weibo_topic.py --debug --page 10
./weibo_hot.py --debug
./weibo_search.py --debug