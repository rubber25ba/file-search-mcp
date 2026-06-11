# File Search MCP 🔍

一个基于 **FastMCP** 的本地文件搜索 MCP Server。让 Claude 能够递归搜索项目文件内容，快速定位关键词。

## 功能

### Tool（工具）

| 工具 | 说明 |
|------|------|
| `search_files(keyword, directory)` | 递归搜索文件内容中的关键词，返回匹配的文件路径、行号和内容 |
| `list_directory(path, pattern)` | 列出目录中的文件和子目录，支持 glob 过滤 |

### Resource（资源）

| 资源 URI | 说明 |
|----------|------|
| `search://stats` | 搜索统计：累计搜索次数、最近 20 条搜索记录 |
| `config://settings` | 当前配置：文本扩展名白名单、跳过目录、文件大小上限等 |

## 特性

- 🧠 **智能文件识别** — 白名单扩展名 + 二进制检测（null byte 扫描），避免搜索图片/压缩包/可执行文件
- 🚫 **自动跳过无关目录** — 默认跳过 `.git`、`node_modules`、`__pycache__`、`venv` 等
- 📏 **大文件保护** — 自动跳过大于 2MB 的文件，防止卡顿
- 🔤 **大小写可选** — 默认不区分大小写，也可精确匹配
- 🎯 **结果上限** — 默认最多返回 50 条，避免输出爆炸
- 📋 **搜索历史** — 内存中保留最近 20 条搜索记录，可通过 Resource 查看

## 快速开始

### 环境要求

- Python 3.10+
- [fastmcp](https://github.com/jlowin/fastmcp) >= 3.0

### 安装

```bash
# 克隆仓库
git clone https://github.com/rubber25ba/file-search-mcp.git
cd file-search-mcp

# 创建虚拟环境（推荐）
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install fastmcp
```

### 本地测试

```bash
python server.py
```

## 在 Claude Code 中配置

在 Claude Code 的 `settings.json` 中添加：

```json
{
  "mcpServers": {
    "file-search": {
      "command": "python",
      "args": ["C:/Users/YOUR_USERNAME/path/to/file-search-mcp/server.py"]
    }
  }
}
```

> 也可以在 Claude Code 中输入 `/config` 打开配置面板，选择 MCP Servers → Add，填写：
> - Name: `file-search`
> - Command: `python`
> - Args: `["你的路径/file-search-mcp/server.py"]`

配置完成后重启 Claude Code，试试：

- 「搜索 mcp-projects 目录下提到 FastMCP 的文件」
- 「列出桌面上所有的 .py 文件」

## 使用示例

### 示例 1：搜索代码中的关键词

```
用户：搜索当前项目里所有提到 "TODO" 的文件

Claude 调用 search_files(keyword="TODO", directory=".", glob_pattern="*.py")
→ 返回所有包含 TODO 的 Python 文件路径、行号和内容
```

### 示例 2：列出目录结构

```
用户：桌面上有哪些 Markdown 文件？

Claude 调用 list_directory(path="~/Desktop", glob_pattern="*.md")
→ 列出桌面上所有 .md 文件
```

### 示例 3：查看搜索统计

```
用户：我最近搜了什么？

Claude 读取 resource search://stats
→ 返回搜索次数和历史记录
```

## 配置说明

可以在 `server.py` 中修改以下常量：

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `MAX_RESULTS` | 50 | 单次搜索最多返回结果数 |
| `MAX_FILE_SIZE` | 2MB | 跳过的文件大小阈值 |
| `SKIP_DIRS` | `.git`, `node_modules`, ... | 跳过搜索的目录名 |
| `TEXT_EXTENSIONS` | `.py`, `.js`, `.md`, ... | 文本文件扩展名白名单 |

## 项目结构

```
file-search-mcp/
├── server.py      # MCP Server 主程序（Tool + Resource）
└── README.md      # 本文件
```

## 技术栈

- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP Server 框架
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) — Anthropic 推出的 AI 工具集成协议

## License

MIT
