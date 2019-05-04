# -*- coding: utf-8 -*-
import re
import time

import scrapy
import datetime
from scrapy.http import Request
from urllib import parse
from scrapy.loader import ItemLoader
from scrapy.mail import MailSender

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class JobboleSpider(scrapy.Spider):
    start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    #收集伯乐在线所有404的url以及404页面数
    handle_httpstatus_list = [404]

    def __init__(self, **kwargs):
        super(JobboleSpider, self).__init__(**kwargs)
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_closed, signals.spider_closed)

    def handle_spider_closed(self, spider, reason):
        self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2. 获取下一页的url并交给scrapy进行下载， 下载完成后交给parse
        """
        #解析列表页中的所有文章url并交给scrapy下载后并进行解析
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url":image_url}, callback=self.parse_detail)

        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        article_item = JobBoleArticleItem()

        #通过item loader加载item
        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()


        yield article_item


    def close(self, reason):
        """
        爬虫邮件报告状态
        """
        # 结束时间
        fnished = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # 创建邮件发送对象
        mail = MailSender.from_settings(self.settings)
        # 邮件内容
        spider_name = self.settings.get('BOT_NAME')
        start_time = self.start
        artice_success_request = self.crawler.stats.get_value("ArticleDetail_Success_Reqeust")
        personpage_success_request = self.crawler.stats.get_value("PersonPage_Success_Reqeust")
        failed_request = self.crawler.stats.get_value("Failed_Reqeust")
        # 若请求成功, 则默认为0
        if failed_request == None:
            failed_request = 0
        insert_into_success = self.crawler.stats.get_value("Success_InsertedInto_MySqlDB")
        failed_db = self.crawler.stats.get_value("Failed_InsertInto_DB")
        # 若插入成功, 则默认为0
        if failed_db == None:
            failed_db = 0
        fnished_time = fnished
        body = "爬虫名称: {}\n\n 开始时间: {}\n\n 文章请求成功总量：{}\n 个人信息获取总量：{}\n 请求失败总量：{} \n\n 数据库存储总量：{}\n 数据库存储失败总量：{}\n\n 结束时间  : {}\n".format(
            spider_name,
            start_time,
            artice_success_request,
            personpage_success_request,
            failed_request,
            insert_into_success,
            failed_db,
            fnished_time)
        try:
            # 发送邮件
            mail.send(to=self.settings.get('RECEIVE_LIST'), subject=self.settings.get('SUBJECT'), body=body)
        except Exception as e:
            self.logger.error("Send Email Existing")