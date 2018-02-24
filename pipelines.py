# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import json
from twisted.enterprise import adbapi
from scrapy import log
import MySQLdb
import MySQLdb.cursors
import datetime
from openpyxl import Workbook
from openpyxl import load_workbook

#发送邮件
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

#下载文件
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
#有编码问题
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

#无编码问题
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
        #self.wb.save('./'+self.wbname)
        return item
        
    def close_spider(self,spider):
        self.wb.save('./'+self.wbname)

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

#图片下载类
class DownloadImagesPipeline(ImagesPipeline):
    # def file_path(self, request, response=None, info=None):  
    #     image_guid = request.url.split('/')[-1]  
    #     return u'full/%s' % (image_guid)
    
    def get_media_requests(self, item, info):
        #yield scrapy.Request("http://m.bookbao.cc"+item['bookface'])
        yield scrapy.Request("http://m.bookbao.cc%s"%(item['bookface']))

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no files")
        item['imagepath'] = image_paths
        # if item['bookname']:
        #     newname=item['bookname']+'bookface.jpg'
        #     os.rename("/images/"+image_paths[0], "/results/full/" + newname)
        #     item['imagepath']="/results/full/" + newname
        return item

#文件下载类
class DownloadFilesPipeline(FilesPipeline):
    # def file_path(self, request, response=None, info=None):  
    #     file_guid = request.url.split('/')[-1]
    #     #file_guid=file_guid.encode("gb2312") 
    #     #file_guid=item['bookname']+"("+item['author']+")"
    #     return 'full/%s' % (file_guid)

    def get_media_requests(self, item, info):
        for file_url in item['downloadurl'].split("|"):
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['filepath'] = file_paths
        # if item['bookname']:
        #     newname=item['bookname']+'('+item['author']+').txt'
        #     os.rename("/results/"+file_paths[0], "/results/full/" + newname)
        #     item['filepath']="/results/full/" + newname 

        #发送邮件
        durls=item['downloadurl'].split('|')
        ds=""
        for i in range(0,3):
            durls[i]=u"<a href='"+durls[i]+u"' style='display:block;'>下载"+str(i+1)+u"</a>"
            ds=ds+durls[i]

        mailto_list = ["pistilwu@qq.com",]
        mail_title = item['bookname']+"("+item['author']+')['+item['bookclass']+']['+item['topclass']+u'][书包网小说]'
        mail_content = u"<table width=700><tr><td width=150>书名|作者</td><td width=550>"+item['bookname']+"|"+item['author']+u"</td></tr>"+\
                       u"<tr><td>分类</td><td>"+item['topclass']+"|"+item['bookclass']+"</td></tr>"+\
                       u"<tr><td>简介</td><td>"+item['introduction']+u"</td></tr>"+\
                       u"<tr><td>下载链接</td><td>"+ds+"</td></tr></table>"
        #mail_content="<table><tr><td>简介</td><td>"+item['introduction']+u"</td></tr><tr><td>下载链接</td><td>"+durls.join()+"</td></tr></table>"
        mail_filepath=item['filepath']
        mail_imagepath=item['imagepath']
        bookname=item['bookname']
        mm = Mailer(mailto_list,mail_title,mail_content,mail_filepath,bookname,mail_imagepath)
        res = mm.sendMail()
        print("Mailer："+res)
        return item
#邮件发送类
class Mailer(object):
    def __init__(self,maillist,mailtitle,mailcontent,filepath,filename,imagepath):
        self.mail_list = maillist
        self.mail_title = mailtitle
        self.mail_content = mailcontent
        self.mail_imagepath=imagepath
        self.mail_filepath=filepath
        self.file_name=filename

        self.mail_host = "smtp.qq.com"
        self.mail_user = "pistilwu"
        self.mail_pass = "pebvsnwogxlrcacj"
        self.mail_postfix = "qq.com"

    def sendMail(self):
        me = self.mail_user + "<" + self.mail_user + "@" + self.mail_postfix + ">"
        msg = MIMEMultipart()
        msg['Subject'] =self.mail_title
        msg['From'] = me
        msg['To'] = ";".join(self.mail_list)

        puretext = MIMEText('<div>'+self.mail_content+'</div>','html','utf-8')
        #puretext = MIMEText('纯文本内容'+self.mail_content)
        msg.attach(puretext)

        # 构造附件
        project_dir=os.path.abspath(os.path.dirname(__file__))
        fpath=os.path.join(project_dir,'results')
        #fname=self.mail_filepath[0].split('/')[-1]
        fname=self.file_name+".txt"
        att = MIMEText(open(os.path.join(fpath,self.mail_filepath[0]), "rb").read(), "base64", "utf-8")
        att["Content-Type"] = "application/octet-stream"
        # 附件名称为中文时的写法
        att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", base64.b64encode(fname.encode('UTF-8'))))
        #att.add_header('Content-Disposition', 'attachment', fname=fname.encode('gb2312'))
        # 附件名称非中文时的写法
        #att["Content-Disposition"] = 'attachment; filename='+os.path.join(fpath,self.mail_filepath[0])
        #print(1)
        msg.attach(att)

        #jpg类型的附件
        ppath=os.path.join(project_dir,'images')
        pname=self.mail_imagepath[0].split('/')[-1]
        jpgpart = MIMEApplication(open(os.path.join(ppath,self.mail_imagepath[0]), 'rb').read())
        jpgpart.add_header('Content-Disposition', 'attachment', filename=pname)
        msg.attach(jpgpart)

        # 首先是xlsx类型的附件
        #xlsxpart = MIMEApplication(open('test.xlsx', 'rb').read())
        #xlsxpart.add_header('Content-Disposition', 'attachment', filename='test.xlsx')
        #msg.attach(xlsxpart)

        # mp3类型的附件
        #mp3part = MIMEApplication(open('kenny.mp3', 'rb').read())
        #mp3part.add_header('Content-Disposition', 'attachment', filename='benny.mp3')
        #msg.attach(mp3part)

        # pdf类型附件
        #part = MIMEApplication(open('foo.pdf', 'rb').read())
        #part.add_header('Content-Disposition', 'attachment', filename="foo.pdf")
        #msg.attach(part)

        try:
            s = smtplib.SMTP() #创建邮件服务器对象
            s.connect(self.mail_host) #连接到指定的smtp服务器。参数分别表示smpt主机和端口
            s.login(self.mail_user+"@"+self.mail_postfix, self.mail_pass) #登录到你邮箱
            s.sendmail(me, self.mail_list, msg.as_string()) #发送内容
            s.close()
            return True
        except Exception, e:
            print str(e)
            return False


