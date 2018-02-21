# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from twisted.enterprise import adbapi
from scrapy import log
import MySQLdb
import MySQLdb.cursors
import datetime
from openpyxl import Workbook
from openpyxl import load_workbook

class BookscrapyPipeline(object):
    def __init__(self):
        now_time = datetime.datetime.now()
        dt=datetime.datetime.strftime(now_time,'%Y-%m-%d %H：%M：%S ')
        self.file = open("./"+dt+"books.json", "wb")

    def process_item(self, item, spider):
        # 编码的转换
        #num=len(item)
        #for k in range(0,num):
            #item[k] = item[k].encode("GB18030")
            #item[k] = item[k].encode("utf8")
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

class BookscrapyPipelineToExcel(object):
    def __init__(self):
        now_time = datetime.datetime.now()
        dt=datetime.datetime.strftime(now_time,'(%Y-%m-%d %H:%M:%S) ')
        self.wbname=dt+'books.xlsx'
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(['下载id', '书名', '作者', '大小', '简介', '大类', '子分类', '备注','下载','封皮'])
        
    def process_item(self, item, spider):
        line = [item['downid'],item['bookname'],item['author'],item['datasize'],item['introduction'],item['topclass'],item['bookclass'],item['remarks'],item['downloadurl'],item['bookface']]
        self.ws.append(line)
        self.wb.save('./'+self.wbname)
        return item
        
    def close_spider(self,spider):
        pass
        #self.wb.save('./'+self.wbname)

class MySQLPipeline(object):

    def __init__(self):
        self.dbpool = adbapi.ConnectionPool("MySQLdb",
                                            host = '127.0.0.1',
                                            port=3306,
                                            db = "bookbao",            # 数据库名
                                            user = "root",       # 数据库用户名 
                                            passwd = "root",     # 密码
                                            cursorclass = MySQLdb.cursors.DictCursor, 
                                            charset = "utf8",
                                            #use_unicode = False 
                                           )
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self._conditional_insert, item)
        query.addErrback(self.handle_error)
        return item

    def _conditional_insert(self, tb, item):            
        # num=len(item)
        # for k in range(0,num):
        #     item[k] = item[k].encode("utf8")
        # tb.execute("insert into books (downid, bookname,author,datasize,introduction,topclass,bookclass,remarks),\
        #             values (%s, %s, %s, %s, %s, %s, %s, %s),\
        #             "(item["downid"],item["bookname"], item["author"], item["datasize"], item["introduction"], item["topclass"],\
        #            item["bookclass"], item["remarks"]))
        sql="insert into books (downid,bookname,author,datasize,introduction,topclass,bookclass,remarks) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        tb.execute(sql,(item['downid'],item['bookname'],item['author'],item['datasize'],item['introduction'],item['topclass'],item['bookclass'],item['remarks']))
        log.msg("Item data in db: %s" % item, level=log.DEBUG)

    def handle_error(self, e):
        log.err(e)
