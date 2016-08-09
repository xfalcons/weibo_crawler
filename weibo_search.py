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

# Global debug flag
DEBUG = False

def main():
    parser = OptionParser()
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print debug messages to stdout")

    (options, args) = parser.parse_args()
    global DEBUG
    DEBUG = options.debug

    search = {
        'hot' : {
            'name' : 'hot',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=all',
            'website_id' : '03',
            'category_id' : '01',
        },
        'popular' : {
            'name' : 'popular',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=films',
            'website_id' : '03',
            'category_id' : '02',
        },
        'person' : {
            'name' : 'person',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=person',
            'website_id' : '03',
            'category_id' : '03',
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

        # 等待：   
        time.sleep(2)
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)

        for k, v in search.items():
            getSearch(
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
        msg = "[%s]微博热门搜索- Runtime Error. %s" % (socket.gethostname(), traceback.format_exc())
        sendNotification(msg)

# End of main

def getSearch(display, driver, name, url, website_id, category_id):
    global DEBUG
    weiboUrlBase = url
    resultLists = []
    datetimeTag = datetime.now().isoformat()

    # Debugging file
    filenameBase = 'debug_page'

    # initialize default value for output data
    ranking = ''
    keyword = ''       
    content = 'null'
    search_index = 'null'
    search_trend = 'null'
    tag_type = 'null'
    type_id = 'null'
    datecol = datetime.now().strftime('%Y%m%d')
    internal_ranking = 0
    retry = 5

    weiboUrl = weiboUrlBase
    pageContent = ''
    print "Crawling %s, url: %s" % (name, url,)

    while retry > 0:
        try:
            driver.get(url)
            time.sleep(7)
            domHtmlContent = driver.find_element_by_tag_name('html')
            # get origin html content
            pageContent = domHtmlContent.get_attribute('innerHTML')
        except TimeoutException:  
            print 'Time out after 30 seconds when loading page'  
            driver.execute_script('window.stop()') #当页面加载时间超过设定时间，通过执行Javascript来stop加载，即可执行后续动作

        if pageContent is None:
            if retry == 0:
                msg = "[%s]微博热搜榜(%s)- Browser renderring error，快來看看（%s）" % (socket.gethostname(), name, datetimeTag,)
                sendNotification(msg)
                print "微博热搜榜(%s)- Browser renderring error，快來看看" % (name,)
                return            
            else:
                retry-=1
                print "Retrying after 60s..."
                time.sleep(60)
                continue

        soup = BeautifulSoup(pageContent, 'lxml')
        rankLists = soup.find_all('tr', attrs={"action-type":"hover"})
        print 'Count: %d' % len(rankLists)
        if len(rankLists) <= 0:
            if retry == 0:
                writeToTempFile('search.html', pageContent)
                msg = "[%s]微博热搜榜(%s)-網頁解析錯誤，快來看看（%s）" % (socket.gethostname(), name, datetimeTag,)
                sendNotification(msg)
                print "微博热搜榜(%s)-網頁解析錯誤，快來看看" % (name,)
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

        ranking = i.find('td', class_='td_01').find('em')
        if ranking is None:
            continue
        else:
            ranking = ranking.string.strip()

        keyword = i.find('td', class_='td_02').find('a')
        if keyword is None:
            continue
        else:
            keyword = keyword.string.strip()
            keyword = keyword.replace("\t", "").replace(" ", "")

        search_index = i.find('td', class_='td_03')
        if search_index is None:
            continue
        else:
            search_index = search_index.string.strip()

        search_trend = i.find('td', class_='td_04').find('span')
        if search_trend is None:
            continue
        else:
            search_trend = str(search_trend)

        # Extract percentage from td_04
        recond = re.compile('.*?width:(\d*)%.*')
        search_trend = recond.search(search_trend).group(1)

        if DEBUG:
            print '==================================='
            print 'Rank: %s' % ranking
            print 'Topic: %s' % keyword
            print '==================================='

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
        data = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (website_id, category_id, ranking, keyword, content, search_index, search_trend, tag_type, type_id,)
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
        os.mkdir('output')
    filename = 'output/weibo_search'
    with open(filename, 'a') as out_file:
        out_file.write(("\n".join(listData).encode('UTF-8')))
        out_file.write("\n")

def removeFile():
    if not os.path.exists('output'):
        os.path.mkdir('output')
    filename = 'output/weibo_search'
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
