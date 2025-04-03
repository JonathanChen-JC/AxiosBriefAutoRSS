#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import subprocess
import time

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
        logging.StreamHandler(sys.stdout),
        # 文件处理器，在本地开发时保存日志
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

# 设置模块日志记录器
logger = logging.getLogger("render_init")
logger.setLevel(logging.INFO)

# 检查环境变量
def check_environment():
    """检查必要的环境变量是否已设置"""
    required_vars = [
        "GEMINI_API_KEY",
        "GITHUB_REPO_OWNER",
        "GITHUB_REPO_NAME",
        "GITHUB_TOKEN",
        "APP_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f"以下环境变量未设置: {', '.join(missing_vars)}")
        
        # GEMINI_API_KEY是必须的
        if "GEMINI_API_KEY" in missing_vars:
            logger.error("GEMINI_API_KEY环境变量未设置，程序无法正常运行")
            return False
        
        # GitHub相关变量缺失会影响同步功能
        if any(var in missing_vars for var in ["GITHUB_REPO_OWNER", "GITHUB_REPO_NAME", "GITHUB_TOKEN"]):
            logger.warning("GitHub相关环境变量未完全设置，GitHub同步功能将不可用")
        
        # APP_URL缺失会影响保活功能
        if "APP_URL" in missing_vars:
            logger.warning("APP_URL环境变量未设置，自我ping功能可能无法正常工作")
    
    return True

# 安装依赖
def install_dependencies():
    """安装项目依赖"""
    try:
        logger.info("开始安装项目依赖")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("项目依赖安装完成")
        return True
    except Exception as e:
        logger.error(f"安装依赖时出错: {str(e)}")
        return False

# 更新requirements.txt
def update_requirements():
    """确保requirements.txt包含所有必要的依赖"""
    try:
        # 读取现有的requirements.txt
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        # 检查并添加缺失的依赖
        new_dependencies = []
        
        if "flask" not in requirements.lower():
            new_dependencies.append("flask==2.0.1")
        
        if "gunicorn" not in requirements.lower():
            new_dependencies.append("gunicorn==20.1.0")
        
        # 如果有新依赖需要添加
        if new_dependencies:
            logger.info(f"向requirements.txt添加新依赖: {', '.join(new_dependencies)}")
            
            with open("requirements.txt", "a") as f:
                f.write("\n" + "\n".join(new_dependencies))
            
            # 重新安装依赖
            return install_dependencies()
        
        return True
    except Exception as e:
        logger.error(f"更新requirements.txt时出错: {str(e)}")
        return False

# 主函数
def main():
    """初始化并启动应用"""
    logger.info("开始初始化Render部署")
    
    # 检查环境变量
    if not check_environment():
        logger.warning("环境变量检查未通过，但将尝试继续运行")
    
    # 更新requirements.txt并安装依赖
    if not update_requirements():
        logger.error("依赖安装失败，程序可能无法正常运行")
    
    # 启动主应用
    try:
        logger.info("启动主应用")
        import main
        main.init_github_sync()
        main.start_web_server()
        main.schedule_job()
    except Exception as e:
        logger.error(f"启动主应用时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()