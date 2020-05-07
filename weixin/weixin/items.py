# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeixinItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    nickname = scrapy.Field()
    title = scrapy.Field()
    digest = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    read_num = scrapy.Field()
    like_num = scrapy.Field()
