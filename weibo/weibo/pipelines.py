# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import csv


class WeiboPipeline(object):
    def __init__(self):
        # 打开文件，指定方式为写，利用newline=''参数把csv写数据时产生的空行消除
        self.file = open('weibo.csv', 'w', newline='', encoding='gb18030')
        # 设置文件第一行的字段名，注意要跟spider传过来的字典item的key名称相同
        self.fieldnames = ['user_id', 'user_url', 'user_name', 'post_content', 'post_imgs', 'forward', 'comment', 'likes', 'discuss']
        # 指定文件的写入方式为csv字典写入，参数1为指定具体文件，参数2为指定字段名
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        # 写入第一行字段名，因为只要写入一次，所以文件放在__init__里面
        self.writer.writeheader()

    def process_item(self, item, spider):
        # 写入spider传过来的具体数值
        self.writer.writerow(item)
        return item

    def __del__(self):
        self.file.close()
