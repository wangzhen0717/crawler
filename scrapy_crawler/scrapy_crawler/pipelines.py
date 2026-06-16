# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from sqlite3.dbapi2 import paramstyle

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from jupyter_client import adapter
from scrapy.exceptions import DropItem
from .settings import MONGODB_URI, MYSQL_CONFIG

import pymongo
import pymysql
import json

from .items import ZhihuItem, ZhihuQuestionItem, ZhihuAnswerItem


class ScrapyCrawlerPipeline:
    def process_item(self, item, spider):
        return item


class JsonlinesPipeline:
    """保存数据逐行到JSON文件(.jl)"""

    def open_spider(self, spider):
        # 存在空文件夹现象(存入数据异常，但文件夹已创建)
        self.file = open(f'data/{spider.name}_pipe.jl', 'a', encoding='utf-8')
        spider.logger.info(f"初始化，打开{self.file.name}")

    def process_item(self, item):
        if isinstance(item, ZhihuItem):
            line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False) + '\n'
            self.file.write(line)

    def close_spider(self, spider):
        self.file.close()
        spider.logger.info(f"爬虫结束，关闭{self.file.name}")

class JsonArrayPipeline:
    """保存数据到标准JSON文件(.json)"""
    def open_spider(self, spider):
        self.items = []

    def process_item(self, item, spider):
        if isinstance(item, ZhihuItem):
            self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        if self.items:
            with open(f'data/{spider.name}_pipe.json', 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=4)
            spider.logger.info(f"爬虫结束，保存{spider.name}.json")
        else:
            spider.logger.info(f"无数据存入，不生成文件")

class MongoPipeline:
    """
    保存数据到MongoDB
    - 根据spider.name 自动创建使用数据库
    - 集合名统一为 'items'
    """
    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri
        self.client = None       # MongoDB 客户端连接（服务层）
        self.db = None           # 数据库（Database）
        self.collection = None   # 集合（Collection，相当于 MySQL 的表）

    @classmethod
    def from_crawler(cls, crawler):
        """从settings.py中读取配置"""
        return cls(
            mongo_uri=crawler.settings.get("MONGODB_URI", "mongodb://localhost:27017")
        )

    def open_spider(self, spider):
        """
        爬虫启动时，建立连接，动态创建数据库
        """
        self.client = pymongo.MongoClient(self.mongo_uri)
        db_name = f"{spider.name}_db"
        self.db = self.client[db_name]
        self.collection = self.db["items"]

        spider.logger.info(f"MongoDB 连接成功: {db_name}.items")

    def close_spider(self, spider):
        """
        爬虫结束，关闭连接
        """
        if self.client:
            self.client.close()
            spider.logger.info(f"MongoDB连接已关闭")

    def process_item(self, item, spider):
        """
        处理item并保存到数据库
        """
        if isinstance(item, ZhihuItem):  # 确保ZhihuItem获取到的数据存入MongoDB
            spider.logger.info(f"进入 Pipeline，收到 item: {item.get('question_id')}")
            try:
                # 将item转为字典
                adapter = ItemAdapter(item)
                data = adapter.asdict()
                # 保存数据
                # 直接存入
                # self.collection.insert_one(data)
                # 去重存入，使用(update_one+upsert)question_id作为唯一键
                self.collection.update_one(
                    {'question_id': data.get('question_id')},    # 查询条件
                    {'$set': data},      # 更新数据，---已存在的问题的回答会被新获取到更新的回答覆盖
                    upsert=True          # 不存在则插入
                )
                spider.logger.info(f"保存数据成功: question_id={data.get('question_id')}")
            except Exception as e:
                spider.logger.error(f"MongonDB保存数据失败: {e}")

        return item

class MySQLPipeline:
    """分表存储数据到MySQL"""
    def __init__(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.conn = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        """从 setting.py 读取配置"""
        mysql_config = crawler.settings.get("MYSQL_CONFIG")
        return cls(
            host=mysql_config.get("host", "localhost"),
            port=mysql_config.get("port", 3306),
            user=mysql_config.get("user", "root"),
            password=mysql_config.get("password"),
            db=mysql_config.get("db", "zhihu_db"),
        )

    def open_spider(self, spider):
        """爬虫启动时，建立数据库连接"""
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            charset='utf8mb4',  # 支持中文和 emoji，防止乱码
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()
        spider.logger.info(f"MySQL连接成功：{self.db}")

    def close_spider(self, spider):
        """爬虫关闭时，关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        spider.logger.info("MySQL连接已关闭")

    def process_item(self, item, spider):
        """
        处理item并保存到数据库
        """
        # 确保ZhihuQuestionItem和ZhihuAnswerItem获取到的数据存入MySQL
        if isinstance(item, ZhihuQuestionItem):
            return self._insert_question(item, spider)
        elif isinstance(item, ZhihuAnswerItem):
            return self._insert_answer(item, spider)
        else:
            return item

    def _execute(self, sql, params, msg, spider):
        """sql存储通用执行逻辑"""
        try:
            _clean_params = self._clean_params(params)
            self.cursor.execute(sql, _clean_params)
            self.conn.commit()  # 提交事务
            spider.logger.info(f"{msg}成功")
        except Exception as e:
            spider.logger.error(f"{msg}失败：{e}")
            self.conn.rollback()  # 发生异常时回滚事务，避免部分写入导致数据不一致

    def _clean_params(self, params):
        """
        清洗存入MySQL数据
        1. 将 Python 列表/字典(包括空和有值)转换为 JSON 字符串（MySQL JSON 字段要求）
        2. 将空字符串 '' 转换为 None（避免存入大量空值）
        3. 其他类型（int、str、None）保持不变
        """
        cleaned_params = []
        for i in params:
            if i is None:
                cleaned_params.append(None)
            elif isinstance(i, str) and i == '':
                cleaned_params.append(None)
            elif isinstance(i, (list, dict)):
                cleaned_params.append(json.dumps(i, ensure_ascii=False))
            else:
                cleaned_params.append(i)

        return tuple(cleaned_params)

    def _insert_question(self, item, spider):
        adapter = ItemAdapter(item)
        sql = """
            INSERT INTO questions (question_id, title, content, author, pubtime, answer_num, tags, images, videos, url) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
                title = VALUES(title),
                content = VALUES(content),
                answer_num = VALUES(answer_num),
                images = VALUES(images),
                videos = VALUES(videos)
        """
        # 问题表 params
        params = (
            adapter.get('question_id'),
            adapter.get('title'),
            adapter.get('content'),
            adapter.get('author'),
            adapter.get('pubtime'),
            adapter.get('answer_num'),
            adapter.get('tags'),
            adapter.get('images'),
            adapter.get('videos'),
            adapter.get('url')
        )
        self._execute(sql, params, "问题数据存储", spider)
        return item

    def _insert_answer(self, item, spider):
        adapter = ItemAdapter(item)
        sql = """
            INSERT INTO answers (question_id, answer_id, author, content, pubtime, images, videos, url) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
                content = VALUES(content),
                images = VALUES(images),
                videos = VALUES(videos)
        """
        params = (
            adapter.get('question_id'),
            adapter.get('answer_id'),
            adapter.get('author'),
            adapter.get('content'),
            adapter.get('pubtime'),
            adapter.get('images'),
            adapter.get('videos'),
            adapter.get('url')
        )
        self._execute(sql, params, "回答数据存储", spider)
        return item







