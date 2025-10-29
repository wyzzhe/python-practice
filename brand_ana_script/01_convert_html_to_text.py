#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 raw_html 文件夹中的 HTML 文件转换为纯文本格式，并以 GBK 编码保存
"""
import pathlib

import sys, os

project_root = pathlib.Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mall_rag_admin.settings')

# from utils.dj_setup import *
import os
import re
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
place_id = os.environ.get('PLACE_ID')
monthly_type = os.environ.get('MONTHLY_TYPE')

def clean_html_content(html_content):
    """
    清理 HTML 内容，提取纯文本
    """
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除 script 和 style 标签
    for script in soup(["script", "style"]):
        script.decompose()

    # 获取纯文本
    text = soup.get_text()

    # 清理文本
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # 移除多余的空白字符
    text = re.sub(r'\n\s*\n', '\n\n', text)  # 将多个空行替换为两个空行
    text = re.sub(r'[ \t]+', ' ', text)  # 将多个空格替换为单个空格

    return text


def convert_html_to_text(input_dir, output_dir):
    """
    将 HTML 文件转换为纯文本文件
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有 HTML 文件
    html_files = list(input_path.glob("*.html"))

    print(f"找到 {len(html_files)} 个 HTML 文件")

    for html_file in html_files:
        try:
            print(f"正在处理: {html_file.name}")

            # 读取 HTML 文件
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            # 清理 HTML 内容
            clean_text = clean_html_content(html_content)

            # 生成输出文件名（将 .html 替换为 .txt）
            output_filename = html_file.stem + '.txt'
            output_file = output_path / output_filename

            # 若输出已存在则跳过
            if output_file.exists():
                print(f"  已存在，跳过: {output_file}")
                continue

            # 以 GBK 编码保存文本文件
            with open(output_file, 'w', encoding='gbk', errors='ignore') as f:
                f.write(clean_text)

            print(f"  已保存: {output_file}")

        except Exception as e:
            print(f"  处理 {html_file.name} 时出错: {e}")

    print(f"\n转换完成！共处理 {len(html_files)} 个文件")
    print(f"输出目录: {output_path.absolute()}")


def main():
    """
    主函数
    """
    # 设置两组输入和输出目录：综合 + 新品（以项目根目录为基准）
    project_root = Path()
    io_pairs = [
        (project_root / f"data/{place_id}/{monthly_type}/raw_html", project_root / f"data/{place_id}/{monthly_type}/raw_text"),
    ]

    print("HTML 转文本转换器")
    print("=" * 50)

    any_processed = False
    for input_dir, output_dir in io_pairs:
        print(f"输入目录: {input_dir}")
        print(f"输出目录: {output_dir}")
        print()

        if not input_dir.exists():
            print(f"跳过：输入目录不存在 -> {input_dir}")
            continue

        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        convert_html_to_text(input_dir, output_dir)
        any_processed = True

    if not any_processed:
        print("未处理任何目录，请检查输入路径是否存在。")


if __name__ == "__main__":
    main()
