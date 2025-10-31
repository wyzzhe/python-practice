#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理分析结果，生成商品分析和店铺分析文档
"""

import os
import json
import argparse
import re
from typing import List, Dict, Optional
from collections import defaultdict

# ==================== 配置项 ====================
DEFAULT_ANALYSIS_DIR = os.path.join(
    os.path.dirname(__file__),
    'analysis_results'
)

DEFAULT_RECOMMENDED_FILE = os.path.join(
    os.path.dirname(__file__),
    'recommended_views/recommended_products.json'
)

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    'output_docs'
)

DEFAULT_BRAND_LIST_FILE = os.path.join(
    os.path.dirname(__file__),
    'brand_list.py'
)


def load_brand_categories(brand_list_file: str = None) -> Dict[str, str]:
    """
    从 brand_list.py 解析品牌分类信息
    
    Returns:
        {brand_name: category_name}
    """
    if brand_list_file is None:
        brand_list_file = DEFAULT_BRAND_LIST_FILE
    
    brand_category_map = {}
    
    if not os.path.exists(brand_list_file):
        print(f'[WARN] 品牌列表文件不存在: {brand_list_file}')
        return brand_category_map
    
    try:
        with open(brand_list_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式解析分类和品牌
        # 匹配格式: # 分类类\n    "品牌1", "品牌2",
        pattern = r'#\s*([^\n#]+类)\s*\n\s*((?:"[^"]+",?\s*)+)'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        for category, brands_str in matches:
            category = category.strip()
            # 提取品牌名称（去除引号和逗号）
            brand_names = re.findall(r'"([^"]+)"', brands_str)
            for brand in brand_names:
                brand_category_map[brand] = category
        
        print(f'[INFO] 已加载 {len(brand_category_map)} 个品牌的分类信息')
    except Exception as ex:
        print(f'[ERROR] 解析品牌列表文件失败: {ex}')
    
    return brand_category_map


def load_recommended_products(recommended_file: str) -> Dict[str, List[Dict]]:
    """
    加载推荐商品信息，按 (brand, panorama_id, name) 建立索引
    
    Returns:
        {(brand, panorama_id, name): vr_link}
    """
    vr_links = {}
    
    if not os.path.exists(recommended_file):
        print(f'[WARN] 推荐商品文件不存在: {recommended_file}')
        return vr_links
    
    try:
        with open(recommended_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            key = (
                product.get('brand', ''),
                product.get('panorama_id', 0),
                product.get('name', '')
            )
            vr_links[key] = product.get('vr_link', '')
        
        print(f'[INFO] 已加载 {len(vr_links)} 个推荐商品的 VR 链接')
    except Exception as e:
        print(f'[ERROR] 加载推荐商品文件失败: {e}')
    
    return vr_links


def load_analysis_results(analysis_dir: str) -> List[Dict]:
    """加载所有分析结果"""
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
        except Exception as e:
            print(f'[ERROR] 读取文件失败 {filename}: {e}')
    
    return results


def get_image_display_path(image_path: str, relative_to: str = None) -> str:
    """
    转换图片路径，如果图片文件存在，返回相对路径；否则返回原路径
    
    Args:
        image_path: 图片绝对路径
        relative_to: 相对路径的基准目录
    """
    if os.path.exists(image_path):
        if relative_to:
            try:
                rel_path = os.path.relpath(image_path, relative_to)
                return rel_path.replace('\\', '/')  # 统一使用 / 分隔符
            except Exception:
                pass
        return image_path.replace('\\', '/')
    return image_path.replace('\\', '/')


def format_product_info(product: Dict, vr_link: Optional[str] = None) -> str:
    """格式化商品信息为 Markdown"""
    lines = []
    
    # 商品名称（推荐商品加标记）
    name = product.get('name', '')
    is_recommended = product.get('is_recommended', False)
    if is_recommended:
        name = f"**{name}** ⭐ (推荐)"
    lines.append(f"- **名称**: {name}")
    
    # 其他信息
    if product.get('type'):
        lines.append(f"  - **类型**: {product['type']}")
    
    if product.get('colors'):
        colors = '、'.join(product['colors'])
        lines.append(f"  - **颜色**: {colors}")
    
    if product.get('materials'):
        materials = '、'.join(product['materials'])
        lines.append(f"  - **材质**: {materials}")
    
    if product.get('location'):
        lines.append(f"  - **位置**: {product['location']}")
    
    if product.get('view_direction'):
        direction_map = {'f': '前', 'b': '后', 'l': '左', 'r': '右'}
        direction = direction_map.get(product['view_direction'], product['view_direction'])
        lines.append(f"  - **视图方向**: {direction}")
    
    if product.get('position_3d'):
        pos = product['position_3d']
        if pos and isinstance(pos, dict):
            lines.append(f"  - **3D坐标**: ({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)})")
    
    # VR 链接（仅推荐商品）
    if vr_link:
        lines.append(f"  - **VR链接**: [{vr_link}]({vr_link})")
    elif is_recommended:
        lines.append("  - **VR链接**: 未找到")
    
    return '\n'.join(lines)


def generate_product_section(results: List[Dict], vr_links: Dict, brand_category_map: Dict[str, str]) -> str:
    """生成商品分析部分"""
    lines = []
    lines.append('# 第一部分：商品分析\n')
    lines.append('本部分按店铺和点位展示所有检测到的商品信息。推荐商品已标记 ⭐ 并包含 VR 链接。\n')
    
    # 按分类分组品牌
    category_brands = defaultdict(list)
    for brand_result in results:
        brand_name = brand_result.get('brand', '')
        category = brand_category_map.get(brand_name, '未分类')
        category_brands[category].append(brand_result)
    
    # 按分类遍历
    for category in sorted(category_brands.keys()):
        lines.append(f'\n## {category}\n')
        
        brand_results = sorted(category_brands[category], key=lambda x: x.get('brand', ''))
        
        for brand_result in brand_results:
            brand_name = brand_result.get('brand', '')
            product_results = brand_result.get('product_results', [])
            
            if not product_results:
                continue
            
            lines.append(f'\n### {brand_name}\n')
            
            for point_result in product_results:
                panorama_id = point_result.get('panorama_id', '')
                seq_id = point_result.get('seq_id', '')
                images = point_result.get('images', [])
                products = point_result.get('products', [])
                
                if not products:
                    continue
                
                # 表头（添加分类列）
                lines.append(f'\n#### 点位 {panorama_id} (序号: {seq_id})\n')
                lines.append('| 店铺分类 | 店铺名称 | 店铺点位 | 点位图片 | 商品信息 |')
                lines.append('|---------|---------|---------|---------|---------|')
                
                # 准备图片链接（四个视角）
                image_links = []
                for img_path in sorted(images):
                    rel_path = get_image_display_path(img_path)
                    # 判断方向
                    direction_map = {'_f.jpg': '前', '_b.jpg': '后', '_l.jpg': '左', '_r.jpg': '右'}
                    direction = '未知'
                    for key, value in direction_map.items():
                        if img_path.endswith(key):
                            direction = value
                            break
                    image_links.append(f"[{direction}]({rel_path})")
                
                images_cell = '<br>'.join(image_links) if image_links else '无图片'
                
                # 准备商品信息
                products_info = []
                for product in products:
                    # 获取 VR 链接
                    vr_link = None
                    if product.get('is_recommended', False):
                        key = (brand_name, panorama_id, product.get('name', ''))
                        vr_link = vr_links.get(key)
                    
                    product_text = format_product_info(product, vr_link)
                    products_info.append(product_text)
                
                products_cell = '<br><br>'.join(products_info) if products_info else '无商品'
                
                # 输出表格行（添加分类）
                category = brand_category_map.get(brand_name, '未分类')
                lines.append(f'| {category} | {brand_name} | {panorama_id} | {images_cell} | {products_cell} |')
    
    return '\n'.join(lines)


def generate_store_section(results: List[Dict], brand_category_map: Dict[str, str]) -> str:
    """生成店铺分析部分"""
    lines = []
    lines.append('\n\n# 第二部分：店铺分析\n')
    lines.append('本部分展示各店铺的整体环境分析信息。\n')
    
    # 按分类分组品牌
    category_brands = defaultdict(list)
    for brand_result in results:
        brand_name = brand_result.get('brand', '')
        category = brand_category_map.get(brand_name, '未分类')
        category_brands[category].append(brand_result)
    
    # 按分类遍历
    for category in sorted(category_brands.keys()):
        lines.append(f'\n## {category}\n')
        
        brand_results = sorted(category_brands[category], key=lambda x: x.get('brand', ''))
        
        for brand_result in brand_results:
            brand_name = brand_result.get('brand', '')
            store_analysis = brand_result.get('store_analysis', {})
            product_results = brand_result.get('product_results', [])
            
            if not store_analysis:
                continue
            
            lines.append(f'\n### {brand_name}\n')
            
            # 收集所有点位图片
            all_point_images = {}
            for point_result in product_results:
                panorama_id = point_result.get('panorama_id', '')
                seq_id = point_result.get('seq_id', '')
                images = point_result.get('images', [])
                if images:
                    all_point_images[panorama_id] = {
                        'seq_id': seq_id,
                        'images': images
                    }
            
            # 为每个有图片的点位生成一行
            if all_point_images:
                lines.append('\n#### 店铺点位信息\n')
                lines.append('| 店铺分类 | 店铺名称 | 店铺点位 | 点位图片 | 店铺信息 |')
                lines.append('|---------|---------|---------|---------|---------|')
            
            for panorama_id in sorted(all_point_images.keys()):
                point_data = all_point_images[panorama_id]
                images = point_data['images']
                
                # 准备图片链接
                image_links = []
                for img_path in sorted(images):
                    rel_path = get_image_display_path(img_path)
                    direction_map = {'_f.jpg': '前', '_b.jpg': '后', '_l.jpg': '左', '_r.jpg': '右'}
                    direction = '未知'
                    for key, value in direction_map.items():
                        if img_path.endswith(key):
                            direction = value
                            break
                    image_links.append(f"[{direction}]({rel_path})")
                
                images_cell = '<br>'.join(image_links) if image_links else '无图片'
                
                # 准备店铺信息（第一行显示完整信息，其他行显示 "-"）
                store_info_lines = []
                if panorama_id == sorted(all_point_images.keys())[0]:
                    # 店铺基本信息
                    if store_analysis.get('store_category'):
                        store_info_lines.append(f"**店铺类别**: {store_analysis['store_category']}")
                    
                    if store_analysis.get('price_positioning'):
                        store_info_lines.append(f"**价格定位**: {store_analysis['price_positioning']}")
                    
                    if store_analysis.get('target_customers'):
                        customers = '、'.join(store_analysis['target_customers'])
                        store_info_lines.append(f"**目标客户**: {customers}")
                    
                    # 店铺环境
                    store_env = store_analysis.get('store_env', {})
                    if store_env:
                        if store_env.get('style'):
                            styles = '、'.join(store_env['style']) if isinstance(store_env['style'], list) else store_env['style']
                            store_info_lines.append(f"**风格**: {styles}")
                        
                        if store_env.get('lighting'):
                            store_info_lines.append(f"**照明**: {store_env['lighting']}")
                        
                        if store_env.get('spatial_layout'):
                            store_info_lines.append(f"**空间布局**: {store_env['spatial_layout']}")
                        
                        if store_env.get('overall_feeling'):
                            store_info_lines.append(f"**整体感觉**: {store_env['overall_feeling']}")
                        
                        if store_env.get('display_method'):
                            methods = store_env['display_method']
                            if isinstance(methods, list):
                                methods_text = '<br>'.join([f"  - {m}" for m in methods])
                            else:
                                methods_text = str(methods)
                            store_info_lines.append(f"**陈列方式**:<br>{methods_text}")
                    
                    # 购物体验
                    shopping_exp = store_analysis.get('store_env', {}).get('shopping_experience', {})
                    if shopping_exp:
                        if shopping_exp.get('has_try_on_area') is not None:
                            store_info_lines.append(f"**有试穿区**: {'是' if shopping_exp['has_try_on_area'] else '否'}")
                        
                        if shopping_exp.get('has_photo_spots') is not None:
                            store_info_lines.append(f"**有拍照点**: {'是' if shopping_exp['has_photo_spots'] else '否'}")
                
                store_info_cell = '<br>'.join(store_info_lines) if store_info_lines else '-'
                
                # 输出表格行（添加分类）
                category = brand_category_map.get(brand_name, '未分类')
                lines.append(f'| {category} | {brand_name} | {panorama_id} | {images_cell} | {store_info_cell} |')
        else:
            # 如果没有点位图片，只显示店铺信息
            lines.append('\n#### 店铺整体信息\n')
            lines.append('| 店铺分类 | 店铺名称 | 店铺点位 | 点位图片 | 店铺信息 |')
            lines.append('|---------|---------|---------|---------|---------|')
            
            store_info_lines = []
            if store_analysis.get('store_category'):
                store_info_lines.append(f"**店铺类别**: {store_analysis['store_category']}")
            # ... 其他信息（同上）
            
            store_info_cell = '<br>'.join(store_info_lines) if store_info_lines else '无信息'
            category = brand_category_map.get(brand_name, '未分类')
            lines.append(f'| {category} | {brand_name} | - | - | {store_info_cell} |')
    
    return '\n'.join(lines)


def generate_markdown_document(results: List[Dict], vr_links: Dict, brand_category_map: Dict[str, str], output_file: str):
    """生成 Markdown 文档"""
    lines = []
    
    # 标题和说明
    lines.append('# 店铺商品分析报告\n')
    lines.append('本报告包含两部分内容：')
    lines.append('1. **商品分析**: 按店铺和点位展示所有检测到的商品信息')
    lines.append('2. **店铺分析**: 展示各店铺的整体环境分析信息\n')
    
    # 第一部分：商品分析
    lines.append(generate_product_section(results, vr_links, brand_category_map))
    
    # 第二部分：店铺分析
    lines.append(generate_store_section(results, brand_category_map))
    
    # 保存文件
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f'\n[INFO] Markdown 文档已保存: {output_file}')


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        description='整理分析结果，生成商品分析和店铺分析文档'
    )
    parser.add_argument(
        '--analysis_dir',
        type=str,
        default=DEFAULT_ANALYSIS_DIR,
        help='分析结果目录路径'
    )
    parser.add_argument(
        '--recommended_file',
        type=str,
        default=DEFAULT_RECOMMENDED_FILE,
        help='推荐商品 JSON 文件路径'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help='输出文档目录'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'html'],
        default='markdown',
        help='输出格式（默认 markdown）'
    )
    
    args = parser.parse_args()
    
    print('[INFO] 开始整理分析结果...')
    print(f'[INFO] 分析结果目录: {args.analysis_dir}')
    print(f'[INFO] 推荐商品文件: {args.recommended_file}')
    print(f'[INFO] 输出目录: {args.output_dir}')
    print(f'[INFO] 输出格式: {args.format}\n')
    
    # 加载数据
    print('[INFO] 加载数据...')
    brand_category_map = load_brand_categories()
    vr_links = load_recommended_products(args.recommended_file)
    results = load_analysis_results(args.analysis_dir)
    
    if not results:
        print('[ERROR] 未找到任何分析结果文件')
        return
    
    print(f'[INFO] 共加载 {len(results)} 个品牌的分析结果\n')
    
    # 生成文档
    output_file = os.path.join(args.output_dir, 'analysis_report.md')
    
    if args.format == 'markdown':
        generate_markdown_document(results, vr_links, brand_category_map, output_file)
    elif args.format == 'html':
        # TODO: 可以实现 HTML 格式输出
        print('[INFO] HTML 格式暂未实现，输出 Markdown 格式')
        generate_markdown_document(results, vr_links, brand_category_map, output_file)
    
    print('\n[INFO] 文档生成完成！')


if __name__ == '__main__':
    main()

