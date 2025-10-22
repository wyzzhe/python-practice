import requests
import json
import os
import time
from typing import Dict, List

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
        
        # 创建目录
        os.makedirs(store_name, exist_ok=True)
        
        # 保存文件
        filename = f"{store_name}/{store_name}.json"
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
    stores = {
        "BIRKENSTOCK": "rnigHTJW6gZ1WvN8",
        "JOMALONE": "wProWw3VWvxMXjSe"
        # 可以继续添加更多店铺...
        # "店铺名": "store_id",
    }
    
    batch_fetch_stores(stores, delay=0.5)