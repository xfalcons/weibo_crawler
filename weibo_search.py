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
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display
import selenium.webdriver.chrome.service as service


def main():
    search = {
        'hot' : {
            'name' : 'hot',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=all',
            'website_id' : '03',
            'category_id' : '01',
        },
    }

    #热搜榜-热点
    getSearch(
        search['hot']['name'], 
        search['hot']['url'],
        search['hot']['website_id'],
        search['hot']['category_id']
        )

def getSearch(name, url, website_id, category_id):
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
    numberOfPageToCrawl = 2
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
    datecol = datetime.now().strftime('%Y%m%d')
    internal_ranking = 0

    for pnum in range(1, numberOfPageToCrawl):
        weiboUrl = weiboUrlBase + `pnum`
        outputFileName = filenameBase + `pnum` + '.html'

        # req2 = urllib2.Request(
        #     url = weiboUrl,
        #     headers = headers
        # )
        # try:
        #     page = urllib2.urlopen(req2)
        #     pageContent = page.read()
        #     # Output to file for debuging
        #     # This html doc using javascript to load content, so we need to load it into webdriver
        #     # to get complete html doc
        #     writeToTempFile(outputFileName, pageContent)
        # except urllib2.HTTPError, e:
        #     msg = "'微博热搜榜(%s)'-網頁回应錯誤，快來看看（%s, %s）" % (name, e.code, e.reason,)
        #     sendNotification(msg)
        #     print "'微博热搜榜(%s)'-網頁回应錯誤，快來看看（%s, %s）" % (name, e.code, e.reason,)
        #     return
        # except urllib2.URLError, e:
        #     msg = "'微博热搜榜(%s)'-找不到网址(%s)，快來看看（%s）" % (name, weiboUrl, e.reason,)
        #     sendNotification(msg)
        #     print "'微博热搜榜(%s)'-找不到网址(%s)，快來看看（%s）" % (name, weiboUrl, e.reason,)
        #     return

        driver = webdriver.Chrome()
        # 等待：   
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        try:
            driver.get(url)
            time.sleep(10)
            domHtmlContent = driver.find_element_by_tag_name('html')
            # get origin html content
            pageContent = domHtmlContent.get_attribute('innerHTML')
        except TimeoutException:  
            print 'Time out after 30 seconds when loading page'  
            driver.execute_script('window.stop()') #当页面加载时间超过设定时间，通过执行Javascript来stop加载，即可执行后续动作
            driver.quit()
        except:
            driver.quit()

        # close browser
        driver.quit()

        # pageContent = page.read()
        # if debug == True:
        #     print '[DEBUG] Output file to ', outputFileName
        #     fw = open(outputFileName, 'w')
        #     fw.write(pageContent)  
        #     fw.close()  

        soup = BeautifulSoup(pageContent, 'lxml')
        rankLists = soup.find_all('tr', attrs={"action-type":"hover"})
        print 'Count: %d' % len(rankLists)
        if len(rankLists) <= 0:
            msg = "'微博热搜榜(%s)'-網頁解析錯誤，快來看看（%s）" % (name, datetimeTag,)
            sendNotification(msg)
            print "'微博热搜榜(%s)'-網頁解析錯誤，快來看看" % (name,)
            os._exit(-1)

        for i in rankLists:
            internal_ranking += 1
            print '==================================='
            print i

            ranking = i.find('td', class_='td_01').find('em')
            if keyword is None:
                continue
            else:
                ranking = ranking.string

            keyword = i.find('td', class_='td_02').find('a')
            if keyword is None:
                continue
            else:
                keyword = keyword.string

            search_index = i.find('td', class_='td_03')
            if search_index is None:
                continue
            else:
                search_index = search_index.string

            search_trend = i.find('td', class_='td_04').find('span')
            if search_trend is None:
                continue
            else:
                search_trend = search_trend.string


            if debug:
                print '==========================='
                print 'Rank: %s' % ranking
                print 'Topic: %s' % keyword
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
            data = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (website_id, category_id, ranking, keyword, content, search_index, search_trend, tag_type, type_id, datecol,)
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
        os.mkdir('output')
    filename = 'output/weibo_search_' + filename
    with open(filename, 'wb') as out_file:
        out_file.write(("\n".join(listData).encode('UTF-8')))

def writeToTempFile(filename, content):
    if not os.path.exists('debug'):
        os.mkdir('debug')
    filename = 'debug/' + filename
    with open(filename, 'wb') as out_file:
        out_file.write(content)

if __name__ == '__main__':
    main()
