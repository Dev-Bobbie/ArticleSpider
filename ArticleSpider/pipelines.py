# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

import pymongo

from scrapy import Item
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlPipeline(object):
    #采用同步的机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('192.168.33.11', 'root', 'mysql', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
                   insert into jobbole_article(title, create_date,url, url_object_id,front_image_url,front_image_path,praise_nums,comment_nums,fav_nums,tags,content)
                   VALUES (%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(fav_nums)
               """
        params = (self["title"], self["create_date"], self["url"], self["url_object_id"], self["front_image_url"],
                  self["front_image_path"], self["praise_nums"], self["comment_nums"], self["fav_nums"], self["tags"],
                  self["content"])
        try:
            self.cursor.execute(insert_sql, params)
            # 记录成功插入的数据总量
            spider.crawler.stats.inc_value('Success_InsertedInto_MySqlDB')
            self.conn.commit()
        except Exception as e:
            logging.error("Failed Insert Into, Reason: {}".format(e.args))
            # 记录插入失败的数据总量
            spider.crawler.stats.inc_value('Failed_InsertInto_DB')
            self.conn.rollback()

class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item,spider)
        query.addErrback(self.handle_error, item, spider) #处理异常

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        spider.crawler.stats.inc_value('Failed_InsertInto_DB')
        _ = failure
        print (_)

    def do_insert(self, cursor, item,spider):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)
        # self.db.commit()   adbapi会自动提交数据的插入事实
        # 记录成功插入数据库的数据总量
        try:
            spider.crawler.stats.inc_value('Success_InsertedInto_MySqlDB')
        except Exception as e:
            _ = e


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path

        return item