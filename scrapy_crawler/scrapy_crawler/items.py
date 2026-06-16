# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ZhihuItem(scrapy.Item):
    url = scrapy.Field()
    question_id = scrapy.Field()
    question_title = scrapy.Field()
    question_content = scrapy.Field()
    question_pubtime = scrapy.Field()
    question_author = scrapy.Field()
    question_answer_num = scrapy.Field()
    question_images = scrapy.Field()
    question_videos = scrapy.Field()
    question_tags = scrapy.Field()
    answer_num = scrapy.Field()
    answers = scrapy.Field()

class ZhihuQuestionItem(scrapy.Item):
    question_id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    pubtime = scrapy.Field()
    answer_num = scrapy.Field()
    tags = scrapy.Field()
    images = scrapy.Field()
    videos = scrapy.Field()
    url = scrapy.Field()

class ZhihuAnswerItem(scrapy.Item):
    question_id = scrapy.Field()
    answer_id = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    pubtime = scrapy.Field()
    images = scrapy.Field()
    videos = scrapy.Field()
    url = scrapy.Field()

