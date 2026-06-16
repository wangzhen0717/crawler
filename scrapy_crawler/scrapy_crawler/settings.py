# Scrapy settings for scrapy_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "scrapy_crawler"

SPIDER_MODULES = ["scrapy_crawler.spiders"]
NEWSPIDER_MODULE = "scrapy_crawler.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "scrapy_crawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False   # 关闭robots.txt

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "scrapy_crawler.middlewares.ScrapyCrawlerSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "scrapy_crawler.middlewares.ScrapyCrawlerDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # "scrapy_crawler.pipelines.ScrapyCrawlerPipeline": 300,
   # "scrapy_crawler.pipelines.JsonlinesPipeline": 100,
   # "scrapy_crawler.pipelines.JsonArrayPipeline": 100,
   "scrapy_crawler.pipelines.MongoPipeline": 200,    # 数字越小，优先级越高，先执行
   # "scrapy_crawler.pipelines.MySQLPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# 日志设置
# 设置日志级别 (从低到高: DEBUG, INFO, WARNING, ERROR, CRITICAL)
# 开发调试时用 DEBUG，线上稳定运行时用 INFO
LOG_LEVEL = "INFO"
# 将日志输出到文件  建议使用绝对路径或者项目下的相对路径
# ****可在run.py添加包含spider名称的日志文件名
# LOG_FILE = "logs/spiders.log"  
# 自定义日志格式
# LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_FORMAT = '\x1b[36m%(asctime)s\x1b[0m \x1b[35m[%(name)s]\x1b[0m \x1b[31m%(levelname)s\x1b[0m: %(message)s'
# 时间格式
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# # 启动FEEDS输出
# FEEDS = {
#     'data/%(name)s_feeds.jl': {   # _%(time)s    UTC+0 时区（即协调世界时）24小时制，北京时间需要+8小时
#         'format': 'jsonlines',    # *必填，格式：json/jsonlines/csv/xml/pickle
#         'encoding': 'utf-8',
#         'overwrite': False,       # False=追加，True=覆盖
#         'store_empty': False,     # 无数据时不生成空文件
#         'indent': 2,      # json格式缩进空格数（0，2，4） 仅对json和xml格式生效
#         # 'fields': ['url', 'title', 'content'],    # 指定字段及顺序
#         # 进阶
#         # 'batch_item_count': 1000,    # 每N条数据写入一次文件, 搭配分片%(batch_id)d/%(batch_time)s使用
#         # 'item_classes': ['myproject.items.MyItem'],  # 只导出指定Item类
#         # 'item_filter'       # 用自定义过滤器决定哪些 Item 写入(用法用时自查)
#         # 'item_export_kwargs': {     # 精细控制导出行为
#         #     'export_empty_fields': True,  # 导出空字段
#         #     'sort_keys': True,            # 按 key 排序
#         # },
#         # 'postprocessing': ['scrapy.extensions.postprocessing.GzipPlugin'],  # 压缩
#         # 'gzip_compresslevel': 5,                 # 压缩级别 1-9，值越大压缩率越高但越慢
#     },
#     # 'data/%(name)s.csv': {    # 扁平数据
#     #     'format': 'csv',
#     #     'encoding': 'utf-8-sig',    # 兼容Excel，csv推荐用utf-8-sig编码，Excel打开不乱码
#     #     'overwrite': True,
#     #     'fields': ['title', 'url', 'content', 'created_time'],  # 固定表头顺序
#     # },
#     # 最终交付
#     # 'data/%(name)s_%(time)s.json': {    # 嵌套数据
#     #     'format': 'json',
#     #     'encoding': 'utf-8',
#     #     'overwrite': True,
#     #     'indent': 2,
#     # }
# }

from dotenv import load_dotenv
import os
import json

# 加载.env文件
load_dotenv()

# 定义配置，从环境变量中取值
# MongoDB连接地址
MONGODB_URI = os.getenv("MONGODB_URI")

# MySQL配置信息
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "db": "zhihu_db",
}

# 知乎登录信息
ZHIHU_LIST_COOKIES = json.loads(os.getenv('ZHIHU_LIST_COOKIES', '{}'))
ZHIHU_DETAIL_COOKIES = json.loads(os.getenv('ZHIHU_DETAIL_COOKIES', '{}'))