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


DEBUG = False

def main():
    parser = OptionParser()
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print debug messages to stdout")

    (options, args) = parser.parse_args()
    global DEBUG
    DEBUG = options.debug

    faxian = {
        'star' : {
            'name' : 'star',
            'url' : 'http://d.weibo.com/102803_ctg1_4288_-_ctg1_4288?from=faxian_hot&mod=fenlei',
            'website_id' : '01',
            'category_id' : '01',
        },
        'popular' : {
            'name' : 'popular',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=films',
            'website_id' : '01',
            'category_id' : '02',
        },
        'person' : {
            'name' : 'person',
            'url' : 'http://s.weibo.com/top/summary?cate=total&key=person',
            'website_id' : '01',
            'category_id' : '03',
        },
    }

    # Prepare display and driver for Chrome headless browser
    display = Display(visible=0, size=(800, 600))
    display.start()
    driver = webdriver.Chrome()
    time.sleep(2)
    # 等待：   
    driver.implicitly_wait(30)
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)

    #热搜榜-热点
    getFaxian(
        display,
        driver,
        faxian['star']['name'], 
        faxian['star']['url'],
        faxian['star']['website_id'],
        faxian['star']['category_id']
        )

    # #热搜榜-名人
    # getSearch(
    #     display,
    #     driver,
    #     search['popular']['name'], 
    #     search['popular']['url'],
    #     search['popular']['website_id'],
    #     search['popular']['category_id']
    #     )

    # #热搜榜-名人
    # getSearch(
    #     display,
    #     driver,
    #     search['person']['name'], 
    #     search['person']['url'],
    #     search['person']['website_id'],
    #     search['person']['category_id']
    #     )

    driver.quit()
    display.stop()

# End of main

def getFaxian(display, driver, name, url, website_id, category_id):
    global DEBUG
    # 使用 Baidu Spider 的 UserAgent,  微博会放行
    # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0 Chrome/20.0.1132.57 Safari/536.11'}  
    headers = {'User-Agent':'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'}
    numberOfPageToCrawl = 2
    weiboUrlBase = url
    resultLists = []
    datetimeTag = datetime.now().isoformat()

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
    like_times = ''
    forward_times = ''
    comment_times = ''
    datecol = datetime.now().strftime('%Y%m%d')
    internal_ranking = 0

    for pnum in range(1, numberOfPageToCrawl):
        weiboUrl = weiboUrlBase + `pnum`
        outputFileName = filenameBase + `pnum` + '.html'
        pageContent = ''
        js="window.scrollTo(0, document.body.scrollHeight);"
        try:
            print "Retrive url..."
            driver.get(url)
            print "Waiting..."
            time.sleep(7)
            print "Scroll down 1st..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 2nd..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 3rd..."
            driver.execute_script(js)
            time.sleep(4)
            print "Locate 'load more' button ..."
            loadmore = driver.find_element_by_class_name("WB_cardmore_noborder")
            if loadmore is not None:
                print "Got 'load more' button"
                loadmore.click()
                time.sleep(4)
            else:
                print "Can NOT got 'load more' button"

            print "Scroll down 4th..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 5th..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 6th..."
            driver.execute_script(js)
            time.sleep(4)
            domHtmlContent = driver.find_element_by_tag_name('html')
            # get origin html content
            pageContent = domHtmlContent.get_attribute('innerHTML')
        except TimeoutException:
            # driver.refresh()
            # time.sleep(7)
            print 'Exception'
            domHtmlContent = driver.find_element_by_tag_name('html')
            pageContent = domHtmlContent.get_attribute('innerHTML')
            print 'Time out after 30 seconds when loading page'  
            driver.execute_script('window.stop()') #当页面加载时间超过设定时间，通过执行Javascript来stop加载，即可执行后续动作

        if pageContent is None:
            msg = "'发现热门微博(%s)'- Browser renderring error，快來看看（%s）" % (name, datetimeTag,)
            sendNotification(msg)
            print "'发现热门微博(%s)'- Browser renderring error，快來看看" % (name,)
            continue            

        soup = BeautifulSoup(pageContent, 'lxml')
        rankLists = soup.find_all('div', class_='WB_feed_type')
        print 'Count: %d' % len(rankLists)
        if len(rankLists) <= 0:
            msg = "'发现热门微博(%s)'-網頁解析錯誤，快來看看（%s）" % (name, datetimeTag,)
            sendNotification(msg)
            print "'发现热门微博(%s)'-網頁解析錯誤，快來看看" % (name,)
            os._exit(-1)

        for i in rankLists:
            internal_ranking += 1
            ranking = internal_ranking
            print 'parsing: ', str(internal_ranking)
            #print '==================================='
            #print i

            detail = i.find('div', class_='WB_feed_detail')
            keyword = detail.find('div', class_='WB_info').find('a')
            if keyword is None:
                continue
            else:
                keyword = keyword.get_text().strip()

            content = detail.find('div', class_='WB_text')
            if content is not None:
                content = content.get_text()

            socialinfo = i.find('div', class_='WB_feed_handle')

            p = re.compile('.*?(\d+).*')
            elements = socialinfo.find('span', attrs={'node-type':'forward_btn_text'})
            if elements is not None:
                forward_times = elements.find_all('em')
                if forward_times is not None:
                    forward_times = forward_times[1].get_text()

            elements = socialinfo.find('span', attrs={'node-type':'comment_btn_text'})
            if elements is not None:
                comment_times = elements.find_all('em')
                if comment_times is not None:
                    comment_times = comment_times[1].get_text()

            if DEBUG:
                print '==========================='
                print 'Rank: %s' % ranking
                print 'Topic: %s' % keyword
                print 'content: %s' % content
                print 'Forward: %s' % forward_times
                print 'Comment: %s' % comment_times                
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
            # like_times              string                                      
            # forward_times           string                                      
            # comment_times           string                                      
            # datecol                 string 
            data = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (website_id, category_id, ranking, keyword, content, search_index, search_trend, tag_type, type_id, like_times, forward_times, comment_times, datecol,)
            resultLists.append(data)

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
