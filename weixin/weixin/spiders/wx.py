# -*- coding: utf-8 -*-
import copy
import json
import random
import re
import time
from .get_cookie import weixin
from ..items import WeixinItem
import scrapy


class WxSpider(scrapy.Spider):
    name = 'wx'
    allowed_domains = ['https://mp.weixin.qq.com']
    start_urls = ['https://mp.weixin.qq.com']
    # cookie
    cookies = weixin()
    # 公众号查询关键字
    query = 'UniCareer'
    # 固定参数
    uin = 'OTUyNzM5MDQw'
    # 不同公众号参数可能不一样，而且具有时效性(半小时)
    pass_ticket = 'RKvPM4lCV7vWFPv%252FzXEGsBihdddoK4YB1fBq2LaEvis7F%252FkZbXmknxpmBydS90QJ'
    # 不同公众号参数可能不一样，而且具有时效性(半小时)
    appmsg_token = '1059_AXrl59Czq%2F7Wfouir8ZVER2oQSVFYT6d3f7ORAnUKc-fLFdXu3zjKQSzG5PQCmRUM90hIXwGDPVPn5PB'
    # 不同公众号参数可能不一样，而且具有时效性(半小时)
    key = '79d7d913589a49f07454be3a4466c294bac45d8cf7de18f1531739cf6003f29c0b3a1e733cbefc91aa84021e43e5b317c15bf4a4ad690e614f8d4eee0b8bcfa6e3025d28c57bf22ce63ad142b78b78ce'

    def start_requests(self):
        url = 'https://mp.weixin.qq.com'
        yield scrapy.Request(url=url, dont_filter=True, cookies=self.cookies, callback=self.parse)

    def parse(self, response):
        # 登录之后的微信公众号首页url变化为：https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1849751598，从这里获取token信息
        token = re.findall(r'token=(\d+)', str(response.url))[0]
        # 搜索微信公众号的接口地址
        search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?action={}&token={}&lang={}&f={}&ajax={}&random={}&query={}&begin={}&count={}'
        # 搜索微信公众号接口需要传入的参数，有三个变量：微信公众号token、随机数random、搜索的微信公众号名字
        query_id = {
            'action': 'search_biz',
            'token': str(token),
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': str(random.random()),
            'query': self.query,
            'begin': '0',
            'count': '5',
        }
        # 打开搜索微信公众号接口地址，需要传入相关参数信息如：cookies、params、headers
        yield scrapy.Request(
            url=search_url.format(query_id['action'], query_id['token'], query_id['lang'], query_id['f'],
                                  query_id['ajax'], query_id['random'], query_id['query'], query_id['begin'],
                                  query_id['count']),
            dont_filter=True, cookies=self.cookies, callback=self.parse_parse, meta={'token': token})

    def parse_parse(self, response):
        item = WeixinItem()
        # 取搜索结果中的第一个公众号
        res = json.loads(response.text)['list'][0]
        # 获取这个公众号的fakeid，后面爬取公众号文章需要此字段
        fakeid = res['fakeid']
        # 获取这个公众号的名字
        nickname = res['nickname']
        # 微信公众号文章接口地址
        appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?token={}&lang={}&f={}&ajax={}&random={}&action={}&begin={}&count={}&query={}&fakeid={}&type={}'

        # 初始参数begin=0,经过测试半小时内能循环50次爬完
        num = -5
        while num < 50:
            num += 5
            # 搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
            query_id_data = {
                'token': response.meta['token'],
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': str(random.random()),
                'action': 'list_ex',
                'begin': num,  # 不同页，此参数变化，变化规则为每页加5
                'count': '5',
                'query': '',
                'fakeid': fakeid,
                'type': '9',
            }
            item['nickname'] = nickname
            # 打开搜索的微信公众号文章列表页
            yield scrapy.Request(
                url=appmsg_url.format(query_id_data['token'], query_id_data['lang'], query_id_data['f'],
                                      query_id_data['ajax'], query_id_data['random'],
                                      query_id_data['action'], query_id_data['begin'],
                                      query_id_data['count'], query_id_data['query'],
                                      query_id_data['fakeid'], query_id_data['type']),
                dont_filter=True, cookies=self.cookies, callback=self.parse_next,
                meta={'item': copy.deepcopy(item), 'begin': num})

    def parse_next(self, response):
        item = response.meta['item']
        for res in json.loads(response.text)['app_msg_list']:
            create_time = res['create_time']
            link = res['link']
            digest = res['digest']
            title = res['title']
            update_time = res['update_time']
            # 获得mid,_biz,idx,sn 这几个在link中的信息
            mid = link.split("&")[1].split("=")[1]
            idx = link.split("&")[2].split("=")[1]
            sn = link.split("&")[3].split("=")[1]
            _biz = link.split("&")[0].split("_biz=")[1]
            # fillder 中取得一些不变得信息
            # req_id = "0614ymV0y86FlTVXB02AXd8p"
            # 目标url
            url = "http://mp.weixin.qq.com/mp/getappmsgext?__biz={}&mid={}&sn={}&idx={}&key={}&pass_ticket={}&appmsg_token={}&uin={}&wxtoken={}"
            # 这里的user-agent最好为手机标识
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat QBCore/3.43.901.400 QQBrowser/9.0.2524.400"
            }
            # 添加data，`req_id`、`pass_ticket`分别对应文章的信息，从fiddler复制即可。
            data = {
                "is_only_read": "1",
                "is_temp_url": "0",
                "appmsg_type": "9",
                'reward_uin_count': '0'
            }
            """
               添加请求参数
               __biz对应公众号的信息，唯一
               mid、sn、idx分别对应每篇文章的url的信息，需要从url中进行提取
               key、appmsg_token从fiddler上复制即可
               pass_ticket对应的文章的信息，也可以直接从fiddler复制
               """
            params = {
                "__biz": _biz,
                "mid": mid,
                "sn": sn,
                "idx": idx,
                "key": self.key,
                "pass_ticket": self.pass_ticket,
                "appmsg_token": self.appmsg_token,
                "uin": self.uin,
                "wxtoken": "777",
            }

            item['link'] = link
            item['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time))
            item['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(update_time))
            item['title'] = title
            item['digest'] = digest

            yield scrapy.FormRequest(
                url=url.format(params['__biz'], params['mid'], params['sn'], params['idx'], params['key'],
                               params['pass_ticket'], params['appmsg_token'], params['uin'], params['wxtoken']),
                headers=headers,
                cookies=self.cookies, formdata=data, dont_filter=True,
                callback=self.parse_next_next, meta={'item': copy.deepcopy(item), 'begin': response.meta['begin']})

    def parse_next_next(self, response):
        item = response.meta['item']
        item['read_num'] = json.loads(response.text)['appmsgstat']['read_num']
        item['like_num'] = json.loads(response.text)['appmsgstat']['like_num']
        print('当前begin:%s' % response.meta['begin'], item)
        yield item
