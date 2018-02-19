# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BookscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    bookname = scrapy.Field()
    author = scrapy.Field()
    introduction = scrapy.Field()
    datasize=scrapy.Field()
    downid=scrapy.Field()
    bookclass=scrapy.Field()
    topclass=scrapy.Field()
    remarks=scrapy.Field()
    downloadurl=scrapy.Field()