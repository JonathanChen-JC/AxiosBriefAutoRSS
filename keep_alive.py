#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import logging
import requests
from flask import Flask

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("keep_alive")

# 创建Flask应用
app = Flask(__name__)

# 健康检查端点
@app.route('/')
def home():
    return "AxiosRSS服务正在运行"

@app.route('/health')
def health_check():
    return {"status": "ok", "timestamp": time.time()}

# 自我ping函数
def self_ping():
    """每5分钟ping一次自己，保持服务活跃"""
    # 从环境变量获取应用URL，如果未设置，则使用默认值
    app_url = os.environ.get("APP_URL", "http://localhost:8000")
    
    while True:
        try:
            # 发送请求到健康检查端点
            response = requests.get(f"{app_url}/health")
            if response.status_code == 200:
                logger.info(f"自我ping成功: {response.json()}")
            else:
                logger.warning(f"自我ping返回非200状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"自我ping失败: {str(e)}")
        
        # 等待5分钟
        time.sleep(300)

# 启动自我ping线程
def start_self_ping():
    """启动自我ping线程"""
    ping_thread = threading.Thread(target=self_ping, daemon=True)
    ping_thread.start()
    logger.info("自我ping线程已启动")

# 启动Web服务器
def run_server():
    """启动Web服务器"""
    # 获取端口，如果环境变量中未设置，则使用默认值8000
    port = int(os.environ.get("PORT", 8000))
    
    # 启动自我ping线程
    start_self_ping()
    
    # 启动Flask应用
    logger.info(f"启动Web服务器，端口: {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    run_server()