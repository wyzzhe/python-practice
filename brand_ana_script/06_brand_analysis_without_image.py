#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝商品品牌画像分析工具

基于商品标题、价格、销量等文本信息，使用OpenAI大模型分析各品牌的商品数据
生成简洁实用的品牌画像报告，为购物者提供品牌推荐和购买指引

作者: AI Assistant
创建时间: 2024-08-25
"""

import json
import os
import pathlib
import sys
import statistics
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import time
import re
import glob


project_root = pathlib.Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mall_rag_admin.settings')

# from utils.dj_setup import *

from dotenv import load_dotenv

load_dotenv()
place_id = os.environ.get('PLACE_ID')
monthly_type = os.environ.get('MONTHLY_TYPE')

class BrandAnalyzer:
    """品牌商品数据分析器 - 基于文本信息生成品牌画像"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, date_dir: str = "202508", force_reanalyze: bool = False):
        """
        初始化分析器
        
        Args:
            api_key: OpenAI API密钥，如果不提供则从环境变量OPENAI_API_KEY获取
            base_url: API基础URL，支持自定义端点
            date_dir: 日期目录名称，用于输出文件路径
            force_reanalyze: 是否强制重新分析所有品牌
        """
        # 设置API密钥和基础URL
        self.api_key = api_key or "2a62f511-c4ac-4415-b51f-080931703a0b"
        self.base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        
        # 初始化豆包thinking模型
        self.client = ChatOpenAI(
            temperature=0.7,
            model="doubao-seed-1-6-thinking-250715",
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            max_tokens=6000,  # 适中的输出长度
            streaming=True
        )
        
        # 品牌数据存储
        self.brand_data = {}
        self.analysis_results = {}
        self.date_dir = pathlib.Path(date_dir)
        self.force_reanalyze = force_reanalyze
        
    def check_brand_already_analyzed(self, brand: str) -> bool:
        """
        检查品牌是否已经分析过
        
        Args:
            brand: 品牌名称
            
        Returns:
            True表示已分析过，False表示未分析
        """
        # 如果强制重新分析，直接返回False
        if self.force_reanalyze:
            print(f"🔄 {brand} 品牌强制重新分析")
            return False
            
        try:
            # 检查品牌分析结果文件是否存在
            safe_brand_name = brand.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            latest_file = fr"data/{place_id}/{monthly_type}/brand_analysis/{brand}/{safe_brand_name}_latest.json"

            if os.path.exists(latest_file):
                # 检查文件内容是否完整
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        existing_result = json.load(f)
                    
                    # 检查是否有完整的品牌画像
                    brand_profile = existing_result.get('brand_profile', {})
                    if isinstance(brand_profile, dict) and 'market_position' in brand_profile:
                        print(f"✅ {brand} 品牌已分析过，跳过重复分析")
                        return True
                    elif 'error' in brand_profile:
                        print(f"⚠️  {brand} 品牌之前分析失败，重新分析")
                        return False
                    else:
                        print(f"⚠️  {brand} 品牌分析结果不完整，重新分析")
                        return False
                        
                except Exception as e:
                    print(f"⚠️  读取 {brand} 现有结果时出错: {str(e)}，重新分析")
                    return False
            
            return False
            
        except Exception as e:
            print(f"⚠️  检查 {brand} 分析状态时出错: {str(e)}，重新分析")
            return False
    
    def load_existing_analysis_results(self) -> Dict[str, Any]:
        """
        加载已存在的分析结果
        
        Returns:
            已存在的分析结果
        """
        existing_results = {
            'analysis_time': datetime.now().isoformat(),
            'total_brands': 0,
            'brand_analyses': {},
            'skipped_brands': [],
            'existing_brands': []
        }
        
        brand_analysis_dir = self.date_dir/f"brand_analysis"
        if not os.path.exists(brand_analysis_dir):
            return existing_results
        
        # 遍历品牌分析目录
        for brand_dir in os.listdir(brand_analysis_dir):
            brand_path = os.path.join(brand_analysis_dir, brand_dir)
            if os.path.isdir(brand_path):
                # 查找最新分析文件
                safe_brand_name = brand_dir.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                latest_file = os.path.join(brand_path, f"{safe_brand_name}_latest.json")
                
                if os.path.exists(latest_file):
                    try:
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            existing_result = json.load(f)
                        
                        # 检查结果是否完整
                        brand_profile = existing_result.get('brand_profile', {})
                        if isinstance(brand_profile, dict) and 'market_position' in brand_profile:
                            existing_results['brand_analyses'][brand_dir] = existing_result
                            existing_results['existing_brands'].append(brand_dir)
                            existing_results['total_brands'] += 1
                        else:
                            existing_results['skipped_brands'].append(brand_dir)
                            
                    except Exception as e:
                        print(f"⚠️  加载 {brand_dir} 现有结果时出错: {str(e)}")
                        existing_results['skipped_brands'].append(brand_dir)
        
        return existing_results
        
    def load_products_from_batch_directory(self, batch_dir: str) -> Dict[str, List[Dict]]:
        """
        从批量产品目录中加载所有品牌的产品数据
        
        Args:
            batch_dir: 批量产品目录路径
            
        Returns:
            按品牌分组的商品数据，只包含核心文本字段
        """
        print(f"📊 正在从批量产品目录加载数据: {batch_dir}")
        print("🎯 专注核心文本信息：商品标题、价格、销量、品牌等")
        
        # 查找所有产品JSON文件
        product_files = glob.glob(os.path.join(batch_dir, "*_products.json"))
        
        if not product_files:
            print(f"❌ 错误: 在目录 {batch_dir} 中找不到产品文件")
            return {}
        
        print(f"📁 找到 {len(product_files)} 个品牌产品文件")
        
        # 按品牌分组
        brand_groups = {}
        total_products = 0
        
        # 定义需要的核心字段
        required_fields = {
            'product_id': '商品ID',
            'title': '商品标题', 
            'price': '价格',
            'sales_count': '销量',
            'brand': '品牌',
            'detail_url': '详情链接'
        }
        
        for product_file in product_files:
            try:
                # 从文件名提取品牌名
                filename = os.path.basename(product_file)
                brand_name = filename.replace("_products.json", "")
                
                print(f"📖 正在加载品牌 {brand_name} 的产品数据...")
                
                with open(product_file, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                
                # 过滤和清理产品数据，只保留核心文本字段
                filtered_products = []
                for product in products:
                    filtered_product = {}
                    
                    # 只保留需要的字段
                    for field, description in required_fields.items():
                        if field in product:
                            filtered_product[field] = product[field]
                        else:
                            # 对于缺失的字段，设置默认值
                            if field == 'price':
                                filtered_product[field] = "0.00"
                            elif field == 'sales_count':
                                filtered_product[field] = "0"
                            elif field == 'brand':
                                filtered_product[field] = brand_name
                            else:
                                filtered_product[field] = ""
                    
                    filtered_products.append(filtered_product)
                
                brand_groups[brand_name] = filtered_products
                total_products += len(filtered_products)
                
                print(f"✅ {brand_name}: 加载了 {len(filtered_products)} 个产品（已过滤核心字段）")
                
            except Exception as e:
                print(f"❌ 加载品牌 {filename} 时出错: {str(e)}")
                continue
        
        print(f"✅ 成功加载 {total_products} 个商品，涵盖 {len(brand_groups)} 个品牌")
        print("📝 数据字段：商品ID、标题、价格、销量、品牌、详情链接")
        
        self.brand_data = brand_groups
        return brand_groups
    
    def load_product_data(self, json_file: str) -> Dict[str, List[Dict]]:
        """
        加载商品数据并按品牌分组（保持向后兼容）
        
        Args:
            json_file: JSON数据文件路径
            
        Returns:
            按品牌分组的商品数据
        """
        print(f"📊 正在加载商品数据: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # 按品牌分组
        brand_groups = {}
        for product in products:
            brand = product.get('brand', 'Unknown')
            if brand not in brand_groups:
                brand_groups[brand] = []
            brand_groups[brand].append(product)
        
        print(f"✅ 成功加载 {len(products)} 个商品，涵盖 {len(brand_groups)} 个品牌")
        
        self.brand_data = brand_groups
        return brand_groups
    
    def calculate_brand_statistics(self, brand: str, products: List[Dict]) -> Dict[str, Any]:
        """
        基于文本信息计算品牌统计数据 - 使用所有商品
        
        Args:
            brand: 品牌名称
            products: 商品列表
            
        Returns:
            品牌统计数据
        """
        # 使用所有商品进行分析，不进行选择
        all_products = products
        
        stats = {
            'brand_name': brand,
            'total_products': len(products),
            'analyzed_products': len(all_products),  # 分析所有商品
            'price_stats': {},
            'sales_stats': {},
            'title_analysis': {},  # 标题分析
            'product_categories': {},
            'detailed_product_samples': [],  # 所有商品样本
            'price_segments': {},  # 价格区间分析
            'sales_performance': {}  # 销售表现分析
        }
        
        # 价格统计 - 使用全部商品数据
        all_prices = []
        for p in products:
            price_str = p.get('price', '0')
            try:
                # 处理价格字符串，提取数字部分
                price = float(price_str.replace('¥', '').replace(',', '').strip())
                if price > 0:
                    all_prices.append(price)
            except (ValueError, AttributeError):
                continue
        
        if all_prices:
            stats['price_stats'] = {
                'min_price': min(all_prices),
                'max_price': max(all_prices),
                'avg_price': round(statistics.mean(all_prices), 2),
                'median_price': round(statistics.median(all_prices), 2),
                'price_range': max(all_prices) - min(all_prices),
                'has_price_count': len(all_prices),
                'price_coverage': round(len(all_prices) / len(products) * 100, 1)
            }
        
        # 销量统计
        all_sales = []
        for p in products:
            sales_str = p.get('sales_count', '0')
            try:
                # 处理销量字符串，提取数字部分
                sales = int(sales_str.replace(',', '').strip())
                if sales > 0:
                    all_sales.append(sales)
            except (ValueError, AttributeError):
                continue
        
        if all_sales:
            stats['sales_stats'] = {
                'min_sales': min(all_sales),
                'max_sales': max(all_sales),
                'avg_sales': round(statistics.mean(all_sales), 2),
                'median_sales': round(statistics.median(all_sales), 2),
                'has_sales_count': len(all_sales),
                'sales_coverage': round(len(all_sales) / len(products) * 100, 1)
            }
        
        # 标题分析 - 基于所有商品
        all_titles = [p.get('title', '') for p in products if p.get('title')]
        
        # 关键词分析
        keywords = {}
        common_words = ['新款', '时尚', '经典', '简约', '潮流', '百搭', '舒适', '官方', '正品', 
                       '男款', '女款', '情侣', '商务', '休闲', '运动', '高端', '奢华', '精致',
                       '新品', '热销', '爆款', '推荐', '精选', '限量', '特价', '促销']
        
        for word in common_words:
            count = sum(1 for title in all_titles if word in title)
            if count > 0:
                keywords[word] = {
                    'count': count,
                    'percentage': round(count / len(all_titles) * 100, 1)
                }
        
        stats['title_analysis'] = {
            'keywords': keywords,
            'sample_titles': all_titles[:20],  # 前20个标题作为样本
            'title_length_stats': {
                'avg_length': round(sum(len(t) for t in all_titles) / len(all_titles), 1) if all_titles else 0,
                'max_length': max(len(t) for t in all_titles) if all_titles else 0,
                'min_length': min(len(t) for t in all_titles) if all_titles else 0
            }
        }
        
        # 所有商品样本 - 包含核心信息
        detailed_samples = []
        for i, p in enumerate(all_products):
            sample = {
                'index': i + 1,
                'product_id': p.get('product_id', ''),
                'title': p.get('title', '')[:100],  # 缩短标题长度以节省空间
                'price': p.get('price', ''),
                'price_numeric': p.get('price_numeric', 0),
                'sales_volume': p.get('sales_volume', ''),
                'sales_numeric': p.get('sales_numeric', 0),
                'product_url': p.get('product_url', '')
            }
            detailed_samples.append(sample)
        stats['detailed_product_samples'] = detailed_samples
        
        # 价格区间分析 - 基于全部商品数据
        if all_prices:
            try:
                median_price = statistics.median(all_prices)
                price_ranges = {
                    'low': [p for p in all_prices if p < median_price * 0.7],
                    'medium': [p for p in all_prices if median_price * 0.7 <= p <= median_price * 1.3],
                    'high': [p for p in all_prices if p > median_price * 1.3]
                }
                
                stats['price_segments'] = {
                    'low_price': {
                        'count': len(price_ranges['low']),
                        'percentage': round(len(price_ranges['low']) / len(all_prices) * 100, 1),
                        'avg_price': round(statistics.mean(price_ranges['low']), 2) if price_ranges['low'] else 0
                    },
                    'medium_price': {
                        'count': len(price_ranges['medium']),
                        'percentage': round(len(price_ranges['medium']) / len(all_prices) * 100, 1),
                        'avg_price': round(statistics.mean(price_ranges['medium']), 2) if price_ranges['medium'] else 0
                    },
                    'high_price': {
                        'count': len(price_ranges['high']),
                        'percentage': round(len(price_ranges['high']) / len(all_prices) * 100, 1),
                        'avg_price': round(statistics.mean(price_ranges['high']), 2) if price_ranges['high'] else 0
                    }
                }
            except Exception as e:
                print(f"⚠️  价格区间分析出错: {str(e)}")
                stats['price_segments'] = {}
        
        # 销售表现分析
        if all_sales:
            try:
                sales_median = statistics.median(all_sales)
                hot_products = []
                cold_products = []
                
                for p in products:
                    sales_num = p.get('sales_numeric')
                    if sales_num is not None and isinstance(sales_num, (int, float)):
                        if sales_num > sales_median * 1.5:
                            hot_products.append(p)
                        elif sales_num < sales_median * 0.5:
                            cold_products.append(p)
                
                stats['sales_performance'] = {
                    'hot_products_count': len(hot_products),
                    'hot_products_percentage': round(len(hot_products) / len(products) * 100, 1),
                    'cold_products_count': len(cold_products),
                    'cold_products_percentage': round(len(cold_products) / len(products) * 100, 1),
                    'hot_product_samples': [p.get('title', '')[:80] for p in hot_products[:5]],  # 增加热销商品样本
                    'sales_median': sales_median
                }
            except Exception as e:
                print(f"⚠️  销售表现分析出错: {str(e)}")
                stats['sales_performance'] = {}
        
        return stats
    
    def generate_brand_analysis_prompt(self, brand_stats: Dict[str, Any]) -> str:
        """
        生成品牌画像分析的提示词 - 基于所有商品文本信息
        
        Args:
            brand_stats: 品牌统计数据
            
        Returns:
            分析提示词
        """
        # 提取核心信息用于分析
        price_info = brand_stats.get('price_stats', {})
        sales_info = brand_stats.get('sales_stats', {})
        title_info = brand_stats.get('title_analysis', {})
        all_products = brand_stats.get('detailed_product_samples', [])  # 所有商品
        
        # 如果商品数量过多，进行智能分组展示
        total_products = len(all_products)
        if total_products > 50:
            # 商品数量过多时，按价格段分组展示
            try:
                median_price = price_info.get('median_price', 1000)
                if median_price and isinstance(median_price, (int, float)) and median_price > 0:
                    low_price_products = [p for p in all_products if p.get('price_numeric', 0) and isinstance(p.get('price_numeric'), (int, float)) and p.get('price_numeric', 0) < median_price * 0.7]
                    medium_price_products = [p for p in all_products if p.get('price_numeric', 0) and isinstance(p.get('price_numeric'), (int, float)) and median_price * 0.7 <= p.get('price_numeric', 0) <= median_price * 1.3]
                    high_price_products = [p for p in all_products if p.get('price_numeric', 0) and isinstance(p.get('price_numeric'), (int, float)) and p.get('price_numeric', 0) > median_price * 1.3]
                else:
                    # 如果没有有效的中位数价格，按价格排序分组
                    valid_prices = [p for p in all_products if p.get('price_numeric') and isinstance(p.get('price_numeric'), (int, float)) and p.get('price_numeric', 0) > 0]
                    if valid_prices:
                        sorted_prices = sorted(valid_prices, key=lambda x: x.get('price_numeric', 0))
                        split_point = len(sorted_prices) // 3
                        low_price_products = sorted_prices[:split_point]
                        medium_price_products = sorted_prices[split_point:split_point*2]
                        high_price_products = sorted_prices[split_point*2:]
                    else:
                        low_price_products = []
                        medium_price_products = []
                        high_price_products = []
                
                # 每个价格段选择代表性商品
                sample_products = {
                    'low_price_samples': low_price_products[:10] if len(low_price_products) > 10 else low_price_products,
                    'medium_price_samples': medium_price_products[:15] if len(medium_price_products) > 15 else medium_price_products,
                    'high_price_samples': high_price_products[:10] if len(high_price_products) > 10 else high_price_products
                }
                
                products_display = f"""
## 商品数据概览（共{total_products}个商品）
- 低价商品（{len(low_price_products)}个）: {len(sample_products['low_price_samples'])}个样本
- 中价商品（{len(medium_price_products)}个）: {len(sample_products['medium_price_samples'])}个样本  
- 高价商品（{len(high_price_products)}个）: {len(sample_products['high_price_samples'])}个样本

## 各价格段商品样本
### 低价商品样本
{json.dumps(sample_products['low_price_samples'], ensure_ascii=False, indent=2)}

### 中价商品样本
{json.dumps(sample_products['medium_price_samples'], ensure_ascii=False, indent=2)}

### 高价商品样本
{json.dumps(sample_products['high_price_samples'], ensure_ascii=False, indent=2)}
"""
            except Exception as e:
                print(f"⚠️  价格分组出错: {str(e)}")
                # 如果分组失败，使用简单的前N个商品
                products_display = f"""
## 商品数据概览（共{total_products}个商品）
- 由于价格分组出错，展示前50个商品样本

## 商品样本
{json.dumps(all_products[:50], ensure_ascii=False, indent=2)}
"""
        else:
            # 商品数量适中时，展示所有商品
            products_display = f"""
## 所有商品数据（共{total_products}个）
{json.dumps(all_products, ensure_ascii=False, indent=2)}
"""
        
        prompt = f"""
请基于以下完整的商品数据，为"{brand_stats['brand_name']}"品牌生成全面准确的品牌画像。

**重要提示：这些商品都是近期上架的新品，代表了品牌最新的产品策略和市场定位。**

## 品牌基础信息
- 品牌名称: {brand_stats['brand_name']}
- 商品总数: {brand_stats['total_products']}个（全部为新品）
- 分析商品数: {brand_stats['analyzed_products']}个
- 价格范围: ¥{price_info.get('min_price', 0):.0f} - ¥{price_info.get('max_price', 0):.0f}
- 平均价格: ¥{price_info.get('avg_price', 0):.0f}
- 中位数价格: ¥{price_info.get('median_price', 0):.0f}

## 销量表现
- 平均销量: {sales_info.get('avg_sales', 0):.0f}
- 最高销量: {sales_info.get('max_sales', 0):.0f}
- 销量覆盖: {sales_info.get('sales_coverage', 0):.1f}%

## 标题关键词分析
{json.dumps(title_info.get('keywords', {}), ensure_ascii=False, indent=2)}

## 价格区间分布
{json.dumps(brand_stats.get('price_segments', {}), ensure_ascii=False, indent=2)}

## 销售表现分析
{json.dumps(brand_stats.get('sales_performance', {}), ensure_ascii=False, indent=2)}

{products_display}

请基于以上完整的商品数据（标题、价格、销量），生成全面准确的品牌画像JSON，包含以下核心内容：

```json
{{
  "brand_name": "{brand_stats['brand_name']}",
  "product_style": "产品风格特点",
  "brand_category": "品牌类别（如：瑞士手表品牌、运动鞋品牌等）",
  "price_positioning": "价格定位（如：中高端、性价比、奢华等）",
  "market_position": "市场定位（一句话概括品牌在市场中的位置）",
  "target_users": "目标用户群体（年龄、收入、生活方式等）",
  "price_strategy": "价格策略分析",
  "sales_characteristics": "销售特征分析",
  "core_features": ["核心特色1", "核心特色2", "核心特色3"],
  "buying_advice": ["最佳购买价格段", "选购要点", "避坑提醒", "新品购买注意事项"],
  "recommended_scenarios": ["推荐使用场景1", "推荐使用场景2", "推荐使用场景3"],
  "new_product_strategy": ["新品策略重点", "新品趋势方向", "创新特色", "市场反应分析"],
  "brand_keywords": ["搜索关键词1", "搜索关键词2", "搜索关键词3", "搜索关键词4", "搜索关键词5"]
}}
```

要求：
1. 基于所有{total_products}个新品的完整数据进行分析
2. 内容全面准确，避免空泛描述
3. 基于商品标题、价格、销量等文本信息进行深入分析
4. 所有内容都是中文
5. 重点突出品牌新品策略、创新特色和市场趋势
6. 适合RAG检索和购物推荐
7. 分析要深入，体现新品数据分析的优势
8. 强调这些商品都是新品，分析品牌的新品策略和市场定位
"""
        return prompt
    
    def analyze_brand_with_ai(self, brand: str, brand_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI分析品牌
        
        Args:
            brand: 品牌名称
            brand_stats: 品牌统计数据
            
        Returns:
            AI分析结果
        """
        print(f"🤖 正在使用AI分析品牌: {brand}")
        
        try:
            prompt = self.generate_brand_analysis_prompt(brand_stats)
            
            # 构建消息
            messages = [
                SystemMessage(content="你是一位专业的电商数据分析师和品牌策略专家，擅长从新品商品数据中洞察品牌的新品策略、创新特色和市场趋势。请基于所有新品的标题、价格、销量等文本信息，提供深入、专业的品牌画像分析。"),
                HumanMessage(content=prompt)
            ]
            
            # 调用豆包thinking模型
            print(f"🧠 开始thinking分析品牌: {brand}")
            print("=" * 60)
            
            # 使用流式输出来实时显示thinking过程
            if hasattr(self.client, 'stream') and self.client.streaming:
                print("💭 实时thinking过程:")
                print("-" * 40)
                
                full_response = ""
                try:
                    # 使用stream方法获取流式响应
                    for chunk in self.client.stream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            content = chunk.content
                            print(content, end='', flush=True)
                            full_response += content
                    
                    ai_response = full_response
                    print("\n" + "=" * 60)
                except Exception as e:
                    print(f"\n⚠️  流式输出出错，切换到普通模式: {str(e)}")
                    # 如果流式输出失败，回退到普通模式
                    response = self.client.invoke(messages)
                    ai_response = response.content
                    
                    # 打印thinking过程
                    print("🤔 AI分析过程:")
                    print("-" * 40)
                    
                    # 如果响应包含thinking标记，分离thinking和最终答案
                    if "<thinking>" in ai_response and "</thinking>" in ai_response:
                        # 提取thinking部分
                        thinking_start = ai_response.find("<thinking>") + len("<thinking>")
                        thinking_end = ai_response.find("</thinking>")
                        thinking_content = ai_response[thinking_start:thinking_end].strip()
                        
                        # 提取最终答案部分
                        final_answer = ai_response[thinking_end + len("</thinking>"):].strip()
                        
                        print("💭 思考过程:")
                        print(thinking_content[:2000] + "..." if len(thinking_content) > 2000 else thinking_content)
                        print("\n" + "-"*40)
                        print("📝 最终分析结果:")
                        print(final_answer[:1000] + "..." if len(final_answer) > 1000 else final_answer)
                        
                        # 使用最终答案进行后续处理
                        ai_response = final_answer
                    else:
                        print("📄 完整响应:")
                        print(ai_response[:1500] + "..." if len(ai_response) > 1500 else ai_response)
                    
                    print("=" * 60)
            else:
                response = self.client.invoke(messages)
                ai_response = response.content
                
                # 打印thinking过程
                print("🤔 AI分析过程:")
                print("-" * 40)
                
                # 如果响应包含thinking标记，分离thinking和最终答案
                if "<thinking>" in ai_response and "</thinking>" in ai_response:
                    # 提取thinking部分
                    thinking_start = ai_response.find("<thinking>") + len("<thinking>")
                    thinking_end = ai_response.find("</thinking>")
                    thinking_content = ai_response[thinking_start:thinking_end].strip()
                    
                    # 提取最终答案部分
                    final_answer = ai_response[thinking_end + len("</thinking>"):].strip()
                    
                    print("💭 思考过程:")
                    print(thinking_content[:2000] + "..." if len(thinking_content) > 2000 else thinking_content)
                    print("\n" + "-"*40)
                    print("📝 最终分析结果:")
                    print(final_answer[:1000] + "..." if len(final_answer) > 1000 else final_answer)
                    
                    # 使用最终答案进行后续处理
                    ai_response = final_answer
                else:
                    print("📄 完整响应:")
                    print(ai_response[:1500] + "..." if len(ai_response) > 1500 else ai_response)
                
                print("=" * 60)
            
            # 尝试解析JSON响应
            try:
                # 清理响应文本，移除markdown标记
                cleaned_response = ai_response.strip()
                
                # 移除可能的markdown代码块标记
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # 移除 ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # 移除 ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # 移除结尾的 ```
                
                cleaned_response = cleaned_response.strip()
                
                # 尝试找到完整的JSON结构
                json_start = cleaned_response.find('{')
                json_end = cleaned_response.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = cleaned_response[json_start:json_end+1]
                    
                    # 检查JSON是否看起来完整
                    if '"brand_name"' in json_str and '"market_position"' in json_str:
                        try:
                            analysis_result = json.loads(json_str)
                            print(f"✅ 成功解析AI分析结果JSON")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON格式有误: {str(e)}")
                            analysis_result = {
                                "raw_analysis": ai_response,
                                "parsing_note": "JSON格式错误，已保存为原始文本"
                            }
                    else:
                        print(f"⚠️  AI返回的JSON结构不完整")
                        analysis_result = {
                            "raw_analysis": ai_response,
                            "parsing_note": "AI返回的JSON不完整，已保存为原始文本"
                        }
                else:
                    analysis_result = {
                        "raw_analysis": ai_response,
                        "parsing_note": "未找到有效的JSON结构，已保存为原始文本"
                    }
                    
            except Exception as e:
                print(f"⚠️  JSON处理异常: {str(e)}")
                analysis_result = {
                    "raw_analysis": ai_response,
                    "parsing_note": f"JSON处理异常: {str(e)}，已保存为原始文本"
                }
            
            print(f"✅ {brand} 品牌分析完成")
            return analysis_result
            
        except Exception as e:
            print(f"❌ {brand} 品牌分析失败: {str(e)}")
            return {
                "error": str(e),
                "brand": brand,
                "analysis_failed": True
            }
    
    def analyze_all_brands(self) -> Dict[str, Any]:
        """
        分析所有品牌，跳过已分析的品牌
        
        Returns:
            所有品牌的分析结果
        """
        if not self.brand_data:
            raise ValueError("请先加载商品数据")
        
        print(f"🚀 开始分析 {len(self.brand_data)} 个品牌...")
        
        # 加载已存在的分析结果
        existing_results = self.load_existing_analysis_results()
        print(f"📋 发现已分析品牌: {len(existing_results['existing_brands'])} 个")
        if existing_results['skipped_brands']:
            print(f"⚠️  需要重新分析的品牌: {len(existing_results['skipped_brands'])} 个")
        
        results = {
            'analysis_time': datetime.now().isoformat(),
            'total_brands': len(self.brand_data),
            'brand_analyses': {},
            'skipped_brands': existing_results['skipped_brands'],
            'existing_brands': existing_results['existing_brands']
        }
        
        # 先添加已存在的分析结果
        results['brand_analyses'].update(existing_results['brand_analyses'])
        
        # 分析新品牌或需要重新分析的品牌
        new_brands_count = 0
        reanalyzed_brands_count = 0
        
        for brand, products in self.brand_data.items():
            # 检查是否已经分析过
            if self.check_brand_already_analyzed(brand):
                continue
            
            print(f"\n📊 分析品牌: {brand} ({len(products)} 个商品)")
            
            try:
                # 计算基础统计
                brand_stats = self.calculate_brand_statistics(brand, products)
                
                # AI分析
                ai_analysis = self.analyze_brand_with_ai(brand, brand_stats)
                
                # 合并结果
                brand_result = {
                    'brand_profile': ai_analysis,  # 品牌画像
                    'summary_stats': {  # 关键统计信息
                        'total_products': brand_stats['total_products'],
                        'analyzed_products': brand_stats.get('analyzed_products', 0),
                        'price_range': {
                            'min': brand_stats.get('price_stats', {}).get('min_price', 0),
                            'max': brand_stats.get('price_stats', {}).get('max_price', 0),
                            'avg': brand_stats.get('price_stats', {}).get('avg_price', 0)
                        },
                        'sales_performance': {
                            'avg_sales': brand_stats.get('sales_stats', {}).get('avg_sales', 0),
                            'max_sales': brand_stats.get('sales_stats', {}).get('max_sales', 0)
                        }
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                results['brand_analyses'][brand] = brand_result
                
                # 立即保存单个品牌结果到独立文件
                self.save_single_brand_result(brand, brand_result)
                
                # 统计新分析或重新分析的品牌
                if brand in existing_results['skipped_brands']:
                    reanalyzed_brands_count += 1
                    print(f"✅ {brand} 品牌重新分析完成")
                else:
                    new_brands_count += 1
                    print(f"✅ {brand} 品牌新分析完成")
                
            except Exception as e:
                print(f"❌ {brand} 品牌分析失败: {str(e)}")
                # 记录错误信息，但不中断整个流程
                error_result = {
                    'brand_profile': {
                        "error": str(e),
                        "brand": brand,
                        "analysis_failed": True
                    },
                    'summary_stats': {
                        'total_products': len(products),
                        'analyzed_products': 0,
                        'error_note': f"分析失败: {str(e)}"
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                results['brand_analyses'][brand] = error_result
                
                # 即使分析失败也保存错误结果
                self.save_single_brand_result(brand, error_result)
            
            # 避免API限流
            time.sleep(1)
        
        # 打印分析统计
        total_analyzed = len(results['brand_analyses'])
        print(f"\n📊 分析完成统计:")
        print(f"   - 总品牌数: {len(self.brand_data)}")
        print(f"   - 已存在结果: {len(existing_results['existing_brands'])}")
        print(f"   - 新分析品牌: {new_brands_count}")
        print(f"   - 重新分析品牌: {reanalyzed_brands_count}")
        print(f"   - 本次实际分析: {new_brands_count + reanalyzed_brands_count}")
        print(f"   - 最终结果总数: {total_analyzed}")
        
        self.analysis_results = results
        return results
    
    def save_single_brand_result(self, brand: str, brand_result: Dict[str, Any]) -> None:
        """
        保存单个品牌的分析结果到独立文件
        
        Args:
            brand: 品牌名称
            brand_result: 品牌分析结果
        """
        try:
            # 创建品牌专属输出目录，放在指定日期目录下
            brand_output_dir = self.date_dir/f"brand_analysis/{brand}"
            os.makedirs(brand_output_dir, exist_ok=True)
            
            # 生成品牌专属文件名（只保存最新版本，不带时间戳）
            safe_brand_name = brand.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            latest_file = f"{brand_output_dir}/{safe_brand_name}_latest.json"
            
            # 保存品牌分析结果（只保存最新版本）
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(brand_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 {brand} 品牌结果已保存到: {latest_file}")
            
        except Exception as e:
            print(f"⚠️  保存 {brand} 品牌结果失败: {str(e)}")
    
    def save_analysis_results(self, output_file: str = None) -> str:
        """
        保存分析结果
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        if not self.analysis_results:
            raise ValueError("没有分析结果可保存")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"brand_analysis_report_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 分析结果已保存到: {output_file}")
        return output_file
    
    def generate_summary_report(self) -> str:
        """
        生成摘要报告
        
        Returns:
            摘要报告文本
        """
        if not self.analysis_results:
            return "没有分析结果可生成报告"
        
        report = []
        report.append("=" * 60)
        report.append("🏆 品牌新品画像分析报告")
        report.append("=" * 60)
        report.append(f"📅 分析时间: {self.analysis_results['analysis_time']}")
        report.append(f"📊 分析品牌数: {self.analysis_results['total_brands']}")
        report.append("🎯 分析重点: 基于所有新品商品数据")
        report.append("")
        
        for brand, data in self.analysis_results['brand_analyses'].items():
            summary_stats = data.get('summary_stats', {})
            brand_profile = data.get('brand_profile', {})
            
            report.append(f"🏷️  品牌: {brand}")
            report.append(f"   商品数量: {summary_stats.get('total_products', 0)}个")
            report.append(f"   分析商品: {summary_stats.get('analyzed_products', 0)}个")
            
            price_range = summary_stats.get('price_range', {})
            if price_range.get('min', 0) > 0:
                report.append(f"   价格区间: ¥{price_range['min']:.0f} - ¥{price_range['max']:.0f}")
                report.append(f"   平均价格: ¥{price_range['avg']:.0f}")
            
            sales_perf = summary_stats.get('sales_performance', {})
            if sales_perf.get('avg_sales', 0) > 0:
                report.append(f"   平均销量: {sales_perf['avg_sales']:.0f}")
            
            # 显示品牌画像核心信息
            if isinstance(brand_profile, dict) and 'market_position' in brand_profile:
                report.append(f"   市场定位: {brand_profile.get('market_position', '未知')}")
                report.append(f"   价格定位: {brand_profile.get('price_positioning', '未知')}")
                if brand_profile.get('core_features'):
                    features = brand_profile['core_features'][:2]  # 只显示前2个特色
                    report.append(f"   核心特色: {', '.join(features)}")
            elif 'error' in brand_profile:
                report.append(f"   状态: ❌ 分析失败 - {brand_profile.get('error', '未知错误')}")
            elif 'raw_analysis' in brand_profile:
                report.append(f"   状态: 分析完成，格式待优化")
            else:
                report.append(f"   状态: 分析中...")
            
            report.append("")
        
        return "\n".join(report)
    
    def generate_brand_profile_stats(self) -> str:
        """
        生成品牌画像统计信息
        
        Returns:
            统计报告文本
        """
        if not self.analysis_results:
            return "没有分析结果可生成统计"
        
        stats = []
        stats.append("=" * 60)
        stats.append("🎨 品牌新品画像分析统计报告")
        stats.append("=" * 60)
        
        total_brands = len(self.analysis_results.get('brand_analyses', {}))
        completed_profiles = 0
        failed_profiles = 0
        total_analyzed_products = 0
        
        for brand, data in self.analysis_results.get('brand_analyses', {}).items():
            summary_stats = data.get('summary_stats', {})
            brand_profile = data.get('brand_profile', {})
            
            # 统计分析商品数量
            analyzed_products = summary_stats.get('analyzed_products', 0)
            total_analyzed_products += analyzed_products
            
            # 检查是否有完整的品牌画像
            if isinstance(brand_profile, dict) and 'market_position' in brand_profile:
                completed_profiles += 1
                stats.append(f"✅ {brand}: {analyzed_products} 个新品")
            elif 'error' in brand_profile:
                failed_profiles += 1
                stats.append(f"❌ {brand}: 分析失败 - {brand_profile.get('error', '未知错误')}")
            else:
                stats.append(f"⏳ {brand}: 分析中或格式待优化")
        
        stats.append("")
        stats.append(f"📊 总计:")
        stats.append(f"   - 品牌总数: {total_brands}")
        stats.append(f"   - 品牌画像完成: {completed_profiles}/{total_brands}")
        stats.append(f"   - 分析失败: {failed_profiles}/{total_brands}")
        stats.append(f"   - 分析新品总数: {total_analyzed_products}")
        stats.append(f"   - 平均每品牌新品数: {total_analyzed_products/total_brands:.1f}")
        
        coverage_rate = completed_profiles / total_brands * 100 if total_brands > 0 else 0
        stats.append(f"   - 品牌画像完成率: {coverage_rate:.1f}%")
        
        stats.append("")
        stats.append("🎯 品牌新品画像特点:")
        stats.append("   - 📝 基于所有新品的标题、价格、销量等文本信息")
        stats.append("   - 🆕 全量新品数据分析，核心关键词和特色提取")
        stats.append("   - 🛒 直接的购买建议和避坑指南")
        stats.append("   - 📊 基于完整新品数据的深度分析")
        stats.append("   - 🔍 适合RAG检索和购物推荐")
        stats.append("   - 🚀 突出新品策略、创新特色和市场趋势")
        
        return "\n".join(stats)
    
    def generate_brand_directory_index(self, results: Dict[str, Any]) -> str:
        """
        生成品牌目录索引文件
        
        Args:
            results: 分析结果
            
        Returns:
            索引文件内容
        """
        index_content = []
        index_content.append("品牌新品画像分析目录索引")
        index_content.append("=" * 50)
        index_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        index_content.append(f"总品牌数: {len(results.get('brand_analyses', {}))}")
        index_content.append("")
        
        # 按品牌名称排序
        sorted_brands = sorted(results.get('brand_analyses', {}).keys())
        
        for brand in sorted_brands:
            data = results['brand_analyses'][brand]
            brand_profile = data.get('brand_profile', {})
            summary_stats = data.get('summary_stats', {})
            
            index_content.append(f"🏷️  {brand}")
            index_content.append(f"   商品数量: {summary_stats.get('total_products', 0)} 个新品")
            
            if 'error' in brand_profile:
                index_content.append(f"   状态: ❌ 分析失败")
                index_content.append(f"   错误: {brand_profile.get('error', '未知错误')}")
            else:
                index_content.append(f"   状态: ✅ 分析成功")
                if isinstance(brand_profile, dict) and 'market_position' in brand_profile:
                    index_content.append(f"   市场定位: {brand_profile.get('market_position', '未知')}")
                    index_content.append(f"   价格定位: {brand_profile.get('price_positioning', '未知')}")
            
            # 文件路径信息
            safe_brand_name = brand.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            index_content.append(f"   文件: brand_analysis_without_image/{brand}/{safe_brand_name}_latest.json")
            index_content.append("")
        
        return "\n".join(index_content)


def main(date_dir: str,output_dir: str,force_reanalyze: bool=False):
    """主函数 - 基于所有新品商品文本信息生成品牌画像"""
    date_dir =pathlib.Path(date_dir)
    output_dir = pathlib.Path(output_dir)

    
    try:
        # 初始化分析器，传递日期参数和强制重新分析选项
        analyzer = BrandAnalyzer(date_dir=date_dir, force_reanalyze=force_reanalyze)
        
        # 使用批量产品目录
        batch_dir = date_dir/f"extracted_products_batch"
        if not os.path.exists(batch_dir):
            print(f"❌ 错误: 找不到批量产品目录 {batch_dir}")
            print("   请确保目录存在且包含品牌产品文件")
            return
        
        # 从批量目录加载所有品牌的产品数据
        brand_data = analyzer.load_products_from_batch_directory(batch_dir)
        
        if not brand_data:
            print("❌ 错误: 无法加载任何品牌数据")
            return
        
        # 分析所有品牌
        results = analyzer.analyze_all_brands()
        
        # 保存结果到指定目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建主输出目录
        main_output_dir = output_dir
        os.makedirs(main_output_dir, exist_ok=True)
        
        # 保存完整分析结果
        output_file = f"{main_output_dir}/all_brands_analysis_{timestamp}.json"
        analyzer.save_analysis_results(output_file)
        
        # 生成品牌分析总结报告
        summary_file = f"{main_output_dir}/brand_analysis_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("品牌新品画像分析总结报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"分析时间: {timestamp}\n")
            f.write(f"总品牌数: {len(results.get('brand_analyses', {}))}\n\n")
            
            # 统计成功和失败的品牌
            success_count = 0
            failed_count = 0
            for brand, data in results.get('brand_analyses', {}).items():
                brand_profile = data.get('brand_profile', {})
                if 'error' in brand_profile:
                    failed_count += 1
                    f.write(f"❌ {brand}: 分析失败\n")
                else:
                    success_count += 1
                    f.write(f"✅ {brand}: 分析成功\n")
            
            f.write(f"\n总结: 成功 {success_count} 个品牌，失败 {failed_count} 个品牌\n")
            f.write(f"成功率: {success_count/(success_count+failed_count)*100:.1f}%\n")
        
        print(f"📋 分析总结已保存到: {summary_file}")
        
        # 生成摘要报告
        summary = analyzer.generate_summary_report()
        print("\n" + summary)
        
        # 保存摘要报告
        summary_file = f"{main_output_dir}/brand_analysis_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"📋 摘要报告已保存到: {summary_file}")
        
        # 生成品牌画像统计
        profile_stats = analyzer.generate_brand_profile_stats()
        print("\n" + profile_stats)
        
        # 保存统计报告
        stats_file = f"{main_output_dir}/brand_profile_stats_{timestamp}.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(profile_stats)
        print(f"📊 统计报告已保存到: {stats_file}")
        
        # 生成品牌目录索引
        index_content = analyzer.generate_brand_directory_index(results)
        index_file = f"{main_output_dir}/brand_analysis_index_{timestamp}.txt"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"📁 品牌目录索引已保存到: {index_file}")
        
        print("\n🎉 品牌新品画像分析完成！")
        print("📝 基于所有新品的标题、价格、销量等文本信息")
        print("🎨 全量新品数据分析，输出格式简洁实用，适合RAG检索")
        print("🛍️ 专注新品策略、创新特色和市场趋势分析")
        print(f"📁 每个品牌结果已单独保存到: {main_output_dir}/")
        print(f"📋 完整分析结果: {output_file}")
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main(
        date_dir=fr"data/{place_id}/{monthly_type}/",
        output_dir=fr"data/{place_id}/{monthly_type}//brand_analysis_without_image",
    )
