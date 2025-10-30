#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用豆包 Doubao-Seed-1.6-vision 模型分析 panorama_json 文件夹中的全景图片
支持通过 --brand_list 参数筛选需要处理的品牌
"""

import os
import sys
import json
import base64
import argparse
import math
from typing import List, Dict, Optional
import requests
from tqdm import tqdm

# 导入提示词
from prompt import vr_pic_prompt


# ==================== 配置项 ====================
DEFAULT_PANORAMA_DIR = os.path.join(
    os.path.dirname(__file__), 
    'panorama_json'
)

# 豆包 API 配置（需要配置环境变量）
DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
DOUBAO_ENDPOINT = os.getenv(
    'DOUBAO_ENDPOINT', 
    'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
)
DOUBAO_MODEL = 'Doubao-Seed-1.6-vision'

# 并发配置
MAX_WORKERS = 3  # 视觉模型较慢，建议设置较小的并发数
TIMEOUT = 60  # API 超时时间（秒）


# ==================== 工具函数 ====================
def load_panorama_coordinates(brand_folder: str) -> Dict[int, Dict]:
    """
    从品牌文件夹的 JSON 文件中加载所有点位的坐标信息
    
    Args:
        brand_folder: 品牌文件夹路径
    
    Returns:
        {seq_id: {position_x, position_y, position_z, direction_x, ...}, ...}
    """
    brand_name = os.path.basename(brand_folder)
    json_file = os.path.join(brand_folder, f'{brand_name}.json')
    
    if not os.path.exists(json_file):
        print(f'[WARN] JSON 文件不存在: {json_file}')
        return {}
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        coordinates = {}
        panorama_list = data.get('data', {}).get('panorama_list', [])
        
        for pano in panorama_list:
            seq_id = pano.get('seq_id')
            coord = pano.get('coordinate', {})
            
            if seq_id is not None and coord:
                coordinates[seq_id] = {
                    'position_x': coord.get('position_x', 0),
                    'position_y': coord.get('position_y', 0),
                    'position_z': coord.get('position_z', 0),
                    'direction_x': coord.get('direction_x', 0),
                    'direction_y': coord.get('direction_y', 0),
                    'direction_z': coord.get('direction_z', 0),
                    'direction_w': coord.get('direction_w', 0)
                }
        
        return coordinates
    except Exception as e:
        print(f'[ERROR] 读取坐标信息失败 {json_file}: {e}')
        return {}


def get_direction_angle(direction: str) -> float:
    """
    根据图片方向获取对应的角度（弧度）
    
    Args:
        direction: f(前)/b(后)/l(左)/r(右)
    
    Returns:
        角度（弧度）
    """
    direction_map = {
        'f': 0,           # 前: 0度
        'r': math.pi / 2, # 右: 90度
        'b': math.pi,     # 后: 180度
        'l': 3 * math.pi / 2  # 左: 270度
    }
    return direction_map.get(direction, 0)


def calculate_product_3d_position(
    bbox: Dict[str, float],
    direction: str,
    point_coord: Dict[str, float],
    estimated_distance: float = 2.0
) -> Dict[str, float]:
    """
    根据商品在图像中的边界框、拍摄方向和点位坐标，计算商品的3D坐标
    
    Args:
        bbox: 边界框 {x_min, y_min, x_max, y_max}（归一化坐标）
        direction: 图片方向 (f/b/l/r)
        point_coord: 点位坐标 {position_x, position_y, position_z}
        estimated_distance: 估算的商品距离（米），默认2米
    
    Returns:
        {x, y, z}: 商品的3D坐标
    """
    # 计算商品在图像中的中心点
    center_x = (bbox.get('x_min', 0) + bbox.get('x_max', 1)) / 2
    center_y = (bbox.get('y_min', 0) + bbox.get('y_max', 1)) / 2
    
    # 将图像坐标转换为角度偏移
    # center_x: 0.5 表示正中心，0 表示最左，1 表示最右
    # 假设图像视野角度为90度（FOV）
    fov_horizontal = math.pi / 2  # 90度视野
    fov_vertical = math.pi / 2
    
    # 计算水平和垂直角度偏移
    horizontal_offset = (center_x - 0.5) * fov_horizontal
    vertical_offset = (center_y - 0.5) * fov_vertical
    
    # 获取基础方向角度
    base_angle = get_direction_angle(direction)
    
    # 最终的水平角度
    final_angle = base_angle + horizontal_offset
    
    # 计算3D坐标（相对于点位）
    # 水平方向的距离分量
    dx = estimated_distance * math.cos(final_angle)
    dy = estimated_distance * math.sin(final_angle)
    
    # 垂直方向（z轴），考虑垂直角度偏移
    # 假设相机高度约1.6米（人眼高度）
    dz = -estimated_distance * math.tan(vertical_offset)
    
    # 计算最终的绝对坐标
    product_x = point_coord.get('position_x', 0) + dx
    product_y = point_coord.get('position_y', 0) + dy
    product_z = point_coord.get('position_z', 0) + dz
    
    return {
        'x': round(product_x, 3),
        'y': round(product_y, 3),
        'z': round(product_z, 3)
    }


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """将图片文件编码为 base64 字符串"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f'[ERROR] 编码图片失败 {image_path}: {e}')
        return None


def get_brand_folders(panorama_dir: str, brand_filter: Optional[List[str]] = None) -> List[str]:
    """
    获取需要处理的品牌文件夹列表
    
    Args:
        panorama_dir: panorama_json 根目录
        brand_filter: 品牌筛选列表，None 表示处理全部
    
    Returns:
        品牌文件夹路径列表
    """
    if not os.path.isdir(panorama_dir):
        print(f'[ERROR] 目录不存在: {panorama_dir}')
        return []
    
    all_folders = [
        os.path.join(panorama_dir, d) 
        for d in os.listdir(panorama_dir) 
        if os.path.isdir(os.path.join(panorama_dir, d))
    ]
    
    # 如果没有品牌筛选，返回全部
    if brand_filter is None:
        return all_folders
    
    # 筛选品牌
    filtered_folders = []
    for folder in all_folders:
        brand_name = os.path.basename(folder)
        if brand_name in brand_filter:
            filtered_folders.append(folder)
    
    return filtered_folders


def group_panorama_images(images_dir: str) -> Dict[str, Dict]:
    """
    将全景图片按 UUID 和 index 分组（排除 d 和 t 方向）
    
    返回格式: {
        "uuid_0": {
            "seq_id": 0,
            "images": ["path_to_f.jpg", "path_to_b.jpg", ...]
        },
        "uuid_1": {
            "seq_id": 1,
            "images": [...]
        },
        ...
    }
    """
    if not os.path.isdir(images_dir):
        return {}
    
    groups = {}
    for filename in os.listdir(images_dir):
        if not filename.lower().endswith('.jpg'):
            continue
        
        # 解析文件名格式: {uuid}_{index}_{direction}.jpg
        parts = filename.rsplit('_', 2)
        if len(parts) != 3:
            continue
        
        uuid_part, index_part, direction_part = parts
        direction = direction_part.replace('.jpg', '')
        
        # 跳过 d（向下）和 t（向上）方向的图片
        if direction in ['d', 't']:
            continue
        
        # 分组键: uuid_index
        group_key = f"{uuid_part}_{index_part}"
        
        if group_key not in groups:
            groups[group_key] = {
                'seq_id': int(index_part),  # 点位编号
                'images': []
            }
        
        groups[group_key]['images'].append(os.path.join(images_dir, filename))
    
    return groups


def call_doubao_vision_api(
    image_paths: List[str], 
    prompt: str,
    api_key: str,
    endpoint: str,
    seq_id: int
) -> Optional[Dict]:
    """
    调用豆包视觉模型 API
    
    Args:
        image_paths: 图片路径列表（一个全景位置的多个方向）
        prompt: 提示词
        api_key: API 密钥
        endpoint: API 端点
        seq_id: VR 点位编号
    
    Returns:
        模型返回的 JSON 结果，失败返回 None
    """
    if not api_key:
        print('[ERROR] 未设置 DOUBAO_API_KEY 环境变量')
        return None
    
    # 准备四个方向的图片（f/b/l/r）
    direction_images = {'f': None, 'b': None, 'l': None, 'r': None}
    
    for path in image_paths:
        for direction in ['f', 'b', 'l', 'r']:
            if path.endswith(f'_{direction}.jpg'):
                direction_images[direction] = path
                break
    
    # 编码所有找到的图片
    encoded_images = []
    for direction in ['f', 'b', 'l', 'r']:
        if direction_images[direction]:
            img_base64 = encode_image_to_base64(direction_images[direction])
            if img_base64:
                encoded_images.append({
                    'direction': direction,
                    'base64': img_base64
                })
    
    if not encoded_images:
        print('[WARN] 未找到有效图片')
        return None
    
    print(f'[DEBUG] 点位 {seq_id}: 找到 {len(encoded_images)} 个方向的图片：{[img["direction"] for img in encoded_images]}')
    
    # 构建请求
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 在提示词中加入点位编号和方向信息
    full_prompt = f"【当前 VR 点位编号：{seq_id}】\n"
    full_prompt += f"【图片方向：共 {len(encoded_images)} 个视角，按顺序为 "
    full_prompt += "、".join([f"图{i+1}({img['direction']}-{'前' if img['direction']=='f' else '后' if img['direction']=='b' else '左' if img['direction']=='l' else '右'})" 
                              for i, img in enumerate(encoded_images)])
    full_prompt += "】\n\n"
    full_prompt += prompt
    
    # 构建内容数组，包含所有图片和提示词
    content = []
    
    # 先添加所有图片
    for img in encoded_images:
        content.append({
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{img["base64"]}'
            }
        })
    
    # 最后添加文本提示词
    content.append({
        'type': 'text',
        'text': full_prompt
    })
    
    payload = {
        'model': DOUBAO_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': content
            }
        ],
        'temperature': 0.7,
        'max_tokens': 4096
    }
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        
        # 解析返回内容
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            
            # 尝试解析为 JSON
            try:
                # 清理可能的 markdown 代码块标记
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f'[WARN] JSON 解析失败: {e}')
                print(f'原始内容: {content[:200]}...')
                return {'raw_content': content, 'parse_error': str(e)}
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f'[ERROR] API 请求失败: {e}')
        return None
    except Exception as e:
        print(f'[ERROR] 处理响应失败: {e}')
        return None


def process_brand(
    brand_folder: str,
    api_key: str,
    endpoint: str,
    prompt: str,
    vr_loc_list: Optional[List[int]] = None
) -> Dict:
    """
    处理单个品牌的所有全景图片
    
    Args:
        brand_folder: 品牌文件夹路径
        api_key: API 密钥
        endpoint: API 端点
        prompt: 提示词
        vr_loc_list: VR 点位筛选列表，None 表示处理全部点位
    
    Returns:
        {
            'brand': '品牌名',
            'results': [
                {
                    'panorama_id': 'uuid_index',
                    'seq_id': 点位编号,
                    'images': ['path1', 'path2', ...],
                    'analysis': {...}  # 模型返回的分析结果
                },
                ...
            ],
            'success_count': 10,
            'fail_count': 2
        }
    """
    brand_name = os.path.basename(brand_folder)
    images_dir = os.path.join(brand_folder, 'images')
    
    # 加载点位坐标信息
    coordinates = load_panorama_coordinates(brand_folder)
    
    # 分组全景图片
    panorama_groups = group_panorama_images(images_dir)
    
    if not panorama_groups:
        print(f'[WARN] {brand_name}: 未找到有效的全景图片')
        return {
            'brand': brand_name,
            'results': [],
            'success_count': 0,
            'fail_count': 0
        }
    
    # 如果有点位筛选，计算实际要处理的点位数
    if vr_loc_list is not None:
        filtered_count = sum(1 for pg in panorama_groups.values() if pg['seq_id'] in vr_loc_list)
        print(f'\n[INFO] 开始处理品牌: {brand_name}（共 {len(panorama_groups)} 个全景位置，筛选后 {filtered_count} 个）')
    else:
        print(f'\n[INFO] 开始处理品牌: {brand_name}（共 {len(panorama_groups)} 个全景位置）')
    
    results = []
    success_count = 0
    fail_count = 0
    
    # 处理每个全景位置
    for panorama_id, panorama_data in tqdm(panorama_groups.items(), desc=brand_name):
        seq_id = panorama_data['seq_id']
        image_paths = panorama_data['images']
        
        # 如果指定了点位列表，只处理列表中的点位
        if vr_loc_list is not None and seq_id not in vr_loc_list:
            continue
        
        # 从图片路径中提取方向信息（使用 f 方向的图片）
        direction = 'f'  # 默认使用前视图
        for path in image_paths:
            if '_f.jpg' in path:
                direction = 'f'
                break
        
        analysis = call_doubao_vision_api(
            image_paths,
            prompt,
            api_key,
            endpoint,
            seq_id
        )
        
        if analysis:
            # 为每个商品计算3D坐标
            if 'products' in analysis and seq_id in coordinates:
                point_coord = coordinates[seq_id]
                for product in analysis['products']:
                    if 'bbox' in product and product['bbox']:
                        try:
                            product_3d = calculate_product_3d_position(
                                product['bbox'],
                                direction,
                                point_coord
                            )
                            product['position_3d'] = product_3d
                        except Exception as e:
                            print(f'[WARN] 计算3D坐标失败: {e}')
                            product['position_3d'] = None
            
            results.append({
                'panorama_id': panorama_id,
                'seq_id': seq_id,
                'images': image_paths,
                'analysis': analysis
            })
            success_count += 1
        else:
            results.append({
                'panorama_id': panorama_id,
                'seq_id': seq_id,
                'images': image_paths,
                'analysis': None,
                'error': '分析失败'
            })
            fail_count += 1
    
    return {
        'brand': brand_name,
        'results': results,
        'success_count': success_count,
        'fail_count': fail_count
    }


def save_results(brand_result: Dict, output_dir: str):
    """保存单个品牌的分析结果"""
    brand_name = brand_result['brand']
    output_file = os.path.join(output_dir, f'{brand_name}_analysis.json')
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(brand_result, f, ensure_ascii=False, indent=2)
    
    print(f'[INFO] 结果已保存: {output_file}')


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        description='使用豆包视觉模型分析商场全景图片'
    )
    parser.add_argument(
        '--brand_list',
        action='store_true',
        help='是否只处理 brand_list.py 中的品牌'
    )
    parser.add_argument(
        '--vr_loc_list',
        action='store_true',
        help='是否只处理 brand_list.py 中指定的 VR 点位号（vr_loc_list）'
    )
    parser.add_argument(
        '--panorama_dir',
        type=str,
        default=DEFAULT_PANORAMA_DIR,
        help='panorama_json 根目录路径'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./analysis_results',
        help='分析结果输出目录'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default=DOUBAO_API_KEY,
        help='豆包 API 密钥（可通过环境变量 DOUBAO_API_KEY 设置）'
    )
    parser.add_argument(
        '--endpoint',
        type=str,
        default=DOUBAO_ENDPOINT,
        help='豆包 API 端点'
    )
    
    args = parser.parse_args()
    
    # 检查 API 密钥
    if not args.api_key:
        print('[ERROR] 未设置 API 密钥！')
        print('请通过以下方式之一设置：')
        print('  1. 设置环境变量: export DOUBAO_API_KEY=your_key')
        print('  2. 使用命令行参数: --api_key your_key')
        sys.exit(1)
    
    # 确定需要处理的品牌
    brand_filter = None
    if args.brand_list:
        try:
            from brand_list import brand_list
            brand_filter = brand_list
            print(f'[INFO] 已加载品牌筛选列表（共 {len(brand_filter)} 个品牌）')
        except ImportError:
            print('[ERROR] 无法导入 brand_list.py')
            sys.exit(1)
    
    # 确定需要处理的 VR 点位
    vr_filter = None
    if args.vr_loc_list:
        try:
            from brand_list import vr_loc_list
            vr_filter = vr_loc_list
            print(f'[INFO] 已加载 VR 点位筛选列表：{vr_filter}')
        except ImportError:
            print('[ERROR] 无法从 brand_list.py 导入 vr_loc_list')
            sys.exit(1)
    
    # 获取品牌文件夹列表
    brand_folders = get_brand_folders(args.panorama_dir, brand_filter)
    
    if not brand_folders:
        print('[ERROR] 未找到需要处理的品牌文件夹')
        sys.exit(1)
    
    print(f'[INFO] 共找到 {len(brand_folders)} 个品牌待处理')
    print(f'[INFO] 使用模型: {DOUBAO_MODEL}')
    print(f'[INFO] API 端点: {args.endpoint}')
    print(f'[INFO] 结果输出目录: {args.output_dir}\n')
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 处理每个品牌
    all_results = []
    for brand_folder in brand_folders:
        try:
            result = process_brand(
                brand_folder,
                args.api_key,
                args.endpoint,
                vr_pic_prompt,
                vr_filter
            )
            
            # 保存结果
            save_results(result, args.output_dir)
            all_results.append(result)
            
            print(f'[INFO] {result["brand"]}: 成功 {result["success_count"]}, 失败 {result["fail_count"]}')
            
        except Exception as e:
            print(f'[ERROR] 处理品牌失败 {os.path.basename(brand_folder)}: {e}')
            import traceback
            traceback.print_exc()
    
    # 生成汇总报告
    summary = {
        'total_brands': len(all_results),
        'total_success': sum(r['success_count'] for r in all_results),
        'total_fail': sum(r['fail_count'] for r in all_results),
        'brands': [
            {
                'name': r['brand'],
                'success': r['success_count'],
                'fail': r['fail_count']
            }
            for r in all_results
        ]
    }
    
    summary_file = os.path.join(args.output_dir, 'summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print('\n' + '='*60)
    print('处理完成！')
    print(f'总品牌数: {summary["total_brands"]}')
    print(f'总成功数: {summary["total_success"]}')
    print(f'总失败数: {summary["total_fail"]}')
    print(f'汇总报告: {summary_file}')
    print('='*60)


if __name__ == '__main__':
    main()

