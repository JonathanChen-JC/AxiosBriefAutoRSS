#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 从keep_alive模块导入Flask应用实例
from keep_alive import app

# 这个文件的目的是为了让Gunicorn能够找到Flask应用实例
# 在Render部署时，Gunicorn会使用 'gunicorn app:app' 命令启动应用
# 其中第一个app是模块名，第二个app是Flask应用实例

if __name__ == "__main__":
    # 如果直接运行此文件，启动Flask应用
    app.run(host='0.0.0.0', port=8000)