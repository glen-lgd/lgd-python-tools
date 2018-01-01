# coding:utf-8
__author__ = 'glen'

import requests
import requests
from bs4 import BeautifulSoup
import threadpool
import threading
import logging
import re
logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger("PROXY")

class SpiderProxy(object):
    headers = {
        "Host": "www.goubanjia.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063",
        "Accept": "text/html, application/xhtml+xml, image/jxr, */*",
        "Accept-Language": "zh-Hans-CN, zh-Hans; q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection":"Keep-Alive",
    }


    thread_count = 15
    prxoy_test_url = "https://www.google.com.hk"

    def __init__(self, session_url):
        self.req = requests.session()
        self.req.get(session_url)
        logger.debug("%s"%self.req.cookies)
        import time
        time.sleep(1)
        self.proxy_can_use = {}
        self.mutex = threading.RLock()

    def get_pagesource(self, url):
        html = self.req.get(url, headers=self.headers)
        return html.content

    def getProxyFromHtml(self, html):
        bs =BeautifulSoup(html, "html.parser")
        rslt = {}
        for zzz in bs.find_all('tr'):
            ips = zzz.find_all(attrs = {"class":"ip"})
            proxy = ''
            for x in ips:
                y = x.find_all(style=re.compile(".*none.*", re.DOTALL|re.I))
                for z in y:
                    z.string = ""
                proxy =  ''.join((t for t in  x.strings))
            if not proxy.strip():
                continue
            m = zzz.find_all(title = "https代理IP")
            if m:
                rslt.setdefault("https", []).append(proxy)

            else:
                rslt.setdefault("http", []).append(proxy)
        logger.debug("proxies getted:%s"%repr(rslt))
        return rslt


    def get_all_proxy(self, url):
        data = []
        html = self.get_pagesource(url)
        # logger.debug("getted url:%s", html)
        proxyes = self.getProxyFromHtml(html)
        self.testProxy(proxyes)
        return self.proxy_can_use

    def add_proxy(self, r, rslt):
        logger.debug("add proxy:%s", rslt)
        if rslt != None:

            with self.mutex:
                if len(rslt) == 2:
                    self.proxy_can_use.setdefault(rslt[0], []).append(rslt[1])
            logger.info("success to get proxy: %s"%repr(rslt))
    def testProxy(self, proxys):
        tp = threadpool.ThreadPool(self.thread_count)
        for proxy_type, p in proxys.iteritems():
            for pp in p:
                tp.putRequest(threadpool.WorkRequest(self._testProxy, args = (proxy_type, pp), callback = self.add_proxy))
            tp.wait()

    def _testProxy(self, proxy_type, proxy):
        logger.debug("test for proxy:%s", repr((proxy_type, proxy)))
        rslt = None
        try:
            logger.debug("test for proxy:%s, %s", proxy_type, proxy)
            url = "%s://%s"%(proxy_type, proxy)
            response  = requests.get(self.prxoy_test_url, proxies = {proxy_type:url})
            if response.status_code < 300:
                rslt =  proxy_type,  proxy
        except:
            logger.exception("failed to connect to google with proxy %s", proxy)
        return rslt




session_url = 'http://www.goubanjia.com/free/gwgn/index1.shtml'
for x in xrange(1, 10):
    url = 'http://www.goubanjia.com/free/gwgn/index%d.shtml'%x
    p = SpiderProxy(session_url)
    proxy_ip = p.get_all_proxy(url)
    print "______proxy______get_______over"
    import  pprint
    pprint.pprint(proxy_ip)
