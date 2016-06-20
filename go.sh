#!/bin/bash

host=`hostname`
if [[ $host == *"logstat.qingdao.youku" ]]; then
	cd /home/up/weibo_crawler
	source ./bin/activate
	cd weibo_crawler
	export LANG=en_US.UTF8
	echo "Running on production env"
else
	cd /home/kevin_luo/dev/weibo_crawler
	echo "Running on beta env"
fi

./weibo_topic.py --debug --page 10
./weibo_hot.py --debug
./weibo_search.py --debug

# Force to finish firefox process to avoid resouces occupied.
sleep 30
ps auxwww | grep -i firefox | grep -v grep | awk '{print $2}' | xargs kill -9