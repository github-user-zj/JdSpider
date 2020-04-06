#!/user/bin/env python
# -*- coding:utf-8 -*-

'''
    title: 京东商城爬虫
    author: zj
    date: 2020-04-05
'''
import os
import json
import time
import random
import requests
import pandas as pd
from lxml import etree
import jieba

class Spider_JD():
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 
        }
        # 初始化ref
        self.ref = ""

    def random_sleep(self):
        time.sleep(round(random.uniform(0.5, 2), 2))

    # 记录错误日志
    def log(self, msg, err):
        pass
    
    # get 封装
    def get(self,url, params=None):
        # 如果失败则经常重试
        for _ in xrange(3):
            try:
                # TODO 参数
                res = self.session.get(url, params=params, headers=self.headers, timeout=20)
                res.encoding = "utf-8"
                if res.ok:
                    return 0, res
            except Exception as e:
                err_msg = u"记录错误日志"
                self.log(err_msg, e)
        else:
            self.log(u"三次都失败，记录日志到MongoDB", "")
            return 1, ""

    # 1、首页信息
    def get_first(self, keyword):
        url = "https://www.jd.com/"
        
        code, res = self.get(url, None)
        if code == 1:
            return ""

        # 1、访问首页
        url = "https://search.jd.com/Search"
        params = {
            "keyword":keyword,
            "wq":keyword,
            "enc": "utf-8",
            "pvid": "" 
        }

        code, res = self.get(url, params)
        if code == 1:
            return ""
        self.headers["Referer"] = res.url
        self.headers["X-Requested-With"] = "XMLHttpRequest"
        
        df = self.parse_html(res.text)
        df02 = self.get_comment(df["pid"].tolist())
        return pd.merge(df,df02,on='pid')

    # 2、下拉刷新数据下半部分
    def drop_down(self, keyword, i):
        url = "https://search.jd.com/s_new.php"    
        params = {
            "keyword":keyword,
            "wq":keyword,
            "enc": "utf-8",
            "page":2*i,
            "qrst":1,
            "rt":1,
            "log_id": "1585987707.27615",
            "s":(2*i-1)*27, # 起始页面
            "scrolling":"y",
            "show_items":"100010300500,100008350534,100001491563,100011333796,100004245926,65788316354,37302116874,100008348506,100003489883,6069878,30412009531,5089273,55652232091,100007411764,100008348528,50553927840,56630299337,65545304296,42743865275,47601961827,7438288,100011516604,57050067815,100011497126,57698864720,43120394667,52280024497,100000322417,34871707227,66361273716",
            "stop":"1",
            "tpl":"3_M",
            "vt":"2",
        }

        code, res = self.get(url, params)
        if code == 1:
            return res 
     
        df = self.parse_html(res.text)
        df02 = self.get_comment(df["pid"].tolist())
        df = pd.merge(df,df02,on='pid')

        self.headers["  "] = res.url
        return df

    # 3、下一页的上半部分
    def get_next(self, keyword, i):
        url = "https://search.jd.com/s_new.php"
        params = {
                "keyword":keyword,
                "enc":"utf-8",
                "qrst":"1",
                "rt":"1",
                "stop":"1",
                "vt":"2",
                "wq":keyword,
                "page":2*i+1,
                "s":2*i*27,
                "click":"0",
            }
        code, res = self.get(url, params)
        if code == 1:
            return res

        # with open("data.html", "w") as f:
        #     f.write(res.text.encode("utf-8"))
        self.headers["Referer"] = res.url
        
        df = self.parse_html(res.text)
        df02 = self.get_comment(df["pid"].tolist())
        df = pd.merge(df,df02,on='pid')

        self.headers["Referer"] = res.url
        return df
     
    # 4、评论数，网站是单独请求的
    def get_comment(self, pid_list):
        pids = str(pid_list).replace("['", "").replace("'", "").replace(" ", "").replace("]", "")
        url = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds={}&callback=&_=".format(pids)
        code, res = self.get(url)
        if code == 1:
            return res 
        #with open("data.html", "w") as f:
        #    f.write(res.text.encode("utf-8"))
        
        df02 = pd.DataFrame(columns=('pid', 'count'))
        commont_json = res.json()
        for commont in commont_json["CommentsCount"]:
            df02 = df02.append({'pid':str(commont["ProductId"]), 'count': commont["CommentCount"]}, ignore_index=True)

        return df02

    # 5、解析网页：
    def parse_html(self, html):
        htmltree = etree.HTML(html)
        trs = htmltree.xpath('//*[@class="gl-item"]')
        
        df = pd.DataFrame(columns=('pid', 'price', 'title', 'href'))
        for tr in trs:
            # 价格
            price = tr.xpath('./div[@class="gl-i-wrap"]/div[@class="p-price"]/strong/i/text()')
            if not len(price):
                continue
            title = tr.xpath('./div[@class="gl-i-wrap"]/div[@class="p-name p-name-type-2"]/a/@title')
            pid = tr.xpath('@data-pid')
            href =  tr.xpath('./div[@class="gl-i-wrap"]/div[@class="p-name p-name-type-2"]/a/@href')
            df = df.append({'pid':str(pid[0]), 'title':title[0], 'price':price[0], 'href': href[0]}, ignore_index=True)
        
        return df

    # 6、爬虫开始
    def start(self):
        keyword = u"手机"
        
        result = pd.DataFrame(columns=('pid', 'price', 'title', 'href', 'count'))

        result = pd.concat([result, self.get_first(keyword)],ignore_index=True)  
        '''
          2、访问接下来的页面
            2.1、访问下拉页面
            2.2、翻页之后的上半页
        
        '''
        
        for i in range(1,50):
            # 下拉加载  self.drop_down(keyword,i)
            # 翻页  self.get_next(keyword,i)
            result = pd.concat([result,self.drop_down(keyword,i), self.get_next(keyword,i)],ignore_index=True)  

            print u"第", i, u"页"
            self.random_sleep()
        # print result
        result.to_csv("test.csv",index=False,sep=',', encoding = 'utf-8')

    # 7、简单统计, 高频的词，均价
    def simple_count(self):
        phone_dict = {}

        df = pd.read_csv("test.csv", encoding='utf-8')
        title_list =df["title"].tolist()
        
        for title in title_list:
            title = title.encode("utf-8")
            title = title.replace("，", "").replace(" ", "").replace("！", "").replace("【", "").replace("】", "")
            seg_list = jieba.cut(title, cut_all=False)   # 精确模式 
            for word in seg_list:
                if phone_dict.has_key(word):
                    phone_dict[word]+=1
                else:
                    phone_dict[word]=1

        a1 = sorted(phone_dict.items(),key = lambda x:x[1],reverse = True)
        # for word in a1[:50]:
        #     print word[0], word[1]
        
        avg_price = df['price'].sum()/df.shape[0]
        print u"手机均价",round(avg_price,2)


'''
    苹果、荣耀、耳机等出现的频率较高。

'''

if __name__ == '__main__':
    spider=Spider_JD()
    # spider.start()
    spider.simple_count()
    


