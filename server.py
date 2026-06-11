"""
File Search MCP Server — 本地文件搜索 MCP Server
提供两个 Tool 和两个 Resource：

Tool:
1. search_files(keyword, directory) — 递归搜索文件内容中的关键词
2. list_directory(path, pattern) — 列出目录中的文件

Resource:
1. search://stats — 搜索统计（累计搜索次数、最近搜索记录）
2. config://settings — 当前配置（跳过的目录、最大文件大小等）

适合场景：在项目代码、文档、日志中快速定位关键词。
"""

import os
import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("File Search MCP")

# ========== 内存中的搜索历史 ==========
_search_count: int = 0
_search_history: list[dict] = []  # 最近 20 条
_MAX_HISTORY = 20

# 常见文本文件扩展名，避免搜二进制文件
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
    ".html", ".css", ".scss", ".xml", ".csv", ".log", ".ini", ".cfg", ".toml",
    ".env", ".gitignore", ".dockerignore", ".sh", ".bat", ".ps1", ".sql", ".r",
    ".java", ".kt", ".swift", ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".rb",
    ".php", ".vue", ".svelte", ".astro", ".graphql", ".proto", ".tex", ".rst",
}

# 默认跳过这些目录
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".nuxt"}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 跳过大于 2MB 的文件
MAX_RESULTS = 50  # 默认最多返回 50 条结果


def is_text_file(filepath: str) -> bool:
    """判断是否为文本文件（先看扩展名，再尝试读取）"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return True
    if ext:
        return False  # 未知扩展名且不是无扩展名，跳过
    # 没有扩展名（如 Makefile、Dockerfile），尝试读取前几个字节
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(512)
        # 包含 null 字节 → 极可能是二进制
        return b"\x00" not in chunk
    except Exception:
        return False


def search_in_file(filepath: str, keyword: str, case_sensitive: bool) -> list[dict]:
    """在单个文件中搜索关键词，返回匹配行列表"""
    matches = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                target = line if case_sensitive else line.lower()
                kw = keyword if case_sensitive else keyword.lower()
                if kw in target:
                    matches.append({
                        "line": i,
                        "content": line.strip()[:200]  # 截断过长行
                    })
    except Exception:
        pass
    return matches


@mcp.tool()
def search_files(
    keyword: str,
    directory: str = ".",
    glob_pattern: str = "*",
    max_results: int = MAX_RESULTS,
    case_sensitive: bool = False,
) -> str:
    """在指定目录中递归搜索文件内容，返回包含关键词的文件路径、行号和匹配行。

    参数:
    - keyword: 搜索关键词（必填）
    - directory: 搜索目录路径，默认当前目录
    - glob_pattern: 文件名过滤，如 "*.py" 或 "*.md"
    - max_results: 最多返回多少条结果，默认 50
    - case_sensitive: 是否区分大小写，默认否
    """
    directory = os.path.abspath(os.path.expanduser(directory))
    if not os.path.isdir(directory):
        return f"错误：目录不存在 —— {directory}"

    all_matches = []
    files_searched = 0

    for root, dirs, files in os.walk(directory):
        # 跳过不需要的目录
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if not fnmatch.fnmatch(filename, glob_pattern):
                continue

            filepath = os.path.join(root, filename)

            # 跳过过大的文件
            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            if not is_text_file(filepath):
                continue

            files_searched += 1
            matches = search_in_file(filepath, keyword, case_sensitive)

            for m in matches:
                all_matches.append({
                    "file": os.path.relpath(filepath, directory),
                    "line": m["line"],
                    "content": m["content"],
                })
                if len(all_matches) >= max_results:
                    break

            if len(all_matches) >= max_results:
                break

        if len(all_matches) >= max_results:
            break

    # 记录搜索历史
    global _search_count, _search_history
    _search_count += 1
    _search_history.insert(0, {
        "keyword": keyword,
        "directory": directory,
        "glob": glob_pattern,
        "results": len(all_matches),
        "files_searched": files_searched,
        "time": datetime.now(timezone.utc).isoformat(),
    })
    if len(_search_history) > _MAX_HISTORY:
        _search_history.pop()

    # 格式化输出
    if not all_matches:
        return (
            f"未找到包含「{keyword}」的文件。\n"
            f"搜索目录: {directory}\n"
            f"已搜索文本文件: {files_searched} 个"
        )

    lines = [f"搜索「{keyword}」—— 找到 {len(all_matches)} 条结果（搜索了 {files_searched} 个文件）:\n"]
    for m in all_matches:
        lines.append(f"  {m['file']}:{m['line']}  |  {m['content']}")

    if len(all_matches) >= max_results:
        lines.append(f"\n(结果已达上限 {max_results} 条，缩小搜索范围可获得更精确结果)")

    return "\n".join(lines)


@mcp.tool()
def list_directory(
    path: str = ".",
    glob_pattern: str = "*",
    show_hidden: bool = False,
) -> str:
    """列出指定目录中的文件和子目录。

    参数:
    - path: 目录路径，默认当前目录
    - glob_pattern: 文件名过滤，如 "*.py"
    - show_hidden: 是否显示隐藏文件（以 . 开头），默认否
    """
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(path):
        return f"错误：目录不存在 —— {path}"

    items = []
    try:
        for entry in sorted(os.listdir(path)):
            if not show_hidden and entry.startswith("."):
                continue
            full = os.path.join(path, entry)
            if not fnmatch.fnmatch(entry, glob_pattern):
                continue
            tag = "[DIR] " if os.path.isdir(full) else "[FILE]"
            items.append(f"  {tag}  {entry}")

    except PermissionError:
        return f"错误：没有权限访问目录 —— {path}"

    if not items:
        return f"目录 {path} 中没有匹配 '{glob_pattern}' 的文件"

    return f"目录 {path} 的内容:\n" + "\n".join(items)


# ========== Resource 原语 ==========

@mcp.resource("search://stats", name="搜索统计", description="返回累计搜索次数和最近搜索记录")
def search_stats() -> str:
    """返回搜索统计信息（JSON 格式）"""
    return json.dumps({
        "total_searches": _search_count,
        "recent_searches": _search_history,
        "max_history": _MAX_HISTORY,
    }, ensure_ascii=False, indent=2)


@mcp.resource("config://settings", name="当前配置", description="返回 File Search MCP Server 的当前配置")
def config_settings() -> str:
    """返回当前配置信息（JSON 格式）"""
    return json.dumps({
        "text_extensions": sorted(TEXT_EXTENSIONS),
        "skip_directories": sorted(SKIP_DIRS),
        "max_file_size_bytes": MAX_FILE_SIZE,
        "max_results_per_search": MAX_RESULTS,
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
