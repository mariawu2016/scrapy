# -*- coding: UTF-8 -*-
import scrapy
import re
import urllib,urllib2,requests
import os
from bookscrapy.items import BookscrapyItem

class bscrapy7(scrapy.Spider):
    key=u'双性'
    name="bsc7"#爬虫名称
    allowed_domains=["m.bookbao.cc"]#允许的域名
    start_urls=["http://m.bookbao.cc"]
    #start_urls=["http://m.bookbao.cc/TXT/list26_1.html"]
    #start_urls=["http://m.bookbao.cc/TXT/list1_1.html","http://m.bookbao.cc/TXT/list2_1.html","http://m.bookbao.cc/TXT/list26_1.html"]
    
    def parse(self, response):#首页
        topclass_urls=response.xpath("//*[@class='menu']/a")
        #print topclass_urls
        for tcu in topclass_urls:
            topclass_url=self.start_urls[0]+tcu.xpath("./@href").extract_first()
            #print topclass_url
            yield scrapy.Request(topclass_url,callback=self.parse_topclass)

    def parse_topclass(self,response):#进入顶层分类
        page_urls=response.xpath("//*[@class='pdlist']/ul/h2/a[1]")
        for pu in page_urls:
            page_url=self.start_urls[0]+pu.xpath("./@href").extract_first()
            yield scrapy.Request(page_url,callback=self.parse_page_url)
    
    def parse_page_url(self,response):#二层分类分页
        base_url=str(response.xpath("//*[@class='listcd']/a[last()]/@href").extract_first())
        base_url=re.findall(r'\d+',base_url)
        page_nums=response.xpath("//*[@class='man_first']/dl/code/a[last()]/text()").extract_first()
        for n in range(1,int(page_nums)):
            page_url = "http://m.bookbao.cc/TXT/list"+base_url[0]+"_"+str(n)+".html"
            yield scrapy.Request(page_url,callback=self.parse_book_list)

    def parse_book_list(self, response):#书名列表页
        #pages=response.xpath("//*[@class='man_first']/ul/li")
        #取红色热门小说
        #pages=response.xpath("//*[@class='man_first']/ul/li[contains(h1/a/@color,'#FF0000')]")
        pages=response.xpath(u"//*[@class='man_first']/ul/li[contains(p/text(),$val)]",val=self.key)
        #pages=response.xpath(u"//*[@class='man_first']/ul/li[contains(p/text(),'ABO')]")
        #print pages
        if len(pages)!=0:
            for page in pages:
                item=BookscrapyItem()#注意item的生成时机，不可过早，否则数据返回后会层层覆盖。
                item['topclass']=response.xpath("normalize-space(//*[@class='listcd']/a[last()-1]/text())").extract_first()
                item['bookclass']=response.xpath("normalize-space(//*[@class='listcd']/a[last()]/text())").extract_first()
                #item['bookname']=page.xpath("normalize-space(./h1/a/@title)").extract_first()
                #item['author']=page.xpath("normalize-space(./h3/text())").extract_first()
                item['downid']=re.sub(r'\D',"",page.xpath("./h1/a/@href").extract_first())
                #item['datasize']=page.xpath("normalize-space(./h4/text())").extract_first()
                book_url=self.start_urls[0]+page.xpath("./h1/a/@href").extract_first()
                #print book_url
                #print("%s,%s,%s,%s|%s\n\r"%(item['bookname'],item['author'],item['downid'],item['topclass'],item['bookclass']))
                yield scrapy.Request(book_url,callback=self.parse_book_info,meta={'item':item})

    def parse_book_info(self, response):#书详情页面
        item = response.meta['item']
        item['bookname']=response.xpath("//*[@class='mlist']/h1/text()").extract_first()
        item['author']=response.xpath("//*[@class='mlist']/ul/li[1]").xpath('normalize-space(string(.))').extract_first()
        item['datasize']=response.xpath("//*[@class='mlist']/ul/li[3]").xpath('normalize-space(string(.))').extract_first()
        item['introduction']=response.xpath("//*[@class='conten']/p").xpath('string(.)').extract_first()
        item['remarks']=response.xpath("//*[@class='mlist']/h3/text()").extract_first()
        durls=response.xpath("//*[@class='qd']/a[@class='right']/@href")
        for u in durls:
            url=u.extract()
            resp = requests.get(url)
            if not os.path.exists('./'+self.key):
                os.mkdir('./'+self.key)
            dn=u'./'+self.key+'/'+item['bookname']+u'('+item['author']+u').txt'
            with open(dn, "wb") as code:
                code.write(resp.content)
            item['downloadurl']=url
            
        yield item

