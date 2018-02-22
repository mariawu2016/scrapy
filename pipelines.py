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

#发送邮件
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
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
        #下载文件、封皮、词云并生成邮件发送
        
        #发送邮件
        durls=item['downloadurl'].split('|')
        ds=""
        for i in range(0,3):
            durls[i]=u"<a href='"+durls[i]+u"' style='display:block;'>下载"+str(i+1)+u"</a>"
            ds=ds+durls[i]

        mailto_list = ["pistilwu@qq.com",]
        mail_title = item['bookname']+"("+item['author']+')['+item['bookclass']+']['+item['topclass']+u'][书包网小说]'
        mail_content = u"<table width=600><tr><td width=120>书名</td><td width=480>"+item['bookname']+u"</td></tr><tr><td>简介</td><td>"+item['introduction']+u"</td></tr><tr><td>下载链接</td><td>"+ds+"</td></tr></table>"
        #mail_content="<table><tr><td>简介</td><td>"+item['introduction']+u"</td></tr><tr><td>下载链接</td><td>"+durls.join()+"</td></tr></table>"
        mm = Mailer(mailto_list,mail_title,mail_content)
        res = mm.sendMail()
        print res
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

#邮件发送类
class Mailer(object):
    def __init__(self,maillist,mailtitle,mailcontent):#,mailattpath,mailattname):
        self.mail_list = maillist
        self.mail_title = mailtitle
        self.mail_content = mailcontent

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
        #att = MIMEText(open(mailattpath+mailattname, "rb").read(), "base64", "utf-8")
        #att["Content-Type"] = "application/octet-stream"
        # 附件名称为中文时的写法
        #att.add_header("Content-Disposition", "attachment", filename=("gbk", "", mailattname))
        # 附件名称非中文时的写法
        #att["Content-Disposition"] = 'attachment; filename="test.txt"'
        #print(1)
        #msg.attach(att)

        # jpg类型的附件
        #jpgpart = MIMEApplication(open('/home/mypan/1949777163775279642.jpg', 'rb').read())
        #jpgpart.add_header('Content-Disposition', 'attachment', filename='beauty.jpg')
        #msg.attach(jpgpart)

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
