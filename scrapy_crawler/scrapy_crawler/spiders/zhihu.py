import scrapy
import json

from fake_useragent import UserAgent
from ..items import ZhihuItem, ZhihuQuestionItem, ZhihuAnswerItem
from ..utils import jsonpath_extract, timestamp_to_str, parse_zhihu_detail
from ..settings import ZHIHU_LIST_COOKIES, ZHIHU_DETAIL_COOKIES


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ["https://www.zhihu.com/hot"]

    headers = {
        "User-Agent": UserAgent().random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd", # 可加，支持的压缩算法（编码格式），指纹请求会自动添加
        "Accept-Language": "zh-CN,zh;q=0.9",
        # "Cache-Control": "max-age=0",   # 对爬虫影响很小可以忽略
        # "Priority": "u=0,i",  # 请求优先级，不用加没意义 
        "Sec-Ch-Ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',   # 可加，浏览器品牌和版本，指纹请求会自动添加
        "Sec-Ch-Ua-Mobile": "?0",   # 可加，是否为移动设备，指纹请求会自动添加
        "Sec-Ch-Ua-Platform": '"Windows"',   # 可加，操作系统平台，指纹请求会自动添加
        # "Sec-Fetch-Dest": "document",   # 请求的目标资源类型，手动指定极易出错，反而暴露特征
        # "Sec-Fetch-Mode": "cors",   # 同上 由浏览器自动管理，爬虫不应伪造
        # "Sec-Fetch-Site": "same-origin",   # 同上
        # "Sec-Fetch-User": "?1",   # 同上
        "Upgrade-Insecure-Requests": "1"    # 可加，要求服务器http->https
    }

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], headers=self.headers, cookies=ZHIHU_LIST_COOKIES, callback=self.parse)

    def parse(self, response):
        self.logger.info(f"列表页请求状态码: {response.status}")
        json_data = response.css("#js-initialData::text").get()
        data = json.loads(json_data)
        items = jsonpath_extract(data, "$..hotList")[0]
        for item in items:
            # title = item["target"]["titleArea"].get("text", "")
            detail_url = item["target"]["link"].get("url", "")
            # detail_headers = self.headers.copy()
            # detail_headers.update({"Referer": ""})
            if "question/" not in detail_url:  # 存在其他主题页面
                continue
            yield scrapy.Request(url=detail_url, callback=self.parse_detail, headers=self.headers, cookies=ZHIHU_DETAIL_COOKIES)

    def parse_detail(self, response):
        answer_dict = {}
        self.logger.info(f"请求详情页{response.url}")
        json_data = response.css("#js-initialData::text").get()
        data = json.loads(json_data)
        # 问题部分
        question_item = jsonpath_extract(data, "$..entities.questions")
        question_id = next(iter(question_item[0].keys()), None)   # 获取dict的key
        url = f"https://www.zhihu.com/question/{question_id}"
        question_data = next(iter(question_item[0].values()))
        question_title = question_data["title"]
        question_pubtime = timestamp_to_str(question_data["created"])
        question_author = question_data["author"]["name"]
        question_answer_num = question_data["answerCount"]
        question_tags = jsonpath_extract(question_data, "$..topics..name")
        question_detail = question_data["detail"]
        question_content = parse_zhihu_detail(question_detail).get("content")
        question_images = parse_zhihu_detail(question_detail).get("images")
        question_videos = parse_zhihu_detail(question_detail).get("videos")

        questionItem = ZhihuQuestionItem()
        questionItem["url"] = url
        questionItem["question_id"] = question_id
        questionItem["title"] = question_title
        questionItem["content"] = question_content
        questionItem["author"] = question_author
        questionItem["pubtime"] = question_pubtime
        questionItem["answer_num"] = question_answer_num
        questionItem["tags"] = question_tags
        questionItem['images'] = question_images
        questionItem['videos'] = question_videos
        yield questionItem    # mysql 添加外键(question_id)约束的话，必须要先存在这个外键，需要先把question存入

        # 回答部分  （答案id，作者，回答时间，回答文本，图片，视频）
        answers = []
        answer_item = jsonpath_extract(data, "$..entities.answers")
        for answer_id, answer in answer_item[0].items():
            answer_dict = {
                "answer_id": answer_id,
                "answer_author": answer["author"]["name"],
                "answer_pubtime": timestamp_to_str(answer["createdTime"]),
                "answer_content": parse_zhihu_detail(answer["content"]).get("content"),
                "answer_images": parse_zhihu_detail(answer["content"]).get("images"),
                "answer_videos": parse_zhihu_detail(answer["content"]).get("videos"),
                "answer_url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
            }
            answers.append(answer_dict)

            answerItem = ZhihuAnswerItem()
            answerItem["url"] = answer_dict.get("answer_url")
            answerItem["question_id"] = question_id
            answerItem["answer_id"] = answer_dict.get("answer_id")
            answerItem["author"] = answer_dict.get("answer_author")
            answerItem["content"] = answer_dict.get("answer_content")
            answerItem["pubtime"] = answer_dict.get("answer_pubtime")
            answerItem["images"] = answer_dict.get("answer_images")
            answerItem["videos"] = answer_dict.get("answer_videos")
            yield answerItem

        # 嵌套型数据
        zhihuItem = ZhihuItem()
        zhihuItem["url"] = url
        zhihuItem["question_id"] = question_id
        zhihuItem["question_title"] = question_title
        zhihuItem["question_pubtime"] = question_pubtime
        zhihuItem["question_author"] = question_author
        zhihuItem["question_answer_num"] = question_answer_num
        zhihuItem["question_tags"] = question_tags
        zhihuItem["question_content"] = question_content
        zhihuItem["question_images"] = question_images
        zhihuItem["question_videos"] = question_videos
        zhihuItem["answers"] = answers   # 不需要存入question_id

        yield zhihuItem




# 知乎热点(hot)爬取路径
# 1、知乎主页点击跳转(自动登录)——>数据在json里(XHR)      请球头里x-……参数，自定义加密函数，结合环境检测
# 2、直接访问hot页面——>数据在html里面，页面一直处于刷新状态
# 3、从script标签(id="js-initialData")里获取页面json数据进行解析 (当前采用)

# 可优化项
# 1、问题回答内容翻页爬取
# 2、部署至docker，定时爬取实时更新数据
# 3、mongodb数据存储日志(更新or插入数量)及数据更新细则(如何更新/更新哪些update_one参数)
# 4、https://www.zhihu.com/question/23561870  访问页面回答部分显示加载失败了，点击再试试会加载成功，暂时拿不到数据，需要优化
# 5、列表页/详情页cookie信息自动化获取   自动登录(人机验证手动协助)获取并保存登录信息 ！！暂时被封控
# 6、主页跳转请求头加密参数x-……    结合环境监测！！暂时搁置



