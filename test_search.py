"""功能验证：直接调用 search_files 和 list_directory 函数"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from server import search_files, list_directory, search_in_file, is_text_file

# 用当前项目目录做测试
test_dir = os.path.dirname(os.path.dirname(__file__))  # mcp-projects/

print("=" * 50)
print("1. 测试 list_directory")
print("=" * 50)
print(list_directory(test_dir))
print()

print("=" * 50)
print("2. 测试 search_files - 搜 'mcp'")
print("=" * 50)
print(search_files("mcp", test_dir, glob_pattern="*.py"))
print()

print("=" * 50)
print("3. 测试 is_text_file")
print("=" * 50)
for f in os.listdir(os.path.dirname(__file__)):
    fp = os.path.join(os.path.dirname(__file__), f)
    if os.path.isfile(fp):
        print(f"  {f}: is_text = {is_text_file(fp)}")
print()
print("全部测试完成!")
