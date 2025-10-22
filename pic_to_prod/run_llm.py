#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 panorama_json 下所有子文件夹中的全景 JSON 里 panorama_images 字段的全部图片
URL 里的空格保留，原样下载！
图片保存到 JSON 文件所在目录的 images 子文件夹中，文件名格式为 {uuid}_{index}_{type}.jpg
python download_panorama_keep_space.py  [json根目录，默认 panorama_json]
"""

import os
import sys
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from urllib.parse import urlparse
import re

DEFAULT_JSON_DIR = 'C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json'
THREADS = 16
TIMEOUT = 15
CHUNK = 1024 * 64


# ----------------- 工具函数 -----------------
def extract_images_with_source(json_file: str):
    """从单个 json 文件里提取所有 panorama_images 链接，并记录来源文件"""
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)
    panorama_list = data.get('data', {}).get('panorama_list', [])
    urls = []
    for pano in panorama_list:
        raw = pano.get('panorama_images', '[]')
        try:
            imgs = json.loads(raw)          # 解析 JSON 数组
            urls.extend(imgs)               # 原样保留，包括末尾空格
        except Exception as e:
            print(f'[WARN] 解析失败 {json_file} -> {e}')
    return urls, json_file


def extract_filename_from_url(url: str):
    """
    从 URL 中提取文件名部分
    例如：https://example.com/3c22fc7144cd49b8b7508af648e8955f/28_r.jpg
    返回：3c22fc7144cd49b8b7508af648e8955f_28_r
    """
    try:
        # 获取 URL 的路径部分
        path = urlparse(url).path
        
        # 去掉开头的斜杠和文件扩展名
        path = path.lstrip('/')
        path = re.sub(r'\.(jpg|jpeg|png|webp)$', '', path, flags=re.IGNORECASE)
        
        # 将路径中的斜杠替换为下划线
        filename = path.replace('/', '_')
        
        return filename
    except Exception as e:
        # 如果解析失败，使用备用方案：从 URL 中提取最后两部分
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            # 取最后两部分并用下划线连接
            filename = f"{parts[-2]}_{parts[-1]}"
            # 去掉文件扩展名
            filename = re.sub(r'\.(jpg|jpeg|png|webp)$', '', filename, flags=re.IGNORECASE)
            return filename
        else:
            # 如果还是失败，使用 MD5 作为备用
            import hashlib
            return hashlib.md5(url.encode('utf-8')).hexdigest()


def build_local_path(url: str, json_file_path: str):
    """根据 JSON 文件路径构建本地保存路径"""
    # 获取 JSON 文件所在目录
    json_dir = os.path.dirname(json_file_path)
    
    # 在 JSON 文件目录下创建 images 子文件夹
    images_dir = os.path.join(json_dir, 'images')
    
    # 从 URL 中提取文件名
    filename_base = extract_filename_from_url(url)
    
    # 确保文件名以 .jpg 结尾
    if not filename_base.lower().endswith('.jpg'):
        filename = filename_base + '.jpg'
    else:
        filename = filename_base
    
    # 构建保存路径（在 images 子文件夹中）
    local_path = os.path.join(images_dir, filename)
    return local_path


def download_one(url: str, json_file_path: str):
    """单文件下载，返回 (url, saved_path|None, error|None)"""
    local = build_local_path(url, json_file_path)
    
    if os.path.isfile(local):
        return url, local, None
        
    try:
        # 确保 images 目录存在
        os.makedirs(os.path.dirname(local), exist_ok=True)
        
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(local, 'wb') as f:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    if chunk:
                        f.write(chunk)
        return url, local, None
    except Exception as e:
        return url, None, str(e)


# ----------------- 主流程 -----------------
def main(json_dir: str):
    if not os.path.isdir(json_dir):
        print(f'[ERROR] 目录不存在: {json_dir}')
        sys.exit(1)

    # 1. 递归扫描所有子文件夹里的 .json，并记录来源文件
    all_download_tasks = []  # 每个元素是 (url, json_file_path)
    
    for root, _, files in os.walk(json_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                json_file_path = os.path.join(root, fn)
                urls, source_file = extract_images_with_source(json_file_path)
                for url in urls:
                    all_download_tasks.append((url, source_file))

    total = len(all_download_tasks)
    print(f'共提取到 {total} 张图片（已保留 URL 空格）')

    if total == 0:
        print('未找到任何图片链接，程序结束。')
        return

    # 2. 并行下载
    fails = []
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        future_map = {pool.submit(download_one, url, source_file): (url, source_file) 
                     for url, source_file in all_download_tasks}
        
        for fut in tqdm(as_completed(future_map), total=total, desc='Downloading'):
            url, path, err = fut.result()
            if err:
                fails.append((url, err))

    # 3. 结果汇总
    if fails:
        print(f'\n===== 失败 {len(fails)} 张 =====')
        for u, e in fails:
            print(u, '->', e)
    else:
        print('\n全部下载完成！')


if __name__ == '__main__':
    json_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON_DIR
    main(json_dir)