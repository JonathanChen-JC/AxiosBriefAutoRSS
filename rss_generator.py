#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import markdown
import pytz
import logging
import sys
import feedparser
from feedgen.feed import FeedGenerator

# 设置日志
log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
log_datefmt = '%Y-%m-%d %H:%M:%S %z'

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=log_datefmt,
    handlers=[
        # 标准输出处理器，确保日志在Render平台上可见
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置模块日志记录器
logger = logging.getLogger("rss_generator")
logger.setLevel(logging.INFO)

# 常量定义
ARTICLES_DIR = "articles"
DAILYBRIEF_DIR = "dailybrief"
RSS_FILENAME = "axiosbrief.xml"


def get_eastern_time():
    """获取当前美东时间"""
    eastern = pytz.timezone('US/Eastern')
    return datetime.datetime.now(eastern)

def markdown_to_html(markdown_text):
    """将Markdown文本转换为HTML，确保段落之间有适当的空行
    
    Args:
        markdown_text (str): Markdown格式的文本
        
    Returns:
        str: 转换后的HTML文本，段落之间有适当的空行
    """
    # 分割文本为段落（按照空行分割）
    paragraphs = markdown_text.split('\n\n')
    
    # 处理每个段落
    html_paragraphs = []
    for paragraph in paragraphs:
        # 跳过空段落
        if not paragraph.strip():
            continue
            
        # 处理标题（以**开头和结尾的行）
        if paragraph.strip().startswith('**') and paragraph.strip().endswith('**'):
            # 将Markdown标题转换为HTML标题
            html_paragraph = f'<h3>{paragraph.strip()[2:-2]}</h3>'
        else:
            # 普通段落，添加段落标签
            html_paragraph = f'<p>{paragraph.strip()}</p>'
            
        html_paragraphs.append(html_paragraph)
    
    # 用两个换行符连接段落，确保在RSS阅读器中显示为分隔的段落
    return '\n\n'.join(html_paragraphs)

def generate_daily_rss(date_str=None):
    """生成指定日期的RSS，如果未指定日期则使用当前日期
    追加新内容到现有的RSS feed中，而不是覆盖原有内容
    """
    try:
        # 如果未指定日期，使用当前美东时间的日期
        if not date_str:
            now = get_eastern_time()
            date_str = now.strftime("%Y%m%d")
        
        # 构建简报文件路径
        brief_filepath = os.path.join(DAILYBRIEF_DIR, f"{date_str}.md")
        
        # 检查文件是否存在
        if not os.path.exists(brief_filepath):
            logger.error(f"简报文件不存在: {brief_filepath}")
            return False
        
        # 读取简报内容
        with open(brief_filepath, "r", encoding="utf-8") as f:
            brief_md_content = f.read()
        
        brief_html_content = markdown.markdown(brief_md_content)
        
        # 创建Feed生成器
        fg = FeedGenerator()
        
        # 检查是否存在现有的RSS文件，如果存在则加载它
        if os.path.exists(RSS_FILENAME):
            logger.info(f"发现现有RSS文件: {RSS_FILENAME}，将追加新内容")
            try:
                # 解析现有的RSS文件
                existing_feed = feedparser.parse(RSS_FILENAME)
                
                # 设置基本信息
                fg.id('https://github.com/yourusername/AxiosRSS')
                fg.title('Axios每日简报')
                fg.author({'name': 'AxiosRSS自动生成', 'email': 'example@example.com'})
                fg.link(href='https://github.com/yourusername/AxiosRSS', rel='alternate')
                fg.subtitle('由Gemini AI生成的Axios新闻每日简报')
                fg.language('zh-CN')
                # 设置logo和icon
                fg.logo('https://uploads.concordia.net/2022/09/13152518/Axios-logo-RGB-1.jpg')
                fg.icon('https://uploads.concordia.net/2022/09/13152518/Axios-logo-RGB-1.jpg')
                
                # 添加现有的条目，但限制最多保留49个旧条目（加上新条目共50个）
                entries_to_keep = []
                for entry in existing_feed.entries:
                    # 检查是否已存在相同日期的条目，避免重复
                    entry_date = str(entry.id).split('/')[-1] if hasattr(entry, 'id') else ''
                    if entry_date != date_str:  # 如果不是当前日期的条目，则添加到待保留列表
                        entries_to_keep.append(entry)
                
                # 按发布日期排序（从新到旧）
                entries_to_keep.sort(key=lambda x: datetime.datetime.strptime(
                    x.published.split(',')[1].strip(), '%d %b %Y %H:%M:%S %z' if '%z' in x.published else '%d %b %Y %H:%M:%S -0456'
                ) if hasattr(x, 'published') else datetime.datetime.now(), reverse=True)
                
                # 只保留最新的49个条目（加上新条目共50个）
                if len(entries_to_keep) > 49:
                    entries_to_keep = entries_to_keep[:49]
                    logger.info(f"限制RSS条目数量为50个，移除了最旧的条目")
                
                # 添加保留的条目
                for entry in entries_to_keep:
                    fe = fg.add_entry()
                    fe.id(entry.id)
                    fe.title(entry.title)
                    fe.link(href=entry.link)
                    # 解析发布日期
                    try:
                        pub_date = datetime.datetime.strptime(
                            entry.published, '%a, %d %b %Y %H:%M:%S %z')
                    except ValueError:
                        # 尝试其他可能的日期格式
                        try:
                            pub_date = datetime.datetime.strptime(
                                entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                        except ValueError:
                            # 如果无法解析，使用当前时间
                            pub_date = datetime.datetime.now(pytz.timezone('US/Eastern'))
                    fe.pubDate(pub_date)
                    fe.description(entry.description)
            except Exception as e:
                logger.warning(f"解析现有RSS文件时出错: {str(e)}，将创建新的RSS文件")
                # 如果解析失败，创建新的RSS文件
                fg.id('https://github.com/yourusername/AxiosRSS')
                fg.title('Axios每日简报')
                fg.author({'name': 'AxiosRSS自动生成', 'email': 'example@example.com'})
                fg.link(href='https://github.com/yourusername/AxiosRSS', rel='alternate')
                fg.subtitle('由Gemini AI生成的Axios新闻每日简报')
                fg.language('zh-CN')
        else:
            # 如果不存在现有的RSS文件，创建新的
            logger.info(f"未发现现有RSS文件，将创建新的RSS文件: {RSS_FILENAME}")
            fg.id('https://github.com/yourusername/AxiosRSS')
            fg.title('Axios每日简报')
            fg.author({'name': 'AxiosRSS自动生成', 'email': 'example@example.com'})
            fg.link(href='https://github.com/yourusername/AxiosRSS', rel='alternate')
            fg.subtitle('由Gemini AI生成的Axios新闻每日简报')
            fg.language('zh-CN')
        
        # 解析日期
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        pub_date = datetime.datetime(year, month, day, tzinfo=pytz.timezone('US/Eastern'))
        
        # 添加新条目
        fe = fg.add_entry()
        fe.id(f'https://github.com/yourusername/AxiosRSS/{date_str}')
        fe.title(f'Axios每日简报 {pub_date.strftime("%Y-%m-%d")}')
        fe.link(href=f'https://github.com/yourusername/AxiosRSS/blob/main/dailybrief/{date_str}.md')
        fe.pubDate(pub_date)
        # 添加默认图片
        brief_html_content = f'<img src="https://uploads.concordia.net/2022/09/13152518/Axios-logo-RGB-1.jpg" alt="Axios Logo" style="max-width:100%;height:auto;margin-bottom:20px;"/><br/>{brief_html_content}'
        fe.description(brief_html_content)
        
        # 生成RSS文件
        fg.rss_file(RSS_FILENAME, pretty=True)
        logger.info(f"RSS生成成功: {RSS_FILENAME}")
        return True
    
    except Exception as e:
        logger.error(f"生成RSS失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 如果直接运行此脚本，生成当天的RSS
    generate_daily_rss()