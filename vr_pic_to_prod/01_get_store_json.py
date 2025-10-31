import requests
import json
import os
import time
from typing import Dict, List
from store_view_dict import store_view_dict

def fetch_store_data(store_id: str, store_name: str) -> bool:
    """
    获取店铺数据并保存为JSON文件
    
    Args:
        store_id: 店铺ID
        store_name: 店铺名称
        
    Returns:
        bool: 是否成功
    """
    url = "https://vr.aibee.cn/aibee-vr/list-panoramas?secret=U4LOTsSWEASOCXNl4lzyg0rOyGztm1so"
    
    payload = {"store_id": store_id}
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_root = os.path.join(script_dir, 'panorama_json')

        # 构建目标目录路径
        store_dir = os.path.join(json_root, store_name)
        os.makedirs(store_dir, exist_ok=True)

        # 保存文件
        filename = os.path.join(store_dir, f"{store_name}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功保存: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ 失败 {store_name}: {e}")
        return False

def batch_fetch_stores(store_list: Dict[str, str], delay: float = 1.0):
    """
    批量获取店铺数据
    
    Args:
        store_list: 店铺字典 {店铺名: store_id}
        delay: 请求间隔时间(秒)，避免请求过快
    """
    print(f"开始爬取 {len(store_list)} 个店铺的数据...")
    
    success_count = 0
    for store_name, store_id in store_list.items():
        print(f"正在处理: {store_name}")
        
        if fetch_store_data(store_id, store_name):
            success_count += 1
        
        # 添加延迟，避免请求过快
        if delay > 0:
            time.sleep(delay)
    
    print(f"\n爬取完成！成功: {success_count}/{len(store_list)}")

# 使用方法
if __name__ == "__main__":
    # 你的店铺列表
    batch_fetch_stores(store_view_dict, delay=0.5)