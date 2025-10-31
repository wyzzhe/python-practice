#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从分析结果 JSON 文件中提取推荐商品信息并生成 VR 链接
"""

import os
import json
import argparse
from typing import List, Dict, Optional

# 导入店铺视图字典
from store_view_dict import store_view_dict

# ==================== 配置项 ====================
DEFAULT_ANALYSIS_DIR = os.path.join(
    os.path.dirname(__file__),
    'analysis_results'
)

DEFAULT_OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    'recommended_views/recommended_products.json'
)


def load_analysis_results(analysis_dir: str) -> List[Dict]:
    """
    加载所有分析结果 JSON 文件
    
    Args:
        analysis_dir: 分析结果目录
    
    Returns:
        所有品牌的分析结果列表
    """
    results = []
    
    if not os.path.isdir(analysis_dir):
        print(f'[ERROR] 目录不存在: {analysis_dir}')
        return results
    
    for filename in os.listdir(analysis_dir):
        if not filename.endswith('_analysis.json'):
            continue
        
        file_path = os.path.join(analysis_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append(data)
                print(f'[INFO] 已加载: {filename} (品牌: {data.get("brand", "未知")})')
        except Exception as e:
            print(f'[ERROR] 读取文件失败 {filename}: {e}')
    
    return results


def extract_recommended_products(results: List[Dict]) -> List[Dict]:
    """
    提取所有推荐商品信息
    
    Args:
        results: 所有品牌的分析结果
    
    Returns:
        推荐商品列表，每个商品包含：
        - brand: 品牌名称
        - name: 商品名称
        - location: 商品位置
        - view_direction: 视图方向
        - panorama_id: VR 点位 ID
        - position_3d: 3D 坐标 {x, y, z}
        - vr_link: 生成的 VR 链接
    """
    recommended_products = []
    
    for brand_result in results:
        brand_name = brand_result.get('brand', '')
        product_results = brand_result.get('product_results', [])
        
        # 获取品牌的 store_view_id
        store_view_id = store_view_dict.get(brand_name)
        if not store_view_id:
            print(f'[WARN] 品牌 {brand_name} 在 store_view_dict 中未找到对应的 view_id，跳过')
            continue
        
        for point_result in product_results:
            panorama_id = point_result.get('panorama_id')
            products = point_result.get('products', [])
            
            for product in products:
                # 只提取推荐商品
                if not product.get('is_recommended', False):
                    continue
                
                # 检查是否有 position_3d
                position_3d = product.get('position_3d')
                if not position_3d:
                    print(f'[WARN] 商品 {product.get("name")} (品牌: {brand_name}, 点位: {panorama_id}) 没有 position_3d，跳过')
                    continue
                
                # 提取商品信息
                product_info = {
                    'brand': brand_name,
                    'name': product.get('name', ''),
                    'location': product.get('location', ''),
                    'view_direction': product.get('view_direction', ''),
                    'panorama_id': panorama_id,
                    'position_3d': position_3d.copy(),
                    'vr_link': None
                }
                
                # 生成 VR 链接
                x = position_3d.get('x', 0)
                y = position_3d.get('y', 0)
                z = position_3d.get('z', 0)
                
                vr_link = (
                    f'https://vr.aibee.cn/store/{store_view_id}?'
                    f'pid={panorama_id}&'
                    f'dirx={x}&'
                    f'diry={y}&'
                    f'dirz={z}'
                )
                
                product_info['vr_link'] = vr_link
                recommended_products.append(product_info)
    
    return recommended_products


def save_results(products: List[Dict], output_file: str, format: str = 'json'):
    """
    保存结果到文件
    
    Args:
        products: 推荐商品列表
        output_file: 输出文件路径
        format: 输出格式 ('json' 或 'csv')
    """
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    if format == 'json':
        # 保存为 JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f'\n[INFO] 结果已保存为 JSON: {output_file}')
    
    elif format == 'csv':
        # 保存为 CSV
        import csv
        
        csv_file = output_file.replace('.json', '.csv')
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'brand', 'name', 'location', 'view_direction', 
                'panorama_id', 'x', 'y', 'z', 'vr_link'
            ])
            writer.writeheader()
            
            for product in products:
                pos = product['position_3d']
                writer.writerow({
                    'brand': product['brand'],
                    'name': product['name'],
                    'location': product['location'],
                    'view_direction': product['view_direction'],
                    'panorama_id': product['panorama_id'],
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'vr_link': product['vr_link']
                })
        
        print(f'\n[INFO] 结果已保存为 CSV: {csv_file}')
    
    else:
        print(f'[ERROR] 不支持的格式: {format}')


def print_summary(products: List[Dict]):
    """打印统计信息"""
    print('\n' + '='*60)
    print('统计信息:')
    print(f'  总推荐商品数: {len(products)}')
    
    # 按品牌统计
    brand_count = {}
    for product in products:
        brand = product['brand']
        brand_count[brand] = brand_count.get(brand, 0) + 1
    
    print(f'\n  按品牌分布:')
    for brand, count in sorted(brand_count.items(), key=lambda x: x[1], reverse=True):
        print(f'    {brand}: {count} 个商品')
    
    print('='*60)


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        description='从分析结果中提取推荐商品并生成 VR 链接'
    )
    parser.add_argument(
        '--analysis_dir',
        type=str,
        default=DEFAULT_ANALYSIS_DIR,
        help='分析结果目录路径'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_FILE,
        help='输出文件路径'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'csv', 'both'],
        default='both',
        help='输出格式：json、csv 或 both（默认 both）'
    )
    
    args = parser.parse_args()
    
    print('[INFO] 开始提取推荐商品信息...')
    print(f'[INFO] 分析结果目录: {args.analysis_dir}')
    print(f'[INFO] 输出文件: {args.output}')
    print(f'[INFO] 输出格式: {args.format}\n')
    
    # 加载所有分析结果
    results = load_analysis_results(args.analysis_dir)
    
    if not results:
        print('[ERROR] 未找到任何分析结果文件')
        return
    
    print(f'\n[INFO] 共加载 {len(results)} 个品牌的分析结果\n')
    
    # 提取推荐商品
    recommended_products = extract_recommended_products(results)
    
    # 打印统计信息
    print_summary(recommended_products)
    
    # 保存结果
    if args.format in ['json', 'both']:
        save_results(recommended_products, args.output, 'json')
    
    if args.format in ['csv', 'both']:
        save_results(recommended_products, args.output, 'csv')
    
    # 显示前几个示例
    if recommended_products:
        print('\n前 5 个商品示例:')
        for i, product in enumerate(recommended_products[:5], 1):
            print(f'\n{i}. {product["brand"]} - {product["name"]}')
            print(f'   位置: {product["location"]}')
            print(f'   视图方向: {product["view_direction"]}')
            print(f'   点位 ID: {product["panorama_id"]}')
            print(f'   3D 坐标: ({product["position_3d"]["x"]}, {product["position_3d"]["y"]}, {product["position_3d"]["z"]})')
            print(f'   VR 链接: {product["vr_link"]}')


if __name__ == '__main__':
    main()

