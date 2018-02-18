# -*- coding: UTF-8 -*-
import scrapy
import re
from bookscrapy.items import BookscrapyItem

class bscrapy2(scrapy.Spider):
    name="bsc2"#爬虫名称
    allowed_domains=["m.bookbao.cc"]#允许的域名
    #start_urls=["http://m.bookbao.cc/TXT/list26_1.html"]
    start_urls=["http://m.bookbao.cc/TXT/list1_1.html","http://m.bookbao.cc/TXT/list2_1.html","http://m.bookbao.cc/TXT/list26_1.html"]
    
    def parse(self, response):
        page_list_urls=response.xpath("//*[@class='pdlist']/ul")
        #print page_list_urls
        # page_list_url = "http://m.bookbao.cc"+page_list_urls[0].xpath('./h2/a/@href').extract_first()
        # yield scrapy.Request(page_list_url,callback=self.parse_page_list)
        for n in page_list_urls:
            page_list_url = "http://m.bookbao.cc"+n.xpath('./h2/a/@href').extract_first()
            yield scrapy.Request(page_list_url,callback=self.parse_page_list)

    def parse_page_list(self, response):
        base_url=str(response.xpath("//*[@class='listcd']/a[last()]/@href").extract_first())
        #print base_url
        base_url=re.findall(r'\d+',base_url)
        #print base_url[0]
        #page_nums=response.xpath("//*[@class='man_first']/dl/code/a[last()]/text()").extract_first()
        #print page_nums
        # page_url = "http://m.bookbao.cc/TXT/list"+base_url[0]+"_1.html"
        # yield scrapy.Request(page_url,callback=self.parse_book_list)
        for i in range(1,int(page_nums)):
            page_url = "http://m.bookbao.cc/TXT/list"+base_url[0]+"_"+str(i)+".html"
            yield scrapy.Request(page_url,callback=self.parse_book_list)

    def parse_book_list(self, response):
        pages=response.xpath("//*[@class='man_first']/ul/li")
        #print pages
        # item = BookscrapyItem()
        # item['topclass']=response.xpath("//*[@class='listcd']/a[last()-1]/text()").extract_first()
        # item['author']=pages[0].xpath("./h3/text()").extract_first()
        # book_url="http://m.bookbao.cc"+str(pages[0].xpath("./h1/a/@href").extract_first())
        # yield scrapy.Request(book_url,callback=self.parse_book_info,meta={'item':item})
        for page in pages:
            item = BookscrapyItem()
            item['topclass']=response.xpath("//*[@class='listcd']/a[last()-1]/text()").extract_first()
            item['author']=page.xpath("./h3/text()").extract_first()
            book_url="http://m.bookbao.cc"+str(page.xpath("./h1/a/@href").extract_first())
            yield scrapy.Request(book_url,callback=self.parse_book_info,meta={'item':item})

    def parse_book_info(self, response):
        item = response.meta['item']
        item = BookscrapyItem()
        item['bookname']=response.xpath("//*[@class='mlist']/h1/text()").extract_first()
        #item['author']=response.xpath("//*[@class='mlist']/ul/li[1]/text()").extract_first()#作者名称有些导不出
        item['introduction']=response.xpath("//*[@class='conten']/p").xpath('string(.)').extract_first()
        item['remarks']=response.xpath("//*[@class='conten']/p/span[1]/text()").extract_first()
        item['datasize']=response.xpath("//*[@class='mlist']/ul/li[3]/text()").extract_first()
        item['bookclass']=response.xpath("normalize-space(//*[@class='mlist']/ul/li[2]/text())").extract_first()
        item['downid']=re.sub(r"\D","",str(response.xpath("//*[@class='mlist']/a[1]/@href").extract_first()))
        print item['bookname']+"\n\r"+item['author']+"\n\r"+item['introduction']+"\n\r"
        yield item

