# -*- coding: utf-8 -*-
import base64
import binascii
import copy
import json
import re
import time
from lxml import etree
from .get_cookie import Login

import rsa
import scrapy
from ..items import WeiboItem
from urllib.parse import quote
from scrapy.http.cookies import CookieJar


class WbSpider(scrapy.Spider):
    # 爬虫名
    name = 'wb'
    # 允许访问域
    allowed_domains = ['https://s.weibo.com']
    # 首次请求的解析地址
    start_urls = ['https://s.weibo.com/weibo']
    # 微博搜索目标主页面
    url = 'https://s.weibo.com/weibo?q={}&page={}'
    # 搜索关键字
    keyword = '新冠'
    # 登陆跳转地址
    next_url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
    # 用户
    username = "testcase1@126.com"
    # 密码
    password = "wza7626222"
    # 初始页码
    page = 1

    # 登陆
    login = Login(username=username, password=password)

    # 载入cookies
    cookies = login.login()

    # 搜索关键字
    def parse(self, response):
        des_url = self.url.format(self.keyword, self.page)
        return scrapy.Request(url=des_url, callback=self.parse_next, dont_filter=True, cookies=self.cookies)

    # 解析
    def parse_next(self, response):
        # 获取参数uid
        uid = re.findall('"uid":"(\d+)"', response.text)[0]
        # 遍历元素节点列表
        for res in response.xpath('//div[@class="card-wrap"]/div[@class="card"]'):
            item = WeiboItem()
            post_content = res.xpath(
                'string(div[@class="card-feed"]/div[@class="content"]/p[@node-type="feed_list_content"])').extract_first()
            url = res.xpath(
                'div[@class="card-feed"]/div[@class="content"]/div[@class="info"]/div/a[@class="name"]/@href').extract_first()
            name = res.xpath(
                'div[@class="card-feed"]/div[@class="content"]/div[@class="info"]/div/a[@class="name"]/text()').extract_first()

            post_imgs = res.xpath(
                'div[@class="card-feed"]/div[@class="content"]/div[@node-type="feed_list_media_prev"]//li/img/@src').extract()

            forward = res.xpath('div[@class="card-act"]/ul/li/a[contains(text(),"转发")]/text()').extract_first()
            comment = res.xpath('div[@class="card-act"]/ul/li/a[contains(text(),"评论")]/text()').extract_first()
            likes = res.xpath('div[@class="card-act"]/ul/li/a[@title="赞"]/em/text()').extract_first()
            # 用户id
            item['user_id'] = re.findall('weibo.com/(.*)\?refer_flag', url)[0]
            # 用户url
            item['user_url'] = response.urljoin(url)
            # 用户name
            item['user_name'] = name
            # 内容
            item['post_content'] = ''.join(post_content.split()).replace('\u200b', '').replace('\ue627', '')
            # 图片
            item['post_imgs'] = [response.urljoin(url) for url in post_imgs]
            # 转发
            item['forward'] = forward.strip().split('转发')[1].strip()
            # 评论
            item['comment'] = comment.strip().split('评论')[1].strip()
            # 赞
            item['likes'] = likes

            # 获取参数mid
            mid = res.xpath('../@mid').extract_first()

            # 构建get参数
            params = {
                'act': 'list',
                'mid': mid,
                'uid': uid,
                'smartFlag': 'false',
                'smartCardComment': '',
                'isMain': 'true',
                'suda-data': 'key%3Dtblog_search_weibo%26value%3Dweibo_h_1_p_p',
                'pageid': 'weibo',
                '_t': '0',
                '__rnd': int(time.time() * 1000),
            }

            next_url = 'https://s.weibo.com/Ajax_Comment/small?act={}&mid={}&uid={}&smartFlag={}&smartCardComment={}&isMain={}&suda-data={}&pageid={}&_t={}&__rnd={}'.format(
                params['act'], params['mid'], params['uid'], params['smartFlag'], params['smartCardComment'],
                params['isMain'], params['suda-data'],
                params['pageid'], params['_t'], params['__rnd'])

            headers = {
                'Referer': response.url,
                'X-Requested-With': 'XMLHttpRequest',
            }

            yield scrapy.Request(url=next_url, cookies=self.cookies, callback=self.parse_next_next, dont_filter=True,
                                 meta={'item': copy.deepcopy(item)}, headers=headers)

        url_next = response.xpath('//a[@class="next"]/@href').extract_first()
        if url_next:
            next = response.urljoin(url_next)
            yield scrapy.Request(url=next, cookies=self.cookies, callback=self.parse_next, dont_filter=True)

    def parse_next_next(self, response):
        item = response.meta['item']
        discuss_list = []
        for res in etree.HTML(json.loads(response.text)['data']['html']).xpath(
                '//div[@class="list"]//div[@class="content"]/div[@class="txt"]'):
            discuss = ''.join(res.xpath('string(.)').split())
            discuss_list.append(discuss)
        item['discuss'] = discuss_list
        print(item)
        yield item
