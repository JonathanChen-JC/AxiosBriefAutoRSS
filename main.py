#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import json
import os
import time
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import schedule
import logging
import threading

# 导入自定义模块
import github_sync
import keep_alive

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("axios_rss")

# 常量定义
RSS_URL = "https://api.axios.com/feed/"
ARTICLES_DIR = "articles"


def ensure_dir_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")


def get_eastern_time():
    """获取当前美东时间"""
    eastern = pytz.timezone('US/Eastern')
    return datetime.datetime.now(eastern)


def is_today_eastern(pub_date):
    """检查发布日期是否为美东时间当天"""
    eastern = pytz.timezone('US/Eastern')
    
    # 解析发布日期
    try:
        # 尝试解析RSS中的日期格式
        dt = datetime.datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
    except ValueError:
        try:
            # 尝试其他可能的日期格式
            dt = datetime.datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            logger.error(f"无法解析日期: {pub_date}")
            return False
    
    # 转换为美东时间
    dt_eastern = dt.astimezone(eastern)
    
    # 获取当前美东时间
    now_eastern = get_eastern_time()
    
    # 检查是否为同一天
    return (dt_eastern.year == now_eastern.year and 
            dt_eastern.month == now_eastern.month and 
            dt_eastern.day == now_eastern.day)


def get_article_content(entry):
    """从RSS条目中提取文章的完整内容"""
    try:
        # 首先尝试从content字段获取内容
        if 'content' in entry and entry.content:
            return entry.content[0].value
        # 然后尝试从summary字段获取内容
        elif 'summary' in entry:
            return entry.summary
        # 最后尝试从description字段获取内容
        elif 'description' in entry:
            return entry.description
        else:
            logger.warning(f"无法找到文章内容: {entry.link}")
            return "无法提取文章内容"
    except Exception as e:
        logger.error(f"提取文章内容时出错: {entry.link if 'link' in entry else 'unknown'}, 错误: {str(e)}")
        return "获取内容时出错"


def fetch_and_save_articles():
    """获取并保存当天的文章"""
    logger.info("开始获取Axios RSS内容")
    
    try:
        # 解析RSS feed
        feed = feedparser.parse(RSS_URL)
        
        if feed.bozo:
            logger.error(f"RSS解析错误: {feed.bozo_exception}")
            return
        
        # 过滤当天的文章
        today_articles = []
        for entry in feed.entries:
            if is_today_eastern(entry.published):
                # 直接从RSS条目中获取文章完整内容
                content = get_article_content(entry)
                
                # 创建文章对象
                article = {
                    "title": entry.title,
                    "published": entry.published,
                    "content": content,
                    "link": entry.link
                }
                
                today_articles.append(article)
                logger.info(f"找到今日文章: {entry.title}")
        
        # 如果有当天的文章，保存为JSON
        if today_articles:
            # 确保目录存在
            ensure_dir_exists(ARTICLES_DIR)
            
            # 生成文件名 (YYYYMMDD格式)
            now = get_eastern_time()
            filename = now.strftime("%Y%m%d") + ".json"
            filepath = os.path.join(ARTICLES_DIR, filename)
            
            # 保存为JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(today_articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存了{len(today_articles)}篇文章到 {filepath}")
        else:
            logger.info("今天没有新文章")
            
    except Exception as e:
        logger.error(f"处理RSS feed时出错: {str(e)}")


def run_daily_tasks():
    """执行每日任务：抓取文章、生成摘要、生成RSS"""
    # 1. 抓取文章
    logger.info("开始执行每日任务")
    fetch_and_save_articles()
    
    # 2. 生成摘要
    try:
        # 获取当前日期
        now = get_eastern_time()
        date_str = now.strftime("%Y%m%d")
        
        # 检查是否有文章文件
        article_file = os.path.join(ARTICLES_DIR, f"{date_str}.json")
        if not os.path.exists(article_file):
            logger.warning(f"没有找到今日文章文件: {article_file}，跳过摘要生成")
            return
        
        # 导入gemini_summarizer模块
        import gemini_summarizer
        
        # 生成摘要
        logger.info("开始生成每日简报")
        success = gemini_summarizer.generate_daily_brief(date_str=date_str)
        if not success:
            logger.error("每日简报生成失败")
            return
        logger.info("每日简报生成成功")
        
        # 3. 生成RSS
        import rss_generator
        
        # 生成RSS
        logger.info("开始生成RSS")
        success = rss_generator.generate_daily_rss(date_str)
        if not success:
            logger.error("RSS生成失败")
            return
        logger.info("RSS生成成功")
        
        # 4. 同步RSS文件到GitHub
        logger.info("开始同步RSS文件到GitHub")
        success = github_sync.update_github_after_local_change()
        if not success:
            logger.warning("同步RSS文件到GitHub失败")
        else:
            logger.info("同步RSS文件到GitHub成功")
        
    except Exception as e:
        logger.error(f"执行每日任务时出错: {str(e)}")


def schedule_job():
    """设置定时任务"""
    # 每天美东时间午夜运行
    schedule.every().day.at("00:00").do(run_daily_tasks)
    logger.info("已设置定时任务，将在美东时间每天00:00运行")
    
    # 立即运行一次，获取当前的文章并生成摘要和RSS
    run_daily_tasks()
    
    # 保持程序运行并执行定时任务
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次是否有待执行的任务


def init_github_sync():
    """初始化GitHub同步"""
    try:
        # 从环境变量获取GitHub信息
        repo_owner = os.environ.get("GITHUB_REPO_OWNER")
        repo_name = os.environ.get("GITHUB_REPO_NAME")
        token = os.environ.get("GITHUB_TOKEN")
        
        if not repo_owner or not repo_name:
            logger.error("未设置GITHUB_REPO_OWNER或GITHUB_REPO_NAME环境变量，无法同步GitHub")
            return False
        
        if not token:
            logger.warning("未设置GITHUB_TOKEN环境变量，将无法更新GitHub文件")
        
        # 同步RSS文件
        logger.info("初始化GitHub同步")
        success = github_sync.sync_rss_with_github(repo_owner, repo_name, token)
        
        if success:
            logger.info("GitHub同步初始化成功")
        else:
            logger.warning("GitHub同步初始化失败")
        
        return success
    except Exception as e:
        logger.error(f"初始化GitHub同步时出错: {str(e)}")
        return False


def start_web_server():
    """在单独的线程中启动Web服务器"""
    web_thread = threading.Thread(target=keep_alive.run_server, daemon=True)
    web_thread.start()
    logger.info("Web服务器线程已启动")


if __name__ == "__main__":
    logger.info("启动Axios RSS抓取程序")
    ensure_dir_exists(ARTICLES_DIR)
    ensure_dir_exists("dailybrief")
    
    # 初始化GitHub同步
    init_github_sync()
    
    # 启动Web服务器（保活功能）
    start_web_server()
    
    # 设置并启动定时任务
    schedule_job()