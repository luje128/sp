# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    user_id = scrapy.Field()
    user_url = scrapy.Field()
    user_name = scrapy.Field()
    post_content = scrapy.Field()
    post_imgs = scrapy.Field()
    forward = scrapy.Field()
    comment = scrapy.Field()
    likes = scrapy.Field()
    discuss = scrapy.Field()
