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
from tqdm import tqdm
from openai import OpenAI

# 导入提示词
from prompt import vr_product_prompt, vr_store_prompt
from dotenv import load_dotenv

load_dotenv()

# ==================== 配置项 ====================
DEFAULT_PANORAMA_DIR = os.path.join(
    os.path.dirname(__file__), 
    'panorama_json'
)

# 豆包 API 配置（需要配置环境变量）
DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
DOUBAO_BASE_URL = os.getenv(
    'DOUBAO_BASE_URL', 
    'https://ark.cn-beijing.volces.com/api/v3'
)
# 豆包模型名称 - 需要使用正确的模型名称
# 常见的豆包视觉模型名称（请根据实际情况调整）：
# - doubao-seed-1-6-250615 (参考代码中的模型)
# - doubao-vision-pro (可能的视觉模型)
# - ep-xxxxx (也可能是 endpoint ID)
DOUBAO_MODEL = os.getenv('DOUBAO_MODEL', 'doubao-seed-1-6-vision-250815')

# 并发配置
MAX_WORKERS = 3  # 视觉模型较慢，建议设置较小的并发数
TIMEOUT = 10000  # API 超时时间（秒），传入多张图片需要更长时间


# ==================== 工具函数 ====================
def load_panorama_coordinates(brand_folder: str) -> Dict[int, Dict]:
    """
    从品牌文件夹的 JSON 文件中加载所有点位的坐标信息
    
    Args:
        brand_folder: 品牌文件夹路径
    
    Returns:
        {seq_id: {id, position_x, position_y, position_z, direction_x, ...}, ...}
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
            panorama_id = pano.get('id')  # 获取 panorama 的 id
            coord = pano.get('coordinate', {})
            
            if seq_id is not None and coord:
                coordinates[seq_id] = {
                    'id': panorama_id,  # 添加 panorama id
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


def select_sample_points(all_seq_ids: List[int], max_points: Optional[int] = None) -> List[int]:
    """
    从所有点位中选择样本点，排除首尾各 总数/5 个点，从中间均匀分布选择
    
    Args:
        all_seq_ids: 所有点位的 seq_id 列表（已排序）
        max_points: 最大选择数量，None 表示不限制（选择所有中间点）
    
    Returns:
        选中的 seq_id 列表
    """
    total_count = len(all_seq_ids)
    
    # 如果没有限制，或者点位数很少，进行首尾去除后全部选择
    if max_points is None or total_count <= (max_points if max_points else 0):
        # 即使不限制数量，也要去除首尾
        if total_count <= 5:
            # 点位数太少，全部返回
            return all_seq_ids
    
    # 计算首尾各去除多少个点（总数 / 5，向下取整）
    trim_count = total_count // 5
    
    # 确保去除后至少还有一些点可选
    if trim_count * 2 >= total_count:
        # 如果去除的太多，只去除首尾各1个
        trim_count = 1
    
    # 去掉首尾，从中间选择
    start_index = trim_count
    end_index = total_count - trim_count
    middle_points = all_seq_ids[start_index:end_index]
    
    print(f'[DEBUG] 总点位 {total_count} 个，去除首部 {trim_count} 个、尾部 {trim_count} 个，剩余 {len(middle_points)} 个')
    
    # 如果没有限制，返回所有中间点位
    if max_points is None:
        print(f'[DEBUG] 不限制点位数量，使用所有 {len(middle_points)} 个中间点位')
        return middle_points
    
    if len(middle_points) <= max_points:
        # 中间点位数不超过最大值，全部选择
        return middle_points
    
    # 均匀分布选择
    step = (len(middle_points) - 1) / (max_points - 1)
    selected_indices = [int(round(i * step)) for i in range(max_points)]
    selected_seq_ids = [middle_points[i] for i in selected_indices]
    
    return selected_seq_ids


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
    base_url: str,
    seq_id: int,
    panorama_id: int
) -> Optional[Dict]:
    """
    调用豆包视觉模型 API（使用 OpenAI SDK）
    
    Args:
        image_paths: 图片路径列表（一个全景位置的多个方向）
        prompt: 提示词
        api_key: API 密钥
        base_url: API 基础 URL
        seq_id: VR 点位序列号（用于内部标识）
        panorama_id: VR 点位 ID（JSON 中的 id 字段，传给模型）
    
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
    
    print(f'[DEBUG] 点位 seq_id={seq_id}, panorama_id={panorama_id}: 找到 {len(encoded_images)} 个方向的图片：{[img["direction"] for img in encoded_images]}')
    
    # 计算总的图片大小（用于调试）
    total_size = sum(len(img['base64']) for img in encoded_images)
    print(f'[DEBUG] 点位 {panorama_id}: Base64 总大小约 {total_size / 1024 / 1024:.2f} MB')
    
    # 初始化 OpenAI 客户端（兼容豆包 API）
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 在提示词中加入点位 ID 和方向信息（使用 panorama_id 而不是 seq_id）
    full_prompt = f"【当前 VR 点位 ID：{panorama_id}】\n"
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
    
    try:
        print(f'[DEBUG] 正在发送请求到: {base_url}')
        print(f'[DEBUG] 使用模型: {DOUBAO_MODEL}')
        print(f'[DEBUG] 请求包含 {len(encoded_images)} 张图片')
        
        # 使用 OpenAI SDK 调用（兼容豆包 API）
        response = client.chat.completions.create(
            model=DOUBAO_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': content
                }
            ],
            temperature=0.7,
            max_tokens=4096,
            timeout=TIMEOUT
        )
        
        print(f'[DEBUG] 收到响应，消耗 tokens: {response.usage.total_tokens if hasattr(response, "usage") else "未知"}')
        
        # 解析返回内容
        if response.choices and len(response.choices) > 0:
            response_content = response.choices[0].message.content
            
            # 尝试解析为 JSON
            try:
                # 清理可能的 markdown 代码块标记
                response_content = response_content.strip()
                if response_content.startswith('```json'):
                    response_content = response_content[7:]
                if response_content.startswith('```'):
                    response_content = response_content[3:]
                if response_content.endswith('```'):
                    response_content = response_content[:-3]
                response_content = response_content.strip()
                
                # 使用 JSONDecoder 的 raw_decode，它会忽略尾部额外数据
                decoder = json.JSONDecoder()
                try:
                    result, index = decoder.raw_decode(response_content)
                    
                    # 检查是否有额外数据
                    remaining = response_content[index:].strip()
                    if remaining:
                        print(f'[WARN] JSON 解析成功，但发现额外数据（已忽略）: {remaining[:100]}...')
                    
                    return result
                except json.JSONDecodeError:
                    # 如果 raw_decode 也失败，尝试标准 json.loads
                    return json.loads(response_content)
                    
            except json.JSONDecodeError as e:
                print(f'[ERROR] JSON 解析失败: {e}')
                
                # 显示错误位置附近的内容
                error_pos = e.pos if hasattr(e, 'pos') else 0
                start = max(0, error_pos - 200)
                end = min(len(response_content), error_pos + 200)
                
                print('错误位置附近的内容（前后各200字符）:')
                print(f'...[{start}:{error_pos}]...')
                print(response_content[start:error_pos])
                print('>>> 错误位置 <<<')
                print(response_content[error_pos:end])
                print(f'...[{error_pos}:{end}]...')
                
                # 保存完整内容到文件以便调试
                debug_file = f'debug_json_error_{seq_id}_{panorama_id}.txt'
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_content)
                    print(f'[DEBUG] 完整响应已保存到: {debug_file}')
                except Exception:
                    pass
                
                return {'raw_content': response_content, 'parse_error': str(e)}
        
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f'[ERROR] API 调用失败: {error_msg}')
        print(f'[调试信息] Base URL: {base_url}')
        print(f'[调试信息] Model: {DOUBAO_MODEL}')
        print(f'[调试信息] 图片数量: {len(encoded_images)}')
        print(f'[调试信息] 请求大小: {total_size / 1024 / 1024:.2f} MB')
        
        # 提供可能的解决方案
        if '404' in error_msg:
            print('[提示] 404 错误可能原因：')
            print('  1. 模型名称不正确，请检查 DOUBAO_MODEL 配置')
            print('  2. Base URL 不正确，当前: {}'.format(base_url))
            print('  3. 该模型可能不支持视觉功能')
        elif 'timeout' in error_msg.lower():
            print(f'[提示] 请求超时（{TIMEOUT}秒），传入了 {len(encoded_images)} 张图片')
        
        import traceback
        traceback.print_exc()
        return None


def call_doubao_store_analysis_api(
    all_point_images: List[Dict],
    prompt: str,
    api_key: str,
    base_url: str,
    brand_name: str
) -> Optional[Dict]:
    """
    调用豆包 API 分析整个店铺环境（综合所有点位）
    
    Args:
        all_point_images: 所有点位的图片列表 [{'seq_id': 0, 'images': [...]}, ...]
        prompt: 提示词
        api_key: API 密钥
        base_url: API 基础 URL
        brand_name: 品牌名称
    
    Returns:
        模型返回的 JSON 结果，失败返回 None
    """
    if not api_key:
        print('[ERROR] 未设置 DOUBAO_API_KEY 环境变量')
        return None
    
    # 收集所有点位的图片（每个点位选择f方向）
    # 这里的 all_point_images 已经是选择好的点位了（最多5个）
    encoded_images = []
    for point_data in all_point_images:
        image_paths = point_data['images']
        # 找到f方向的图片
        for path in image_paths:
            if path.endswith('_f.jpg'):
                img_base64 = encode_image_to_base64(path)
                if img_base64:
                    encoded_images.append({
                        'seq_id': point_data['seq_id'],
                        'base64': img_base64
                    })
                break
    
    if not encoded_images:
        print('[WARN] 未找到有效的店铺图片')
        return None
    
    point_seq_ids = [img['seq_id'] for img in encoded_images]
    print(f'[INFO] 店铺环境分析：收集了 {len(encoded_images)} 个点位的图片 {point_seq_ids}')
    
    # 初始化客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 构建提示词
    full_prompt = f"【品牌名称：{brand_name}】\n"
    full_prompt += f"【包含点位：{len(encoded_images)} 个VR点位】\n\n"
    full_prompt += prompt
    
    # 构建内容数组
    content = []
    for img in encoded_images:
        content.append({
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/jpeg;base64,{img["base64"]}'
            }
        })
    
    content.append({
        'type': 'text',
        'text': full_prompt
    })
    
    try:
        print('[DEBUG] 正在分析店铺环境...')
        
        response = client.chat.completions.create(
            model=DOUBAO_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': content
                }
            ],
            temperature=0.7,
            max_tokens=4096,
            timeout=TIMEOUT
        )
        
        print('[DEBUG] 店铺分析完成')
        
        if response.choices and len(response.choices) > 0:
            response_content = response.choices[0].message.content
            
            try:
                response_content = response_content.strip()
                
                # 清理 markdown 代码块
                if response_content.startswith('```json'):
                    response_content = response_content[7:]
                if response_content.startswith('```'):
                    response_content = response_content[3:]
                if response_content.endswith('```'):
                    response_content = response_content[:-3]
                response_content = response_content.strip()
                
                # 使用 JSONDecoder 的 raw_decode，它会忽略尾部额外数据
                decoder = json.JSONDecoder()
                try:
                    result, index = decoder.raw_decode(response_content)
                    
                    # 检查是否有额外数据
                    remaining = response_content[index:].strip()
                    if remaining:
                        print(f'[WARN] JSON 解析成功，但发现额外数据（已忽略）: {remaining[:100]}...')
                    
                    return result
                except json.JSONDecodeError:
                    # 如果 raw_decode 也失败，尝试标准 json.loads
                    return json.loads(response_content)
                    
            except json.JSONDecodeError as e:
                print(f'[ERROR] 店铺分析 JSON 解析失败: {e}')
                
                # 显示错误位置附近的内容
                error_pos = e.pos if hasattr(e, 'pos') else 0
                start = max(0, error_pos - 200)
                end = min(len(response_content), error_pos + 200)
                
                print('错误位置附近的内容（前后各200字符）:')
                print(f'...[{start}:{error_pos}]...')
                print(response_content[start:error_pos])
                print('>>> 错误位置 <<<')
                print(response_content[error_pos:end])
                print(f'...[{error_pos}:{end}]...')
                
                # 保存完整内容到文件以便调试
                debug_file = f'debug_store_json_error_{brand_name}.txt'
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_content)
                    print(f'[DEBUG] 完整响应已保存到: {debug_file}')
                except Exception:
                    pass
                
                return {'raw_content': response_content, 'parse_error': str(e)}
        
        return None
        
    except Exception as e:
        print(f'[ERROR] 店铺环境分析失败: {e}')
        return None


def process_brand(
    brand_folder: str,
    api_key: str,
    base_url: str,
    vr_loc_list: Optional[List[int]] = None,
    max_product_points: int = 10,
    max_store_points: int = 10
) -> Dict:
    """
    处理单个品牌的所有全景图片
    
    Args:
        brand_folder: 品牌文件夹路径
        api_key: API 密钥
        base_url: API 基础 URL
        vr_loc_list: VR 点位筛选列表，None 表示处理全部点位
        max_product_points: 商品分析最大点位数，默认 10 个
        max_store_points: 店铺分析最大点位数，默认 10 个
    
    Returns:
        {
            'brand': '品牌名',
            'product_results': [  # 各点位的商品数据
                {
                    'panorama_id': 点位ID,
                    'seq_id': 点位序列号,
                    'images': ['path1', 'path2', ...],
                    'products': [...]  # 商品列表
                },
                ...
            ],
            'store_analysis': {...},  # 整体店铺环境分析
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
    
    # 获取所有点位的 seq_id 并排序
    all_seq_ids = sorted([pg['seq_id'] for pg in panorama_groups.values()])
    
    # 应用 vr_loc_list 筛选（如果有）
    if vr_loc_list is not None:
        all_seq_ids = [sid for sid in all_seq_ids if sid in vr_loc_list]
        print(f'\n[INFO] 应用 vr_loc_list 筛选后: {len(all_seq_ids)} 个点位')
    
    # 选择商品分析的样本点位（默认不限制）
    product_seq_ids = select_sample_points(all_seq_ids, max_points=max_product_points)
    
    # 选择店铺分析的样本点位（默认10个）
    store_seq_ids = select_sample_points(all_seq_ids, max_points=max_store_points)
    
    print(f'\n[INFO] 开始处理品牌: {brand_name}')
    print(f'  - 总点位数: {len(panorama_groups)}')
    if vr_loc_list is not None:
        print(f'  - 筛选后: {len(all_seq_ids)} 个点位')
    print(f'  - 商品分析点位: {len(product_seq_ids)} 个 {product_seq_ids}')
    print(f'  - 店铺分析点位: {len(store_seq_ids)} 个 {store_seq_ids}')
    
    # ========== 第一阶段：按点位分析商品 ==========
    print('[INFO] 第一阶段：分析各点位商品...')
    
    product_results = []
    store_point_images = []  # 收集店铺分析的点位图片
    success_count = 0
    fail_count = 0
    
    for panorama_key, panorama_data in tqdm(panorama_groups.items(), desc=f'{brand_name}-商品'):
        seq_id = panorama_data['seq_id']
        image_paths = panorama_data['images']
        
        # 只处理选中的商品分析点位
        if seq_id not in product_seq_ids:
            continue
        
        # 获取 panorama_id
        panorama_id_value = coordinates.get(seq_id, {}).get('id', seq_id)
        
        # 调用商品分析 API（使用 vr_product_prompt）
        analysis = call_doubao_vision_api(
            image_paths,
            vr_product_prompt,  # 使用商品分析提示词
            api_key,
            base_url,
            seq_id,
            panorama_id_value
        )
        
        if analysis:
            # 检查是否有商品数据
            products = analysis.get('products', [])
            
            # 只为推荐商品计算3D坐标
            if products and seq_id in coordinates:
                point_coord = coordinates[seq_id]
                for product in products:
                    # 只有推荐商品才计算坐标
                    if product.get('is_recommended', False) and 'bbox' in product and product['bbox']:
                        try:
                            # 使用模型返回的图片方向（而不是默认的'f'）
                            product_direction = product.get('view_direction', 'f')
                            product_3d = calculate_product_3d_position(
                                product['bbox'],
                                product_direction,  # 使用正确的方向
                                point_coord
                            )
                            product['position_3d'] = product_3d
                        except Exception as e:
                            print(f'[WARN] 计算3D坐标失败: {e}')
                            product['position_3d'] = None
                    else:
                        # 非推荐商品不返回坐标
                        product['position_3d'] = None
            
            # 只保存有商品的点位
            if products:
                product_results.append({
                    'panorama_id': panorama_id_value,
                    'seq_id': seq_id,
                    'images': image_paths,
                    'products': products
                })
                success_count += 1
            else:
                print(f'[INFO] 点位 {seq_id} (ID:{panorama_id_value}) 未检测到商品，跳过')
        else:
            print(f'[WARN] 点位 {seq_id} (ID:{panorama_id_value}) 分析失败，跳过')
            fail_count += 1
    
    # ========== 第二阶段：分析整体店铺环境 ==========
    print('\n[INFO] 第二阶段：分析店铺整体环境...')
    
    # 收集店铺分析需要的点位图片
    for panorama_key, panorama_data in panorama_groups.items():
        seq_id = panorama_data['seq_id']
        image_paths = panorama_data['images']
        
        # 只收集店铺分析选中的点位
        if seq_id in store_seq_ids:
            store_point_images.append({
                'seq_id': seq_id,
                'images': image_paths
            })
    
    store_analysis = None
    if store_point_images:
        store_analysis = call_doubao_store_analysis_api(
            store_point_images,
            vr_store_prompt,  # 使用店铺分析提示词
            api_key,
            base_url,
            brand_name
        )
    
    # ========== 合并结果 ==========
    return {
        'brand': brand_name,
        'product_results': product_results,  # 各点位的商品数据
        'store_analysis': store_analysis,    # 整体店铺环境分析
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
        default='C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\vr_pic_to_prod\\analysis_results',
        help='分析结果输出目录'
    )
    parser.add_argument(
        '--api_key',
        type=str,
        default=DOUBAO_API_KEY,
        help='豆包 API 密钥（可通过环境变量 DOUBAO_API_KEY 设置）'
    )
    parser.add_argument(
        '--base_url',
        type=str,
        default=DOUBAO_BASE_URL,
        help='豆包 API 基础 URL'
    )
    parser.add_argument(
        '--max_product_points',
        type=int,
        default=10,
        help='商品分析最大点位数（默认10个）'
    )
    parser.add_argument(
        '--max_store_points',
        type=int,
        default=10,
        help='店铺分析最大点位数（默认10个）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新分析已有结果的品牌'
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
    print(f'[INFO] API 基础 URL: {args.base_url}')
    print(f'[INFO] 结果输出目录: {args.output_dir}\n')
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 处理每个品牌
    all_results = []
    for brand_folder in brand_folders:
        brand_name = os.path.basename(brand_folder)
        output_file = os.path.join(args.output_dir, f'{brand_name}_analysis.json')
        
        # 检查是否已经有分析结果
        if not args.force and os.path.exists(output_file):
            print(f'[SKIP] {brand_name}: 已有分析结果，跳过（使用 --force 强制重新分析）')
            
            # 加载已有结果用于生成汇总报告
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    all_results.append(result)
            except Exception as e:
                print(f'[WARN] 无法读取已有结果 {output_file}: {e}')
            
            continue
        
        try:
            result = process_brand(
                brand_folder,
                args.api_key,
                args.base_url,
                vr_filter,
                max_product_points=args.max_product_points,
                max_store_points=args.max_store_points
            )
            
            # 保存结果
            save_results(result, args.output_dir)
            all_results.append(result)
            
            print(f'[INFO] {result["brand"]}: 成功 {result["success_count"]}, 失败 {result["fail_count"]}')
            
        except Exception as e:
            print(f'[ERROR] 处理品牌失败 {brand_name}: {e}')
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

