#! /usr/bin/env python  
# -*- coding: utf-8 -*-  
  
import sys  
import urllib  
import urllib2  
import cookielib  
import base64  
import time
import re  
import json  
import hashlib  
import pycurl
import StringIO
import os
from datetime import datetime
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode
from optparse import OptionParser
from bs4 import BeautifulSoup

def main():
    hotTopic = {
        '24hour' : {
            'name' : '24hour',
            'url' : 'http://d.weibo.com/100803?pids=Pl_Discover_Pt6Rank__5&cfs=920&Pl_Discover_Pt6Rank__5_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__5_page=',
            'website_id' : '02',
            'category_id' : '01',
        },
        'star' : {
            'name' : 'star',
            'url' : 'http://d.weibo.com/100803_ctg1_2_-_ctg12?pids=Pl_Discover_Pt6Rank__4&cfs=920&Pl_Discover_Pt6Rank__4_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__4_page=',
            'website_id' : '02',
            'category_id' : '02',
        },
        'variety' : {
            'name' : 'variety',
            'url' : 'http://d.weibo.com/100803_ctg1_102_-_ctg1102?pids=Pl_Discover_Pt6Rank__4&cfs=920&Pl_Discover_Pt6Rank__4_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__4_page=',
            'website_id' : '02',
            'category_id' : '03',
        },
        'show' : {
            'name' : 'show',
            'url' : 'http://d.weibo.com/100803_ctg1_101_-_ctg1101?pids=Pl_Discover_Pt6Rank__4&cfs=920&Pl_Discover_Pt6Rank__4_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__4_page=',
            'website_id' : '02',
            'category_id' : '04',
        },
        'movie' : {
            'name' : 'movie',
            'url' : 'http://d.weibo.com/100803_ctg1_100_-_ctg1100?pids=Pl_Discover_Pt6Rank__4&cfs=920&Pl_Discover_Pt6Rank__4_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__4_page=',
            'website_id' : '02',
            'category_id' : '05',
        },
        'comic' : {
            'name' : 'comic',
            'url' : 'http://d.weibo.com/100803_ctg1_97_-_ctg197?pids=Pl_Discover_Pt6Rank__4&cfs=920&Pl_Discover_Pt6Rank__4_filter=hothtlist_type=1&Pl_Discover_Pt6Rank__4_page=',
            'website_id' : '02',
            'category_id' : '06',
        },
    }

    try:
        for k, v in hotTopic.items():
            getHotTopic(
                v['name'], 
                v['url'],
                v['website_id'],
                v['category_id']
                )
    except:
        traceback.print_exc()
        msg = "'发现热门微博'- Runtime Error. %s" % traceback.print_exc()
        sendNotification(msg)

def getHotTopic(name, url, website_id, category_id):
    parser = OptionParser()
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print debug messages to stdout")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    parser.add_option("-p", "--page",
                      dest="page", default=2,
                      help="don't print status messages to stdout")

    (options, args) = parser.parse_args()
    # 使用 Baidu Spider 的 UserAgent,  微博会放行
    # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0 Chrome/20.0.1132.57 Safari/536.11'}  
    headers = {'User-Agent':'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'}
    numberOfPageToCrawl = int(options.page) + 1
    weiboUrlBase = url
    resultLists = []
    datetimeTag = datetime.now().isoformat()

    debug = options.debug
    # Debugging file
    filenameBase = 'debug_page'

    # initialize default value for output data
    ranking = ''
    keyword = ''       
    content = ''
    search_index = ''
    search_trend = ''
    tag_type = ''
    type_id = ''
    read_times = ''
    host = ''
    datecol = datetime.now().strftime('%Y%m%d')
    internal_ranking = 0

    for pnum in range(1, numberOfPageToCrawl):
        weiboUrl = weiboUrlBase + `pnum`
        outputFileName = filenameBase + `pnum` + '.html'
        print 'URL:', weiboUrl
        req2 = urllib2.Request(
            url = weiboUrl,
            headers = headers
        )
        try:
            page = urllib2.urlopen(req2)
        except urllib2.HTTPError, e:
            msg = "'微話題(%s)'-網頁回应錯誤，快來看看（%s, %s）" % (name, e.code, e.reason,)
            sendNotification(msg)
            print "'微話題(%s)'-網頁回应錯誤，快來看看（%s, %s）" % (name, e.code, e.reason,)
            return
        except urllib2.URLError, e:
            msg = "'微話題(%s)'-找不到网址(%s)，快來看看（%s）" % (name, weiboUrl, e.reason,)
            sendNotification(msg)
            print "'微話題(%s)'-找不到网址(%s)，快來看看（%s）" % (name, weiboUrl, e.reason,)
            return

        pageContent = page.read()
        if debug == True:
            print '[DEBUG] Output file to ', outputFileName
            fw = open(outputFileName, 'w')
            fw.write(pageContent)  
            fw.close()  

        soup = BeautifulSoup(pageContent, 'lxml')
        rankLists = soup.find_all('li', class_='pt_li')
        print 'Count: %d' % len(rankLists)
        if len(rankLists) <= 0:
            msg = "'微話題(%s)'-網頁解析錯誤，快來看看（%s）" % (name, datetimeTag,)
            sendNotification(msg)
            print "'微話題(%s)'-網頁解析錯誤，快來看看" % (name,)
            os._exit()

        for i in rankLists:
            internal_ranking += 1
            title = i.find('div', class_='title')
            if title is None:
                continue

            # Get rank from title div
            ranking = title.find(class_=re.compile('DSC_topic.*'))
            # In the hottopic category, there is no rank info
            if ranking is not None:
                ranking = ranking.string
                if isInt(ranking) == False:
                    if ranking == 'TOP1':
                        ranking = 1
                    elif ranking == 'TOP2':
                        ranking = 2
                    elif ranking == 'TOP3':
                        ranking = 3
                    else:
                        ranking = None
                if ranking is None:
                    continue
            else:
                ranking = internal_ranking

            # Get subtitle. This data could be omit if it doesn't exist
            content = i.find('div', class_='subtitle')
            if content is not None:
                content = content.string.strip()
            else:
                content = ''

            keyword = i.find('div', class_='pic_box').find('img').get('alt')
            if keyword is None:
                continue

            subinfo = i.find('div', class_='subinfo')
            if subinfo is None:
                continue

            read_times = subinfo.find('span', class_='number')
            if read_times is None:
                continue
            read_times = read_times.string

            # Get host from subinfo
            host = subinfo.find('a')
            if host is not None:
                host = host.string.strip()
            else:
                host = ''

            if debug:
                print '==========================='
                print 'Rank: %s' % ranking
                print 'Topic: %s' % keyword
                print 'Number: %s' % read_times
                print 'Subtitle: %s' % content
                print '==========================='

            # Data Format for each record
            # website_id              string                                      
            # category_id             string                                      
            # ranking                 string                                      
            # keyword                 string                                      
            # content                 string                                      
            # search_index            string                                      
            # search_trend            string                                      
            # tag_type                string                                      
            # type_id                 string                                      
            # read_times              string                                      
            # host                    string                                      
            # datecol                 string 
            data = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (website_id, category_id, ranking, keyword, content, search_index, search_trend, tag_type, type_id, read_times, host, datecol,)
            resultLists.append(data)

    # for idx, val in enumerate(resultLists):
    #     print idx+1, val
    for rec in resultLists:
        print rec

    # write result set to file
    writeToFile(name, resultLists)

# 將錯誤訊息，回報到 datainside 的瀑布裡，通知相關人員處理
def sendNotification(msg):
    c = pycurl.Curl()
    c.setopt(pycurl.URL, 'https://hooks.pubu.im/services/2p4lk91mvde9h6')
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 3)

    post_data = {"text":msg}
    # Form data must be provided already urlencoded.
    postfields = urlencode(post_data)
    # Sets request method to POST,
    # Content-Type header to application/x-www-form-urlencoded
    # and data to send in request body.
    c.setopt(pycurl.POSTFIELDS, postfields)
    c.perform()
    c.close()
    print

def isInt(input):
    try:
        num = int(input)
    except ValueError:
        return False
    return True

def writeToFile(filename, listData):
    if not os.path.exists('output'):
        os.path.mkdir('output')
    filename = 'output/weibo_topic_' + filename
    with open(filename, 'wb') as out_file:
        out_file.write(("\n".join(listData).encode('UTF-8')))

if __name__ == '__main__':
    main()
