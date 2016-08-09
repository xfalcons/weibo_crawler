#! /usr/bin/env python  
# -*- coding: utf-8 -*-  
  
import sys  
import platform
import socket
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
import traceback
from datetime import datetime
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode
from optparse import OptionParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display
import selenium.webdriver.chrome.service as service
from selenium.webdriver.chrome.options import Options

reload(sys)
sys.setdefaultencoding('utf-8')

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

    # 使用 Baidu Spider 的 UserAgent,  微博会放行
    # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0 Chrome/20.0.1132.57 Safari/536.11'}  
    useragent = "user-agent=Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"
    removeFile()

    try:
        # Prepare display and driver for Chrome headless browser
        display = Display(visible=0, size=(800, 600))
        display.start()
        [linux_dist, linux_ver, linux_rel] = platform.linux_distribution()

        if linux_dist.lower() == 'centos' and linux_ver == '6.2':
            profile = webdriver.FirefoxProfile()
            profile.set_preference("general.useragent.override", useragent)
            driver = webdriver.Firefox(profile)
        else:
            opts = Options()
            opts.add_argument(useragent)
            driver = webdriver.Chrome(chrome_options=opts)

        time.sleep(2)
        # 等待：   
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)

        for k, v in hotTopic.items():
            getHotTopic(
                display,
                driver,
                v['name'], 
                v['url'],
                v['website_id'],
                v['category_id']
                )

        driver.quit()
        display.stop()
    except:
        traceback.print_exc()
        msg = "[%s]微话题- Runtime Error. %s" % (socket.gethostname(), traceback.format_exc())
        sendNotification(msg)

# End of main

def getHotTopic(display, driver, name, url, website_id, category_id):
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
    search_index = 'null'
    search_trend = 'null'
    tag_type = 'null'
    type_id = 'null'
    read_times = 'null'
    host = 'null'
    datecol = datetime.now().strftime('%Y%m%d')
    retry = 5

    for pnum in range(1, numberOfPageToCrawl):
        internal_ranking = 0
        while retry > 0:
            weiboUrl = weiboUrlBase + `pnum`
            pageContent = ''
            print 'Crawling(%s) : %s' % (name, weiboUrl,)

            try:
                driver.get(weiboUrl)
                time.sleep(7)
                domHtmlContent = driver.find_element_by_tag_name('html')
                # get origin html content
                pageContent = domHtmlContent.get_attribute('innerHTML')
            except TimeoutException:  
                print 'Time out after 30 seconds when loading page'  
                driver.execute_script('window.stop()') #当页面加载时间超过设定时间，通过执行Javascript来stop加载，即可执行后续动作

            if pageContent is None:
                if retry == 0:
                    msg = "[%s]微話題(%s)- Browser renderring error，快來看看（%s）" % (socket.gethostname(), name, datetimeTag,)
                    sendNotification(msg)
                    print "微話題(%s)- Browser renderring error，快來看看" % (name,)
                    return
                else:
                    retry-=1
                    print "Retrying after 60s..."
                    time.sleep(60)
                    continue

            soup = BeautifulSoup(pageContent, 'lxml')
            rankLists = soup.find_all('li', class_='pt_li')
            print 'Count: %d' % len(rankLists)
            if len(rankLists) <= 0:
                if retry == 0:
                    writeToTempFile('topic.html', pageContent)
                    msg = "[%s]微話題(%s)-網頁解析錯誤，快來看看（%s）" % (socket.gethostname(), name, datetimeTag,)
                    sendNotification(msg)
                    print "微話題(%s)-網頁解析錯誤，快來看看" % (name,)
                    return
                else:
                    retry-=1
                    print "Retrying after 60s..."
                    time.sleep(60)
                    continue
            else:
                break

            # end of while retry

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
                content = content.string.strip().replace('\n', ' ').replace('\r', ' ')
            else:
                content = 'null'

            keyword = i.find('div', class_='pic_box').find('img').get('alt')
            if keyword is None:
                continue
            else:
                keyword = keyword.replace("\t", "").replace(" ", "")

            subinfo = i.find('div', class_='subinfo')
            if subinfo is None:
                continue

            read_times = subinfo.find('span', class_='number')
            if read_times is None:
                continue
            read_times = read_times.string.strip()

            # Get host from subinfo
            host = subinfo.find('a')
            if host is not None:
                host = host.string.strip()
            else:
                host = 'null'

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

            # Format ranking to page-ranking like '01-03'
            ranking = str(pnum).zfill(2) + '-' + str(ranking).zfill(2)
            search_index = read_times

            data = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (website_id, category_id, ranking, keyword, content, search_index, search_trend, tag_type, type_id, read_times, host,)
            resultLists.append(data)

    # for idx, val in enumerate(resultLists):
    #     print idx+1, val
    for rec in resultLists:
        print rec

    # write result set to file
    writeToFile(resultLists)

# 將錯誤訊息，回報到 datainside 的瀑布裡，通知相關人員處理
def sendNotification(msg):
    c = pycurl.Curl()
    c.setopt(pycurl.URL, 'https://hooks.pubu.im/services/2p4lk91mvde9h6')
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 3)
    c.setopt(pycurl.SSL_VERIFYPEER, 0)   
    c.setopt(pycurl.SSL_VERIFYHOST, 0)

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

def writeToFile(listData):
    if not os.path.exists('output'):
        os.path.mkdir('output')
    filename = 'output/weibo_topic'
    with open(filename, 'a') as out_file:
        out_file.write(("\n".join(listData).encode('UTF-8')))
        out_file.write("\n")

def removeFile():
    if not os.path.exists('output'):
        os.path.mkdir('output')
    filename = 'output/weibo_topic'
    ## check if a file exists on disk ##
    ## if exists, delete it else show message on screen ##
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except OSError, e:
            print ("Error: %s - %s." % (e.filename,e.strerror))

def writeToTempFile(filename, content):
    if not os.path.exists('debug'):
        os.mkdir('debug')
    filename = 'debug/' + filename
    with open(filename, 'wb') as out_file:
        out_file.write(content)

if __name__ == '__main__':
    main()
