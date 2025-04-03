#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys

# 设置日志
log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
log_datefmt = '%Y-%m-%d %H:%M:%S %z'

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=log_datefmt,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置模块日志记录器
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# 初始化应用
logger.info("开始初始化应用")

# 执行render.py中的初始化
import render
render.main()

# 从keep_alive模块导入Flask应用实例
from keep_alive import app

if __name__ == "__main__":
    # 如果直接运行此文件，启动Flask应用
    app.run(host='0.0.0.0', port=8000)