#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import pytz
import requests
import logging
import argparse

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gemini_summarizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gemini_summarizer")

# 常量定义
ARTICLES_DIR = "articles"
DAILYBRIEF_DIR = "dailybrief"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent"


def ensure_dir_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")


def get_eastern_time():
    """获取当前美东时间"""
    eastern = pytz.timezone('US/Eastern')
    return datetime.datetime.now(eastern)


# 默认提示词模板
DEFAULT_PROMPT = """你是美国主流媒体的资深编辑，擅长提炼新闻的要点，并在不遗漏新闻重要信息的前提下，用简练的语言表达。请将文件中的所有新闻，浓缩为要点，整合成一篇每日新闻简报形式的摘要。简报的格式为：

第1自然段：总结文件中所有新闻所涉及的事件，不要展开细节。
接下来的自然段，以每条新闻为一个自然段，分别总结新闻的要点。
最后一个自然段：根据当天的新闻，提供面向政治家和投资者的决策建议。

请注意，你得到文本中存在大量 JSON 格式代码，请正确理解这些代码的含义，同时不要让它们出现于简报中。"""


def load_articles(date_str=None):
    """加载指定日期的文章，如果未指定日期则加载最新的文章"""
    try:
        # 如果未指定日期，使用当前美东时间的日期
        if not date_str:
            now = get_eastern_time()
            date_str = now.strftime("%Y%m%d")
        
        # 构建文件路径
        filepath = os.path.join(ARTICLES_DIR, f"{date_str}.json")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"文件不存在: {filepath}")
            return None
        
        # 加载文章
        with open(filepath, "r", encoding="utf-8") as f:
            articles = json.load(f)
            logger.info(f"从 {filepath} 加载了 {len(articles)} 篇文章")
            return articles
    except Exception as e:
        logger.error(f"加载文章失败: {str(e)}")
        return None


def call_gemini_api(api_key, prompt, articles):
    """调用Gemini API生成摘要"""
    try:
        # 构建请求数据
        request_data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"text": json.dumps(articles, ensure_ascii=False)}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=request_data
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("成功生成摘要")
                return text
            else:
                logger.error(f"API响应中没有找到候选结果: {result}")
        else:
            logger.error(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
        
        return None
    except Exception as e:
        logger.error(f"调用Gemini API失败: {str(e)}")
        return None


def save_daily_brief(content, date_str=None):
    """保存每日简报"""
    try:
        # 如果未指定日期，使用当前美东时间的日期
        if not date_str:
            now = get_eastern_time()
            date_str = now.strftime("%Y%m%d")
        
        # 确保目录存在
        ensure_dir_exists(DAILYBRIEF_DIR)
        
        # 构建文件路径
        filepath = os.path.join(DAILYBRIEF_DIR, f"{date_str}.md")
        
        # 保存简报
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"简报已保存到 {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存简报失败: {str(e)}")
        return None


def generate_daily_brief(api_key, date_str=None):
    """生成每日简报"""
    # 使用默认提示词
    prompt = DEFAULT_PROMPT
    logger.info("使用默认提示词模板")
    
    # 加载文章
    logger.info(f"开始加载文章，日期: {date_str if date_str else '今天'}")
    articles = load_articles(date_str)
    if not articles:
        logger.error(f"文章加载失败，无法继续生成简报")
        return False
    logger.info(f"成功加载{len(articles)}篇文章")
    
    # 调用Gemini API
    logger.info(f"开始调用Gemini API生成摘要")
    summary = call_gemini_api(api_key, prompt, articles)
    if not summary:
        logger.error("Gemini API调用失败，无法生成摘要")
        return False
    logger.info("Gemini API调用成功，已获取摘要")
    
    # 保存简报
    logger.info(f"开始保存简报")
    filepath = save_daily_brief(summary, date_str)
    if not filepath:
        logger.error("简报保存失败")
        return False
    logger.info(f"简报已成功保存到: {filepath}")
    
    return True


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="使用Gemini API生成每日新闻简报")
    parser.add_argument("--api-key", required=True, help="Gemini API密钥")
    parser.add_argument("--date", help="指定日期 (YYYYMMDD格式)，默认为当天")
    args = parser.parse_args()
    
    # 确保目录存在
    ensure_dir_exists(DAILYBRIEF_DIR)
    
    # 生成每日简报
    success = generate_daily_brief(args.api_key, args.date)
    
    if success:
        logger.info("每日简报生成成功")
    else:
        logger.error("每日简报生成失败")


if __name__ == "__main__":
    main()