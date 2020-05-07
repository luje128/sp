import json
import random
import time
import requests
import urllib3
from fake_useragent import UserAgent
from lxml import etree
import sys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import re

# 加载web驱动路径
web_path = 'D:/chromedriver'

# 生成随机浏览器对象
ua = UserAgent()

username = 'weijie.wang@hdedu.com'

password = 'HD666888'


def weixin():
    # 定义chrome的配置
    option = webdriver.ChromeOptions()
    # option.add_argument('headless')
    option.add_argument('no-sandbox')
    option.add_argument('disable-dev-shm-usage')
    option.add_argument('disable-gpu')
    # 修改chrome的配置
    # prefs = {
    #     'profile.default_content_setting_values': {
    #         'images': 2,  # 限制图片加载
    #         # 'javascript': 2  # 禁用js
    #     }
    # }
    # 将变量传入
    # option.add_experimental_option('prefs', prefs)
    # 传入驱动路径，导入设置，生成webdriver.Chrome对象
    browser = webdriver.Chrome(web_path, chrome_options=option)
    # 目标地址
    login_url = 'https://mp.weixin.qq.com'
    # 加载目标地址
    browser.get(url=login_url)
    print('---获取作业信息中---')
    # 获取并加载用户框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//input[@name="account"]')))
    browser.find_element_by_xpath('//input[@name="account"]').clear()
    browser.find_element_by_xpath('//input[@name="account"]').send_keys(username)
    # 获取并加载密码框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//input[@name="password"]')))
    browser.find_element_by_xpath('//input[@name="password"]').clear()
    browser.find_element_by_xpath('//input[@name="password"]').send_keys(password)
    # 获取并加载登陆按钮
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//a[@class="btn_login"]')))
    browser.find_element_by_xpath('//a[@class="btn_login"]').click()
    print("请拿手机扫码二维码登录公众号!")
    time.sleep(20)
    print('登陆成功!')
    # 获取cookies
    cookie_items = browser.get_cookies()
    # 定义一个空的字典，存放cookies内容
    post = {}
    # 获取到的cookies是列表形式，将cookies转成json形式并存入本地名为cookie的文本中
    for cookie_item in cookie_items:
        post[cookie_item['name']] = cookie_item['value']
    cookie_str = json.dumps(post)
    # 传回爬虫
    return json.loads(cookie_str)
