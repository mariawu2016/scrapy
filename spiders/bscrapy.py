# -*- coding: UTF-8 -*-
import scrapy
import re
from bookscrapy.items import BookscrapyItem

class bscrapy(scrapy.Spider):
    name="bsc"#爬虫名称
    allowed_domains=["m.bookbao.cc"]#允许的域名
    start_urls=["http://m.bookbao.cc/book/recommend.asp?cid=26&Page=1"]
    def parse(self, response):
        #num_pages = response.xpath("//*[@class='tj']/li[last]/a").extract_first())
        num_pages=27
        base_url = "http://m.bookbao.cc/book/recommend.asp?cid=26&Page={0}"
        for page in range(1, num_pages):
            yield scrapy.Request(base_url.format(page), dont_filter=True, callback=self.parse_page)

    def parse_page(self, response):
        book_urls=response.xpath("//*[@class='tj']/li")
        nums=len(book_urls)-1#把li末尾的页码li删除
        for n in range(0,nums-1):
            book_detail_url = "http://m.bookbao.cc"+str(book_urls[n].xpath("./a/@href").extract_first())
            #item = BookscrapyItem()
            #item['downid']=re.sub("\D","",book_detail_url)
            #yield scrapy.Request(book_detail_url,callback=self.parse_book_info,meta={'item':item})
            yield scrapy.Request(book_detail_url,callback=self.parse_book_info)

    def parse_book_info(self, response):
        #item = response.meta['item']
        item = BookscrapyItem()
        item['bookname']=response.xpath("//*[@class='mlist']/h1/text()").extract_first()
        item['author']=response.xpath("//*[@class='mlist']/ul/li[1]/text()").extract_first()
        item['introduction']=response.xpath("//*[@class='conten']/p").xpath('string(.)').extract_first()
        item['remarks']=response.xpath("//*[@class='conten']/p/span[1]/text()").extract_first()
        item['datasize']=response.xpath("//*[@class='mlist']/ul/li[3]/text()").extract_first()
        item['bookclass']=response.xpath("normalize-space(//*[@class='mlist']/ul/li[2]/text())").extract_first()
        item['downid']=re.sub(r"\D","",str(response.xpath("//*[@class='mlist']/a[1]/@href").extract_first()))
        #print item['bookname']+"\n\r"+item['author']+"\n\r"+item['introduction']+"\n\r"
        yield item

