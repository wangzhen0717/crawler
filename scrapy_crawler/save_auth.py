import logging
import os

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
# from utils import get_logger

load_dotenv()
zhihu_username = os.getenv("ZHIHU_USERNAME")
zhihu_password = os.getenv("ZHIHU_PASSWORD")

def save_auth(platform, login_url, username, password, auth_file="auth.json"):
    """
    保存平台登录信息
    :param username: 用户名
    :param password: 密码
    :return: None
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',    # 禁用自动化控制特征
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'        # 指定和本地一样的ua
            ]
        )
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url)
        # 页面默认为验证码登录，切换为账号密码登录
        page.get_by_role("button", name="密码登录").click()
        # 输入用户名密码
        page.locator('input[name="username"]').fill(username)
        page.locator('input[name="password"]').fill(password)
        # 点击登录按钮
        page.get_by_role("button", name="登录", exact=True).click() # 精确匹配

        # 手动处理页面上的验证码
        input(f"请手动完成{platform}登录验证码，登录成功后按回车...")
        # 登录成功，页面url为知乎首页
        try:
            page.wait_for_url("https://www.zhihu.com/", timeout=10000)
            logging.info("登录成功")
        except TimeoutError as e:
            logging.info(f"登录失败,{e}")

        # 获取登录后的cookies
        context.storage_state(path=auth_file)
        print(f"登录态已保存到 {auth_file}")
        browser.close()

def test_auth():
    """测试登录状态(cookie是否能用)"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="zhihu_auth.json")
        page = context.new_page()
        
        # 访问知乎首页
        response = page.goto("https://www.zhihu.com/hot")
        
        # 检查最终URL，看有没有被重定向到登录页
        print("最终URL:", response.url)
        print("状态码:", response.status)
        
        # 简单检查页面标题是否包含"知乎"
        title = page.title()
        if "知乎" in title:
            print("✅ 登录态有效，页面加载成功")
        else:
            print("❌ 登录态可能失效，页面标题异常:", title)
        
        input("按回车键关闭浏览器...")
        browser.close()


if __name__ == '__main__':
    save_auth("zhihu", "https://www.zhihu.com/signin?next=%2F",
              username=zhihu_username, password=zhihu_password,
              auth_file="scrapy_crawler/zhihu_auth.json")
    

# 命令行获取登陆状态信息（建议项目根目录下执行）   断点问题可以关掉调试
# playwright codegen --save-storage=zhihu_auth.json https://www.zhihu.com/signin?next=%2F

#！！！！！！！！暂时不可行