#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 panorama_json 下所有子文件夹中的全景 JSON 里 panorama_images 字段的全部图片
python download_panorama_all.py  [json根目录，默认 panorama_json]
"""

import os
import sys
import json
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

DEFAULT_JSON_DIR = 'C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json'
THREADS = 16
TIMEOUT = 15
CHUNK = 1024 * 64


# ----------------- 工具函数 -----------------
def extract_images(json_file: str):
    """从单个 json 文件里提取所有 panorama_images 链接"""
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)
    panorama_list = data.get('data', {}).get('panorama_list', [])
    urls = []
    for pano in panorama_list:
        raw = pano.get('panorama_images', '[]')
        try:
            imgs = json.loads(raw)
            urls.extend([u.strip() for u in imgs if u.strip().startswith('http')])
        except Exception as e:
            print(f'[WARN] 解析失败 {json_file} -> {e}')
    return urls


def build_local_path(url: str, base_folder='images'):
    """把远程 URL 映射到本地目录，保持目录层级"""
    u = urlparse(url)
    rel_path = u.path.lstrip('/')
    local = os.path.join(base_folder, rel_path)
    return local


def download_one(url: str, base_folder='images'):
    """单文件下载，返回 (url, saved_path|None, error|None)"""
    local = build_local_path(url, base_folder)
    if os.path.isfile(local):
        return url, local, None          # 已存在跳过
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
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

    # 1. 递归扫描所有子文件夹里的 .json
    all_urls = []
    for root, _, files in os.walk(json_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                full = os.path.join(root, fn)
                all_urls.extend(extract_images(full))
    total = len(all_urls)
    print(f'共提取到 {total} 张图片')

    if total == 0:
        print('未找到任何图片链接，程序结束。')
        return

    # 2. 并行下载
    fails = []
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        future_map = {pool.submit(download_one, u): u for u in all_urls}
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