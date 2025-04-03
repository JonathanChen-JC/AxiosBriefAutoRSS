  AxiosRSS

![版本](https://img.shields.io/badge/版本-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)

## 项目介绍

AxiosRSS 是一个自动化工具，用于抓取 [Axios](https://www.axios.com/) 新闻网站的内容，使用 Google Gemini AI 生成每日新闻简报，并将其转换为 RSS 订阅源。该项目旨在帮助用户快速获取 Axios 新闻的精华内容，无需浏览整个网站。

### 主要功能

- **自动抓取**：每日自动从 Axios 官方 RSS 源获取最新新闻
- **AI 摘要生成**：使用 Google Gemini AI 对新闻内容进行智能摘要
- **RSS 生成**：将生成的摘要转换为标准 RSS 格式，方便用户订阅
- **GitHub 同步**：自动将生成的 RSS 文件同步到 GitHub 仓库
- **定时执行**：支持定时任务，确保内容定期更新
- **Web 服务**：提供简单的 Web 服务接口，支持健康检查

## 技术架构

项目使用 Python 开发，主要组件包括：

- **数据抓取**：使用 `feedparser` 解析 Axios 的 RSS 源
- **内容处理**：使用 `BeautifulSoup` 处理 HTML 内容
- **AI 摘要**：调用 Google Gemini API 生成摘要
- **RSS 生成**：使用 `feedgenerator` 创建标准 RSS 文件
- **GitHub 集成**：通过 GitHub API 实现文件同步
- **Web 服务**：使用 Flask 提供简单的 Web 接口
- **定时任务**：使用 `schedule` 库实现定时执行

## 安装指南

### 前提条件

- Python 3.10 或更高版本
- Google Gemini API 密钥
- GitHub 个人访问令牌（用于同步功能）

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/AxiosRSS.git
cd AxiosRSS
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

创建 `.env` 文件或直接设置以下环境变量：

```
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro-exp-03-25  # 可选，默认使用此模型
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=your_repo_name
GITHUB_TOKEN=your_github_token
APP_URL=your_app_url  # 部署后的应用URL，用于自我ping
```

## 使用说明

### 本地运行

```bash
python main.py
```

这将启动主程序，执行以下操作：

1. 抓取当天的 Axios 新闻
2. 使用 Gemini AI 生成每日简报
3. 生成 RSS 文件
4. 将 RSS 文件同步到 GitHub

### 手动生成特定日期的简报

```bash
python gemini_summarizer.py --date YYYYMMDD
```

### 定时任务

项目默认配置为每天美东时间上午 9:00 执行一次完整的处理流程。可以在 `main.py` 中修改定时设置。

## 部署指南

### 部署到 Render

1. 在 [Render](https://render.com/) 上创建一个新的 Web 服务
2. 连接到你的 GitHub 仓库
3. 设置以下配置：
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`python render.py`
4. 添加上述环境变量
5. 部署服务

Render 部署会自动启动 Web 服务和定时任务，并通过自我 ping 机制保持服务活跃。

## 项目结构

```
.
├── main.py              # 主程序入口
├── gemini_summarizer.py # Gemini AI 摘要生成模块
├── rss_generator.py     # RSS 生成模块
├── github_sync.py       # GitHub 同步模块
├── keep_alive.py        # Web 服务和保活机制
├── render.py            # Render 部署入口
├── articles/            # 存储抓取的文章
├── dailybrief/          # 存储生成的每日简报
└── axiosbrief.xml       # 生成的 RSS 文件
```

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| GEMINI_API_KEY | 是 | Google Gemini API 密钥 |
| GEMINI_MODEL | 否 | Gemini 模型名称，默认为 gemini-2.5-pro-exp-03-25 |
| GITHUB_REPO_OWNER | 是* | GitHub 仓库所有者用户名 |
| GITHUB_REPO_NAME | 是* | GitHub 仓库名称 |
| GITHUB_TOKEN | 是* | GitHub 个人访问令牌 |
| APP_URL | 是** | 应用部署 URL，用于自我 ping |

*: 如需使用 GitHub 同步功能则必填  
**: 如需使用自我 ping 保活功能则必填

## 常见问题

**Q: 如何获取 Gemini API 密钥？**  
A: 访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 创建 API 密钥。

**Q: 如何创建 GitHub 个人访问令牌？**  
A: 访问 GitHub 设置 -> Developer settings -> Personal access tokens，创建具有 repo 权限的令牌。

**Q: 如何修改摘要生成的提示词？**  
A: 在 `gemini_summarizer.py` 文件中修改 `DEFAULT_PROMPT` 变量。

## 许可证

[MIT](LICENSE)

## 贡献指南

欢迎提交 Issues 和 Pull Requests 来改进项目。

---

*本项目仅用于学习和个人使用，与 Axios 官方无关。*