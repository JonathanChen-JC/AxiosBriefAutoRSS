#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import logging
import base64
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("github_sync")

# 常量定义
RSS_FILENAME = "axiosbrief.xml"


def get_github_file_content(repo_owner, repo_name, file_path, branch="main", token=None):
    """从GitHub获取文件内容"""
    try:
        # 构建API URL
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
        
        # 设置请求头
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        
        # 发送请求
        response = requests.get(url, headers=headers)
        
        # 检查响应
        if response.status_code == 200:
            # 解码内容
            content_data = response.json()
            if content_data.get("encoding") == "base64":
                content = base64.b64decode(content_data["content"]).decode("utf-8")
                logger.info(f"成功从GitHub获取文件: {file_path}")
                return content
            else:
                logger.error(f"不支持的编码: {content_data.get('encoding')}")
        elif response.status_code == 404:
            logger.warning(f"GitHub上未找到文件: {file_path}")
            return None
        else:
            logger.error(f"获取GitHub文件失败，状态码: {response.status_code}, 响应: {response.text}")
        
        return None
    except Exception as e:
        logger.error(f"从GitHub获取文件时出错: {str(e)}")
        return None


def update_github_file(repo_owner, repo_name, file_path, content, commit_message, branch="main", token=None):
    """更新GitHub上的文件"""
    try:
        if not token:
            logger.error("未提供GitHub访问令牌，无法更新文件")
            return False
        
        # 首先获取文件的SHA值
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}"
        }
        
        # 获取当前文件信息
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # 文件存在，获取SHA
            file_sha = response.json()["sha"]
        elif response.status_code == 404:
            # 文件不存在
            file_sha = None
        else:
            logger.error(f"获取文件信息失败，状态码: {response.status_code}, 响应: {response.text}")
            return False
        
        # 准备更新数据
        update_data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }
        
        # 如果文件已存在，添加SHA
        if file_sha:
            update_data["sha"] = file_sha
        
        # 发送更新请求
        response = requests.put(url, headers=headers, json=update_data)
        
        # 检查响应
        if response.status_code in [200, 201]:
            logger.info(f"成功更新GitHub文件: {file_path}")
            return True
        else:
            logger.error(f"更新GitHub文件失败，状态码: {response.status_code}, 响应: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"更新GitHub文件时出错: {str(e)}")
        return False


def parse_last_build_date(xml_content):
    """从XML内容中解析lastBuildDate"""
    try:
        if not xml_content:
            return None
        
        # 解析XML
        root = ET.fromstring(xml_content)
        
        # 查找lastBuildDate元素
        last_build_date_elem = root.find("./channel/lastBuildDate")
        
        if last_build_date_elem is not None and last_build_date_elem.text:
            # 解析日期
            date_str = last_build_date_elem.text
            try:
                # 尝试解析RSS中的日期格式
                dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                return dt
            except ValueError:
                try:
                    # 尝试其他可能的日期格式
                    dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                    return dt
                except ValueError:
                    logger.error(f"无法解析lastBuildDate: {date_str}")
        
        return None
    except Exception as e:
        logger.error(f"解析lastBuildDate时出错: {str(e)}")
        return None


def sync_rss_with_github(repo_owner, repo_name, token=None):
    """同步本地和GitHub上的RSS文件"""
    try:
        # 检查本地文件是否存在
        local_exists = os.path.exists(RSS_FILENAME)
        
        # 从GitHub获取文件内容
        github_content = get_github_file_content(repo_owner, repo_name, RSS_FILENAME, token=token)
        github_exists = github_content is not None
        
        # 如果两者都不存在，无需同步
        if not local_exists and not github_exists:
            logger.info("本地和GitHub上都不存在RSS文件，无需同步")
            return True
        
        # 如果只有GitHub上存在，下载到本地
        if not local_exists and github_exists:
            with open(RSS_FILENAME, "w", encoding="utf-8") as f:
                f.write(github_content)
            logger.info(f"从GitHub下载RSS文件到本地: {RSS_FILENAME}")
            return True
        
        # 如果只有本地存在，上传到GitHub
        if local_exists and not github_exists:
            with open(RSS_FILENAME, "r", encoding="utf-8") as f:
                local_content = f.read()
            
            success = update_github_file(
                repo_owner, repo_name, RSS_FILENAME, local_content,
                "初始化RSS文件", token=token
            )
            
            if success:
                logger.info(f"成功将本地RSS文件上传到GitHub: {RSS_FILENAME}")
            else:
                logger.error(f"上传本地RSS文件到GitHub失败")
            
            return success
        
        # 如果两者都存在，比较lastBuildDate并使用较新的版本
        with open(RSS_FILENAME, "r", encoding="utf-8") as f:
            local_content = f.read()
        
        # 解析lastBuildDate
        local_date = parse_last_build_date(local_content)
        github_date = parse_last_build_date(github_content)
        
        # 如果无法解析日期，记录警告并保持现状
        if local_date is None and github_date is None:
            logger.warning("无法解析本地和GitHub RSS文件的lastBuildDate，保持现状")
            return True
        
        # 如果只有一个可以解析，使用可解析的那个
        if local_date is None:
            with open(RSS_FILENAME, "w", encoding="utf-8") as f:
                f.write(github_content)
            logger.info(f"使用GitHub上的RSS文件（本地文件日期无法解析）")
            return True
        
        if github_date is None:
            success = update_github_file(
                repo_owner, repo_name, RSS_FILENAME, local_content,
                "更新RSS文件（GitHub文件日期无法解析）", token=token
            )
            
            if success:
                logger.info(f"使用本地RSS文件更新GitHub（GitHub文件日期无法解析）")
            else:
                logger.error(f"更新GitHub RSS文件失败")
            
            return success
        
        # 比较日期并使用较新的版本
        if github_date > local_date:
            # GitHub版本较新，更新本地文件
            with open(RSS_FILENAME, "w", encoding="utf-8") as f:
                f.write(github_content)
            logger.info(f"使用GitHub上的较新RSS文件更新本地文件")
            return True
        elif local_date > github_date:
            # 本地版本较新，更新GitHub文件
            success = update_github_file(
                repo_owner, repo_name, RSS_FILENAME, local_content,
                "更新RSS文件（本地版本较新）", token=token
            )
            
            if success:
                logger.info(f"使用本地较新RSS文件更新GitHub")
            else:
                logger.error(f"更新GitHub RSS文件失败")
            
            return success
        else:
            # 日期相同，无需更新
            logger.info("本地和GitHub RSS文件日期相同，无需同步")
            return True
        
    except Exception as e:
        logger.error(f"同步RSS文件时出错: {str(e)}")
        return False


def update_github_after_local_change():
    """本地RSS文件更新后，同步到GitHub"""
    try:
        # 从环境变量获取GitHub信息
        repo_owner = os.environ.get("GITHUB_REPO_OWNER")
        repo_name = os.environ.get("GITHUB_REPO_NAME")
        token = os.environ.get("GITHUB_TOKEN")
        
        if not repo_owner or not repo_name:
            logger.error("未设置GITHUB_REPO_OWNER或GITHUB_REPO_NAME环境变量，无法同步到GitHub")
            return False
        
        if not token:
            logger.error("未设置GITHUB_TOKEN环境变量，无法同步到GitHub")
            return False
        
        # 检查本地文件是否存在
        if not os.path.exists(RSS_FILENAME):
            logger.error(f"本地RSS文件不存在: {RSS_FILENAME}")
            return False
        
        # 读取本地文件内容
        with open(RSS_FILENAME, "r", encoding="utf-8") as f:
            local_content = f.read()
        
        # 更新GitHub文件
        success = update_github_file(
            repo_owner, repo_name, RSS_FILENAME, local_content,
            "更新RSS文件", token=token
        )
        
        if success:
            logger.info(f"成功将本地RSS文件同步到GitHub")
        else:
            logger.error(f"同步本地RSS文件到GitHub失败")
        
        return success
    
    except Exception as e:
        logger.error(f"同步本地RSS文件到GitHub时出错: {str(e)}")
        return False


if __name__ == "__main__":
    # 从环境变量获取GitHub信息
    repo_owner = os.environ.get("GITHUB_REPO_OWNER")
    repo_name = os.environ.get("GITHUB_REPO_NAME")
    token = os.environ.get("GITHUB_TOKEN")
    
    if not repo_owner or not repo_name:
        logger.error("未设置GITHUB_REPO_OWNER或GITHUB_REPO_NAME环境变量")
    elif not token:
        logger.warning("未设置GITHUB_TOKEN环境变量，将无法更新GitHub文件")
    else:
        # 同步RSS文件
        sync_rss_with_github(repo_owner, repo_name, token)