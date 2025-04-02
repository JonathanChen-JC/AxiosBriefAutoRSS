#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import json

# 解析RSS feed
feed = feedparser.parse('https://api.axios.com/feed/')

# 提取第一篇文章的信息
if feed.entries:
    entry = feed.entries[0]
    # 打印文章结构
    print("\nRSS条目结构:")
    for key in entry.keys():
        print(f"- {key}")
    
    # 检查是否包含内容
    if 'content' in entry:
        print("\n文章内容示例:")
        print(entry.content[0].value[:500] + "...")
    elif 'summary' in entry:
        print("\n文章摘要示例:")
        print(entry.summary[:500] + "...")
    
    # 检查其他可能包含内容的字段
    for field in ['description', 'summary_detail']:
        if field in entry:
            print(f"\n{field}示例:")
            content = entry[field]
            if isinstance(content, str):
                print(content[:500] + "...")
            else:
                print(json.dumps(content, ensure_ascii=False, indent=2))
else:
    print("没有找到任何文章")