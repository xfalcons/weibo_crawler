#! /usr/bin/env python  
# -*- coding: utf-8 -*-  
  
import sys  
import platform
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
DEBUG = False

def main():
    parser = OptionParser()
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print debug messages to stdout")

    (options, args) = parser.parse_args()
    global DEBUG
    DEBUG = options.debug

    hot = {
        'variety' : {
            'name' : 'variety',
            'url' : 'http://d.weibo.com/102803_ctg1_4688_-_ctg1_4688?page=',
            'website_id' : '01',
            'category_id' : '00',
        },
        'star' : {
            'name' : 'star',
            'url' : 'http://d.weibo.com/102803_ctg1_4288_-_ctg1_4288?page=',
            'website_id' : '01',
            'category_id' : '01',
        },
        'show' : {
            'name' : 'show',
            'url' : 'http://d.weibo.com/102803_ctg1_2488_-_ctg1_2488?page=',
            'website_id' : '01',
            'category_id' : '02',
        },
        'movie' : {
            'name' : 'movie',
            'url' : 'http://d.weibo.com/102803_ctg1_3288_-_ctg1_3288?page=',
            'website_id' : '01',
            'category_id' : '03',
        },
        'comic' : {
            'name' : 'comic',
            'url' : 'http://d.weibo.com/102803_ctg1_2388_-_ctg1_2388?page=',
            'website_id' : '01',
            'category_id' : '04',
        },
    }

    # 使用 Baidu Spider 的 UserAgent,  微博会放行
    # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0 Chrome/20.0.1132.57 Safari/536.11'}  
    useragent = "user-agent=Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"

    # Prepare display and driver for Chrome headless browser
    try:
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

        for k, v in hot.items():
            getHot(
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
        msg = "'发现热门微博'- Runtime Error. %s" % traceback.format_exc()
        sendNotification(msg)

# End of main

def getHot(display, driver, name, url, website_id, category_id):
    global DEBUG
    # Get 2 page of hot_weibo
    numberOfPageToCrawl = 3
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
        pageContent = ''
        js="window.scrollTo(0, document.body.scrollHeight);"
        try:
            print "Retrive url: %s" % (weiboUrl,)
            driver.get(weiboUrl)
            print "Waiting page ..."
            time.sleep(7)
            print "Scroll down 1st ..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 2nd ..."
            driver.execute_script(js)
            time.sleep(4)
            print "Scroll down 3rd ..."
            driver.execute_script(js)
            time.sleep(4)
            # print "Locate 'load more' button ..."
            # loadmore = driver.find_element_by_class_name("WB_cardmore_noborder")
            # if loadmore is not None:
            #     print "Got 'load more' button"
            #     loadmore.click()
            #     time.sleep(4)
            # else:
            #     print "Can NOT got 'load more' button"

            # print "Scroll down 4th..."
            # driver.execute_script(js)
            # time.sleep(4)
            # print "Scroll down 5th..."
            # driver.execute_script(js)
            # time.sleep(4)
            # print "Scroll down 6th..."
            # driver.execute_script(js)
            # time.sleep(4)
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
            writeToTempFile('hot.html', pageContent)
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
            if detail is None:
                continue

            wb_info = detail.find('div', class_='WB_info')
            if wb_info is None:
                continue

            keyword = wb_info.find('a')
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

            elements = socialinfo.find('span', attrs={'node-type':'like_status'})
            if elements is not None:
                comment_times = elements.find('em')
                if comment_times is not None:
                    comment_times = comment_times.get_text()

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

def writeToFile(filename, listData):
    if not os.path.exists('output'):
        os.mkdir('output')
    filename = 'output/weibo_hot_' + filename
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
