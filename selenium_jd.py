#!/user/bin/env python
# -*- coding:utf-8 -*-

'''
    title: 京东商城爬虫
    author: zj
    date: 2020-04-04
'''


import time
import random
import selenium
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Spider_JD():

    # 随机休眠
    def random_sleep(self):
        time.sleep(round(random.uniform(0.5, 3), 2))

    # 初始化浏览器
    def open_browser(self):
        self.driver = webdriver.Chrome()
        # 显示等待
        self.wait = WebDriverWait(self.driver, 10)

    # 以下代码是将浏览器页面拉到最下面。
    def take_screenshot(self, driver):
        driver.execute_script("""
            (function () {
                var y = 0;
                var step = 100;
                window.scroll(0, 0);
                function f() {
                    if (y < document.body.scrollHeight) {
                        y += step;
                        window.scroll(0, y);
                        setTimeout(f, 100);
                    } else {
                        window.scroll(0, 0);
                        document.title += "scroll-done";
                    }
                }
                setTimeout(f, 1000);
            })();
        """)
        time.sleep(10)

    # 解析网页
    def parse_page(self):
        try:
            # 价格
            price_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='p-price']/strong/i")))
            prices = [price.text for price in price_list]

            # 标题
            title_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='p-name p-name-type-2']/a")))
            titles = [title.text for title in title_list]

            # 链接
            link_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='p-name p-name-type-2']/a")))
            # print link_list
            links = [link.get_attribute('href') for link in link_list]

            # 评论数
            commit_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='p-commit']/strong/a")))
            commits = [commit.text for commit in commit_list]

            # 保存数据库 略。。。。
            pass

        except selenium.common.exceptions.TimeoutException:
            print('parse_page: TimeoutException')
        except selenium.common.exceptions.StaleElementReferenceException:
            print('parse_page: StaleElementReferenceException')

    # 首页搜索
    def first_page(self):
        url = 'https://www.jd.com/'
        self.driver.get(url)
        self.random_sleep()

        input_text = self.driver.find_element_by_id("key")
        input_text.click()

        self.random_sleep()
        input_text.send_keys(u'手机')

        self.random_sleep()
        input_text.send_keys(Keys.ENTER)

    def next_page(self):
        for _ in xrange(20):
            # 下拉加载
            time.sleep(3)
            self.take_screenshot(self.driver)
            self.parse_page()
            self.driver.find_element_by_xpath("//a[@class='pn-next']").click()

    # 关闭浏览器
    def close_browser(self):
        self.driver.close()
        self.driver.quit()

    def start(self):
        try:
            self.open_browser()
            self.first_page()
            self.next_page()
        except Exception as ex:
            print ex
        finally:
            self.close_browser()

if __name__ == '__main__':
    spider=Spider_JD()
    spider.start()

