import datetime
import logging
import json
import os

from jsonpath_ng import parse
from bs4 import BeautifulSoup

logger = logging.getLogger("scrapy")

def jsonpath_extract(json_data, json_path):
    """
    使用 jsonpath-ng 提取 json 数据
    """
    jsonpath_expr = parse(json_path).find(json_data)
    return [match.value for match in jsonpath_expr] if jsonpath_expr else []

def timestamp_to_str(timestamp, format="%Y-%m-%d %H:%M:%S"):
    """
    时间戳转字符串
    :param timestamp: 时间戳(int或str)
    :param format: 输出格式，默认为"%Y-%m-%d %H:%M:%S"
    :return: 格式化的时间字符串
    """
    if not timestamp:
        return ""
    try:
        ts = int(timestamp)
        if len(str(ts)) > 10:
            ts //= 1000  # 如果是毫秒级时间戳，则转换为秒级(整除)
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime(format)
    except (ValueError, OSError, TypeError) as e:
        logger.info(f"时间戳转换失败：{e}")
        return ""
    
def parse_zhihu_detail(html_str):
    """
    解析知乎详情数据
    :param html_str: 详情数据
    :return: dict {
        'content': str,      # 纯文本内容
        'images': list,   # 图片 URL 列表
        'videos': list    # 视频 URL 列表
    }
    """
    result = {
        'content': '',
        'images': [],
        'videos': []
    }

    if not html_str or not isinstance(html_str, str):
        logger.warning(f"解析数据为空或数据格式错误: {html_str}")
        return result
    
    try:
        soup = BeautifulSoup(html_str, 'html.parser')
        # print(soup.prettify())    # 分行缩进结构化输出需要提取的html
        # 图片
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith('http'):
                result['images'].append(src)
        # TODO 视频 例：https://www.zhihu.com/question/2046232710452965574   detail解析拿到是无效链接，待优化
        # 视频
        for video in soup.find_all('a', class_='video-box'):
            href = video.get('href')
            if href and 'video' in href:
                result['videos'].append(href)

        # 纯文本内容   移除干扰标签（图片，视频，链接等）
        # 单独占位符处理代码块   # 优化：使用占位符替换法处理代码块，避免 get_text() 拆散代码   https://www.zhihu.com/question/68411978/answer/335776437
        code_blocks = []
        for i, highlight in enumerate(soup.find_all('div', class_='highlight')):  # enumerate 遍历一个可迭代对象（如列表、元组、字符串）时，同时获得元素的序号（索引）和元素本身
            code_text = highlight.get_text()  # 取出代码块
            code_blocks.append(code_text)
            # 用唯一占位符替换原标签
            highlight.replace_with(f"__CODE_BLOCK_{i}__")
        for tag in soup.find_all(['img', 'a', 'video']):
            tag.decompose()  #删除该标签及其所有子内容(销毁标签对象)  extract() 移除标签及其内容,会返回被删除的标签
        # 取出其他文本块
        text = soup.get_text(separator='\n', strip=True)   # separator='\n' 不同标签之间的文本用换行符分隔, strip=True 去除每个文本块收尾的空白字符
        # 将占位符替换回完整代码块
        for i, code in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", f"\n```\n{code}\n```\n")  # 区分代码块
        result['content'] = text
    except Exception as e:
        logger.error(f"解析知乎详情数据失败：{e}")
    
    return result
