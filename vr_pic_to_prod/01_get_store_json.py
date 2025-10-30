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
    stores = {
        "BIRKENSTOCK": "rnigHTJW6gZ1WvN8",
        "JOMALONE": "wProWw3VWvxMXjSe",
        "MCM": "IggvX5NAGCBYGghG",
        "HOURGLASS": "t9UIduAKaGQ6iSpL",
        "SK-2": "WURVaubhFG1Zo4i7",
        "ARMANI": "3JDW9p6znrMepLeW",
        "Whoo": "jZodpniiOIyKB0T4",
        "apm": "hmYDdSnqARaUL53I",
        "PRADA": "ak3kgLadqHujKhub",
        "BVLGARI": "LpyhRRXZa4G4DSxm",
        "GUERLAIN": "0GqnCykmp5mOeGoQ",
        "JORDAN": "HDUJQhI8E18QsxPk",
        "SKINCEUTICALS": "xzGVEl38OXW9Zid5",
        "BROMPTON": "N1vfzj3dO5rgiSJt",
        "BOBBIBROWN": "6NLu57R9xBvtHe6V",
        "ACQUADIPARMA": "O8mlHKnzTO2mbOmY",
        "cledepeau": "ZcuSRtGblQozinwK",
        "TOMFORD": "JJ9Gbpcytf9gwCSN",
        "HERMES": "P1BLhggCACUmdSS3",
        "LANCOME": "rUfFij7SItdZtJXJ",
        "DECORTE": "SsH8RekNya3OOPKz",
        "VALMONT": "p5R3uVLXilDq9RhE",
        "sisly": "MMzt3bZ1qXnsgSKc",
        "laprairie": "FOoMcyY53FdQ4QMZ",
        "Eland": "w5dYvSXJ0hwxwK86",
        "CLARINS": "vXYYtYkxYtWOTRZh",
        "13DEMARZO": "8G9EN0maAHsqvbnV",
        "WE11DONE": "lwsugpDHzMY1zObr",
        "MICHAELKORS": "FBYSLzoCVQ8mihaZ",
        "蔚来": "q9miW0WJbi7HycrE",
        "BALLY": "93yqMh6CZEOmksbE",
        "OMEGA": "nKNnCpr4FVuyprVu",
        "Caurtier": "dnMffFWJ7BRKDrTU",
        "HEFANG": "F0iNsPY8PQJluclQ",
        "CUCCI": "8ZmBSWC9VvAnKkZG",
        "IWC": "znTthd2FSEnmjQLV",
        "智己": "i3fumkKm7tFtYusJ",
        "睿锦尚品": "P0xC1z9hVr3zmJmo",
        "TUDOR": "ZHvseHy0ATYHaRyN",
        "L'OCCITANE": "fuH9KBjx2TzSNzGf",
        "DIOR": "Pykl9tIdgeXnq00A",
        "HIEIDO": "RE8KrirSDSt6Y5l2",
        "LAMER": "TYCOtw4zpRnVYc6n",
        "雅诗兰黛": "n1lmIUsnhnoLv994",
        "GIVENCHY": "dnGOm3Fs3yin8btm",
        "BOOS": "qdOgKDWts8cB2PCC",
        "六福珠宝": "wsw0UmU9FdiG2EKC",
        "老庙": "xfCOfrfS1a0THHdX",
        "老凤祥": "rrTijKwe7bzYKkxU",
        "诗普琳": "S01PXrezDO2vZn7H",
        "中国珠宝": "QYQYy32fPjL11VGs",
        "周生生": "irGehvOv1nWI24Y0",
        "潮宏基": "Guu2q4xqu3m7xVV9",
        "周大生": "tafGlH95BnEY46aF",
        "DR": "pGqn9Aov6EPQEbpS",
        "中国黄金": "q3hgWcAmCDkxXiQO",
        "Dissona": "537VM2h98CmQa75M",
        "珠利莱": "fzmhb2EATcSWpPS5",
        "ST&SAT": "NVnfSXUtfhOWKFJG",
        "GG-CC": "sOpglG1QDVsJDULW",
        "太平鸟": "awldtX6UIJI9ZhXr",
        "MO&CO": "yMTCrfwjO6NzN9Ep",
        "安踏": "iaLmwKGtFquzmC5d",
        "李宁": "Rcreb3uQgdTqz8U5",
        "耐克": "ZMdyjpLTu1ATFNi0",
        "O'eat": "RnbLw8dT9JWulKP3",
        "兰湘子": "iOe8mUI7u0jouEXK",
        "阿吉豆": "lis7L2XkpVWDtJvC",
        "浮光之秋": "CZqWyGLGzvpbJXnW"
    }
    
    batch_fetch_stores(stores, delay=0.5)