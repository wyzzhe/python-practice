#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理 raw_json 文件夹中品牌数据的商品信息提取器
从HTML文件中提取商品信息，支持多种品牌
"""
import pathlib
import sys, os

project_root = pathlib.Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mall_rag_admin.settings')

# from utils.dj_setup import *
import re
import json
from pathlib import Path
import logging
import sys
from dotenv import load_dotenv

load_dotenv()
place_id = os.environ.get('PLACE_ID')
monthly_type = os.environ.get('MONTHLY_TYPE')

# 添加scripts目录到Python路径，以便导入price_extractor
sys.path.append(str(Path(__file__).parent))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BrandProductExtractor:
    """品牌商品信息提取器"""

    # 类级别的单例price_extractor和字体缓存
    _price_extractor = None
    _font_cache = {}  # {font_family: {url: str, loaded: bool, mappings: dict}}
    _html_content_cache = {}  # {file_path: content}

    def __init__(self, html_file_path):
        self.html_file_path = html_file_path
        self.brand_name = Path(html_file_path).stem
        self.products = []
        self.price_mapping = {}

        # 初始化类级别的price_extractor（单例）
        if BrandProductExtractor._price_extractor is None:
            try:
                from ali_font_price_extractor import AliFontDecoder
                BrandProductExtractor._price_extractor = AliFontDecoder()
                logger.info("成功创建价格解码器单例")
            except ImportError as e:
                logger.warning(f"无法导入价格解码器: {e}")
                BrandProductExtractor._price_extractor = None

        self.price_extractor = BrandProductExtractor._price_extractor

    def read_html_file(self):
        """读取HTML文件，处理GBK编码 - 带缓存"""
        # 检查类级别缓存
        if self.html_file_path in BrandProductExtractor._html_content_cache:
            return BrandProductExtractor._html_content_cache[self.html_file_path]

        try:
            with open(self.html_file_path, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read()
            logger.info(f"成功读取HTML文件: {self.html_file_path}")

            # 缓存内容
            BrandProductExtractor._html_content_cache[self.html_file_path] = content
            return content
        except Exception as e:
            logger.error(f"读取HTML文件失败: {e}")
            return None

    def extract_products(self):
        """提取商品信息"""
        content = self.read_html_file()
        if not content:
            return []

        # 处理jsonp包装的内容
        content = self._extract_jsonp_content(content)
        if not content:
            logger.error("无法提取jsonp中的HTML内容")
            return []

        # 提取价格映射
        self._extract_price_mapping(content)

        # 查找所有商品项
        product_items = self._find_product_items(content)
        logger.info(f"找到 {len(product_items)} 个商品项")

        for item_content in product_items:
            try:
                product = self._extract_single_product(item_content)
                if product:
                    self.products.append(product)
            except Exception as e:
                logger.warning(f"提取商品信息时出错: {e}")
                continue

        return self.products

    def _extract_jsonp_content(self, content):
        """从jsonp调用中提取HTML内容"""
        try:
            # 查找各种jsonp模式
            patterns = [
                r'jsonp\d+\("(.*)"\)',  # jsonp1034("...")
                r'jsonp\d+\(\'(.*?)\'\)',  # jsonp1034('...')
                r'jsonp\d+\(`(.*?)`\)',  # jsonp1034(`...`)
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    html_content = match.group(1)
                    # 解码HTML实体和Unicode转义
                    html_content = self._decode_html_content(html_content)
                    logger.info("成功提取jsonp中的HTML内容")
                    return html_content

            logger.warning("未找到jsonp包装，尝试直接解析")
            return self._decode_html_content(content)
        except Exception as e:
            logger.error(f"提取jsonp内容失败: {e}")
            return self._decode_html_content(content)

    def _decode_html_content(self, content):
        """解码HTML内容中的各种编码"""
        try:
            # 解码HTML实体
            content = content.replace('\\"', '"')
            content = content.replace('\\/', '/')
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&amp;', '&')
            content = content.replace('&quot;', '"')
            content = content.replace('&#39;', "'")

            # 更安全的Unicode转义序列处理
            try:
                # 使用正则表达式替换Unicode转义序列
                import re
                # 处理 \uXXXX 格式
                content = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), content)
                # 处理 \xXX 格式
                content = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), content)
                # 处理其他转义字符
                content = content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
            except Exception as e:
                logger.warning(f"Unicode解码时出错: {e}")

            # 处理HTML实体
            import html
            content = html.unescape(content)

            return content
        except Exception as e:
            logger.warning(f"解码HTML内容时出错: {e}")
            return content

    def _extract_price_mapping(self, content):
        """从HTML商品块中提取价格映射 - 优先从c-price中获取"""
        try:
            # 首先找到所有完整的商品块
            item_blocks = re.findall(r'<dl[^>]*class="[^"]*item[^"]*"[^>]*data-id="([^"]*)"[^>]*>.*?</dl>', content,
                                     re.DOTALL)

            if not item_blocks:
                # 备用方法：查找所有商品ID
                id_pattern = r'data-id="([^"]*)"'
                item_blocks = re.findall(id_pattern, content)

            logger.info(f"找到 {len(item_blocks)} 个商品块")

            # 为每个商品ID查找对应的完整商品块并提取价格
            logger.info("开始为每个商品ID查找对应的价格...")

            for item_id in item_blocks:
                # 查找包含该商品ID的完整商品块
                item_block_pattern = rf'<dl[^>]*data-id="{item_id}"[^>]*>.*?</dl>'
                item_match = re.search(item_block_pattern, content, re.DOTALL)

                if item_match:
                    item_content = item_match.group(0)

                    # 在商品块内查找价格信息
                    price = self._extract_price_from_item_block(item_content, item_id)
                    if price:
                        self.price_mapping[item_id] = price
                        logger.debug(f"商品 {item_id} 在商品块中找到价格: {price}")
                        continue

                # 如果找不到完整商品块，标记为未找到
                logger.warning(f"商品 {item_id} 未找到完整的商品块或价格信息")

            logger.info(f"成功为 {len(self.price_mapping)} 个商品找到价格")

        except Exception as e:
            logger.error(f"提取价格映射失败: {e}")

    def _extract_price_from_item_block(self, item_content, item_id):
        """从商品块中提取价格 - 优先从c-price中获取，使用price_extractor解码"""
        try:
            # 方法1: 优先从c-price class中提取价格
            c_price_patterns = [
                r'<span[^>]*class="[^"]*c-price[^"]*"[^>]*>([^<]*)</span>',  # c-price class
                r'<span[^>]*class="[^"]*c-price[^"]*"[^>]*style="[^"]*font-family:\s*([^;"]+)[^"]*"[^>]*>([^<]*)</span>',
                # 带字体样式的c-price
            ]

            for pattern in c_price_patterns:
                matches = re.findall(pattern, item_content)
                for match in matches:
                    if isinstance(match, tuple):
                        # 带字体样式的匹配
                        font_family = match[0]
                        price_text = match[1].strip()
                    else:
                        # 普通匹配
                        font_family = None
                        price_text = match.strip()

                    if price_text:
                        # 如果font_family是None，尝试从style属性中单独提取
                        if font_family is None:
                            font_family = self._extract_font_family_from_style(item_content)

                        # 尝试使用price_extractor解码价格
                        decoded_price = self._decode_price_with_extractor(price_text, font_family)
                        if decoded_price:
                            logger.info(f"商品 {item_id} 从c-price中提取到价格: {price_text} -> {decoded_price}")
                            return decoded_price

            # 方法2: 如果c-price中没有找到，尝试从价格注释中提取
            comment_pattern = r'<!--\s*item\.discntPrice:\s*([^>]*?)\s*-->'
            comment_matches = re.findall(comment_pattern, item_content)
            if comment_matches:
                price_text = comment_matches[0].strip()
                if self._is_valid_price(price_text):
                    logger.info(f"商品 {item_id} 从注释中提取到价格: {price_text}")
                    return price_text

            # 方法3: 备用方法：从其他价格相关class中提取
            price_patterns = [
                r'<span[^>]*class="[^"]*price[^"]*"[^>]*>([^<]*)</span>',  # price class
                r'<div[^>]*class="[^"]*price[^"]*"[^>]*>([^<]*)</div>',  # price div
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, item_content)
                for match in matches:
                    price_text = match.strip()
                    # 检查是否是有效的价格格式
                    if self._is_valid_price(price_text):
                        logger.info(f"商品 {item_id} 从其他价格class中提取到价格: {price_text}")
                        return price_text

            return None

        except Exception as e:
            logger.debug(f"从商品块提取价格失败: {e}")
            return None

    def _extract_font_family_from_style(self, item_content):
        """从商品块的style属性中提取字体族名称"""
        try:
            # 查找包含c-price的span标签，并提取其style属性中的font-family
            font_pattern = r'<span[^>]*class="[^"]*c-price[^"]*"[^>]*style="[^"]*font-family:\s*([^;"]+)[^"]*"[^>]*>'
            match = re.search(font_pattern, item_content)
            if match:
                return match.group(1).strip()

            # 备用方法：查找任何包含font-family的style属性
            font_pattern2 = r'style="[^"]*font-family:\s*([^;"]+)[^"]*"'
            match = re.search(font_pattern2, item_content)
            if match:
                return match.group(1).strip()

            return None

        except Exception as e:
            logger.debug(f"从style属性提取字体族名称失败: {e}")
            return None

    def _decode_price_with_extractor(self, price_text, font_family=None):
        """使用price_extractor解码价格 - 优化版本，避免重复加载字体"""
        if not self.price_extractor:
            return None

        try:
            # 如果价格文本看起来像是字体编码的，尝试解码
            if self._looks_like_encoded_price(price_text):
                # 检查字体是否已经加载
                if font_family and font_family in BrandProductExtractor._font_cache:
                    font_info = BrandProductExtractor._font_cache[font_family]
                    if font_info.get('loaded'):
                        # 字体已加载，直接解码
                        decoded_price = self.price_extractor.decode_price(price_text)
                        if decoded_price and decoded_price != price_text:
                            return decoded_price

                # 如果字体未加载，尝试加载
                if font_family:
                    # 尝试从HTML中提取字体URL
                    font_url = self._extract_font_url_from_html()
                    if font_url:
                        # 检查是否需要加载字体
                        if (font_family not in BrandProductExtractor._font_cache or
                                not BrandProductExtractor._font_cache[font_family].get('loaded')):

                            # 加载字体
                            if self.price_extractor.load_font_by_family_and_url(font_family, font_url):
                                # 更新字体缓存状态
                                BrandProductExtractor._font_cache[font_family] = {
                                    'url': font_url,
                                    'loaded': True,
                                    'mappings': self.price_extractor.number_mappings.copy()
                                }
                                logger.info(f"字体 {font_family} 加载成功并缓存")
                            else:
                                # 字体加载失败，标记为失败
                                BrandProductExtractor._font_cache[font_family] = {
                                    'url': font_url,
                                    'loaded': False,
                                    'mappings': {}
                                }
                                return price_text

                        # 尝试解码价格
                        decoded_price = self.price_extractor.decode_price(price_text)
                        if decoded_price and decoded_price != price_text:
                            return decoded_price

            # 如果解码失败或不需要解码，返回原文本
            return price_text

        except Exception as e:
            logger.debug(f"使用price_extractor解码价格失败: {e}")
            return price_text

    def _looks_like_encoded_price(self, price_text):
        """判断价格文本是否看起来像是字体编码的"""
        # 检查是否包含HTML实体编码
        if '&#' in price_text:
            return True

        # 检查是否包含非ASCII字符（可能是字体编码）
        if any(ord(char) > 127 for char in price_text):
            return True

        # 检查是否看起来像乱码
        if len(price_text) > 5 and not re.match(r'^[\d\s¥￥\.\,]+$', price_text):
            return True

        return False

    def _extract_font_url_from_html(self):
        """从HTML中提取字体URL"""
        try:
            # 读取HTML文件内容
            content = self.read_html_file()
            if not content:
                return None

            # 查找字体映射信息
            font_patterns = [
                r'fontUrl\s*:\s*["\']([^"\']+)["\']',
                r'fontUrl\s*:\s*([^\s,}]+)',
                r'webfontcdn\.taobao\.com/webfont/[^"\'\s]+',
            ]

            for pattern in font_patterns:
                match = re.search(pattern, content)
                if match:
                    font_url = match.group(1) if match.groups() else match.group(0)
                    if font_url.startswith('http'):
                        return font_url
                    elif font_url.startswith('//'):
                        return 'https:' + font_url
                    else:
                        return 'https://' + font_url

            return None

        except Exception as e:
            logger.debug(f"提取字体URL失败: {e}")
            return None

    def _extract_price_from_context(self, context, item_id):
        """从上下文中提取价格"""
        try:
            # 查找包含数字的文本，可能是价格
            number_patterns = [
                r'>([^<]*\d+[^<]*)<',  # 标签内的数字文本
                r'<span[^>]*>([^<]*\d+[^<]*)</span>',  # span内的数字文本
            ]

            for pattern in number_patterns:
                matches = re.findall(pattern, context)
                for match in matches:
                    price_text = match.strip()
                    if self._is_valid_price(price_text):
                        return price_text

            return None

        except Exception as e:
            logger.debug(f"从上下文提取价格失败: {e}")
            return None

    def _is_valid_price(self, price_text):
        """检查是否是有效的价格格式"""
        try:
            # 移除常见的价格前缀和后缀
            clean_price = price_text.replace('¥', '').replace('￥', '').replace('元', '').replace('RMB', '').strip()

            # 检查是否包含数字和小数点
            if re.match(r'^\d+\.?\d*$', clean_price):
                # 转换为浮点数验证
                price_float = float(clean_price)
                # 价格应该在合理范围内 (10 到 100000) - 排除太小的数字
                if 10 <= price_float <= 100000:
                    # 排除明显不是价格的数字 (如销量、SKU编号等)
                    if price_float >= 100:  # 13DE MARZO的商品价格通常在100以上
                        return clean_price
                    elif price_float >= 10 and price_float < 100:
                        # 对于10-100之间的数字，需要额外验证
                        # 检查是否包含小数点 (如 88.00)
                        if '.' in clean_price:
                            return clean_price
                        # 检查是否是常见的价格数字 (如 88, 99等)
                        if price_float in [88, 99, 89, 79, 69, 59, 49, 39, 29, 19]:
                            return clean_price

            return None

        except Exception:
            return None

    def _find_product_items(self, content):
        """查找所有商品项"""
        try:
            # 查找商品项的模式 - 基于实际HTML结构
            # 先找到所有data-id的位置 - 尝试多种模式
            id_positions = []

            # 模式1: 转义引号
            for match in re.finditer(r'data-id=\\"([^"]*)\\"', content):
                id_positions.append(match.start())

            # 模式2: 普通引号
            if not id_positions:
                for match in re.finditer(r'data-id="([^"]*)"', content):
                    id_positions.append(match.start())

            logger.info(f"找到 {len(id_positions)} 个data-id位置")

            items = []
            for i, id_pos in enumerate(id_positions):
                # 从data-id位置向前查找<dl标签的开始
                start_pos = content.rfind('<dl', 0, id_pos)
                if start_pos == -1:
                    continue

                # 从<dl开始查找对应的</dl>结束标签
                # 使用简单的计数方法找到匹配的结束标签
                open_count = 0
                end_pos = start_pos
                for j in range(start_pos, len(content)):
                    if content[j:j + 3] == '<dl':
                        open_count += 1
                    elif content[j:j + 4] == '</dl':
                        open_count -= 1
                        if open_count == 0:
                            end_pos = j + 4
                            break

                if end_pos > start_pos:
                    item_content = content[start_pos:end_pos]
                    items.append(item_content)

            logger.info(f"找到 {len(items)} 个完整的商品项")
            return items

        except Exception as e:
            logger.error(f"查找商品项失败: {e}")
            return []

    def _extract_single_product(self, item_content):
        """提取单个商品信息 - 在同一个商品块内提取所有字段"""
        product = {}

        # 提取商品ID - 从当前商品块中提取
        id_match = re.search(r'data-id="([^"]*)"', item_content)
        if id_match:
            product['product_taobao_id'] = id_match.group(1)
        else:
            product['product_taobao_id'] = 'N/A'

        # 提取商品标题 - 基于实际HTML结构
        title = None

        # 方法1: 从item-name class中提取
        title_match = re.search(r'<a[^>]*class="[^"]*item-name[^"]*"[^>]*>([^<]*)</a>', item_content)
        if title_match:
            title = title_match.group(1).strip()

        # 方法2: 从图片alt属性中提取
        if not title:
            alt_match = re.search(r'<img[^>]*alt="([^"]*)"', item_content)
            if alt_match:
                title = alt_match.group(1).strip()

        # 方法3: 从链接文本中提取（处理HTML实体编码）
        if not title:
            # 查找所有链接文本
            link_texts = re.findall(r'<a[^>]*>([^<]*)</a>', item_content)
            for link_text in link_texts:
                # 清理HTML实体编码
                clean_text = link_text.replace('&lt;', '<').replace('&gt;', '>').strip()
                if clean_text and len(clean_text) > 10:  # 标题通常比较长
                    title = clean_text
                    break

        if title:
            product['title'] = title
        else:
            product['title'] = '标题未知'

        # 提取atpanel信息
        atpanel_match = re.search(r'atpanel="[^"]*"', item_content)
        if atpanel_match:
            product['atpanel'] = atpanel_match.group(0)

        # 提取详情链接
        url_match = re.search(r'<a[^>]*class="[^"]*item-name[^"]*"[^>]*href="([^"]*)"', item_content)
        if url_match:
            product['detail_url'] = url_match.group(1)

        # 提取商品图片
        img_match = re.search(r'<img[^>]*data-ks-lazyload="([^"]*)"', item_content)
        if img_match:
            product['image_url'] = img_match.group(1)
        else:
            img_match = re.search(r'<img[^>]*src="([^"]*)"', item_content)
            if img_match:
                product['image_url'] = img_match.group(1)

        # 提取图片alt文本
        alt_match = re.search(r'<img[^>]*alt="([^"]*)"', item_content)
        if alt_match:
            product['image_alt'] = alt_match.group(1)

        # 提取价格信息 - 优先使用价格映射，因为已经通过price_extractor处理过
        product_taobao_id = product.get('product_taobao_id')
        if product_taobao_id and product_taobao_id in self.price_mapping:
            product['price'] = self.price_mapping[product_taobao_id]
            product['price_source'] = 'c-price_decoded'
        else:
            # 备用方法：从商品块中查找价格注释
            comment_match = re.search(r'<!--\s*item\.discntPrice:\s*([^>]*?)\s*-->', item_content)
            if comment_match:
                price_text = comment_match.group(1).strip()
                if self._is_valid_price(price_text):
                    product['price'] = price_text
                    product['price_source'] = 'comment'
                else:
                    product['price'] = '价格未知'
                    product['price_source'] = 'invalid_comment'
            else:
                product['price'] = '价格未知'
                product['price_source'] = 'no_comment'

        # 提取销量信息
        sale_match = re.search(r'<span[^>]*class="[^"]*sale-num[^"]*"[^>]*>([^<]*)</span>', item_content)
        if sale_match:
            product['sales_count'] = sale_match.group(1).strip()

        # 提取SKU信息
        sku_matches = re.findall(r'data-sku="([^"]*)"', item_content)
        if sku_matches:
            product['skus'] = sku_matches

        # 提取缩略图
        thumb_matches = re.findall(r'<img[^>]*atpanel="[^"]*"[^>]*src="([^"]*)"', item_content)
        if thumb_matches:
            product['thumbnails'] = thumb_matches

        # 提取商品属性
        product['attributes'] = self._extract_attributes(item_content)

        # 添加品牌信息
        product['brand'] = self.brand_name

        return product

    def _extract_attributes(self, item_content):
        """提取商品属性"""
        attributes = {}

        # 查找属性区域
        attr_pattern = r'<div[^>]*class="[^"]*attr[^"]*"[^>]*>.*?</div>'
        attr_matches = re.findall(attr_pattern, item_content, re.DOTALL)

        for attr_content in attr_matches:
            # 提取属性键
            key_match = re.search(r'<div[^>]*class="[^"]*attrKey[^"]*"[^>]*>([^<]*)</div>', attr_content)
            if key_match:
                key = key_match.group(1).strip()

                # 提取属性值
                value_matches = re.findall(r'<a[^>]*>([^<]*)</a>', attr_content)
                if value_matches:
                    attributes[key] = [v.strip() for v in value_matches]

        return attributes

    def save_to_json(self, output_file):
        """保存提取的商品信息到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            logger.info(f"商品信息已保存到: {output_file}")
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            return False

    def generate_summary(self):
        """生成提取结果摘要"""
        if not self.products:
            return f"品牌 {self.brand_name}: 未提取到任何商品信息"

        # 统计价格来源
        price_sources = {}
        for product in self.products:
            source = product.get('price_source', 'unknown')
            price_sources[source] = price_sources.get(source, 0) + 1

        summary = f"""
品牌 {self.brand_name} 提取结果摘要:
=====================================
总商品数量: {len(self.products)}
商品ID列表: {[p.get('product_taobao_id', 'N/A') for p in self.products[:10]]}...
价格来源统计: {price_sources}
标题示例: {[p.get('title', 'N/A')[:50] + '...' if len(p.get('title', '')) > 50 else p.get('title', 'N/A') for p in self.products[:3]]}
        """
        return summary


class BatchBrandProcessor:
    """批量品牌处理器"""

    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.results = {}

    def process_all_brands(self):
        """处理所有品牌文件"""
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 获取所有文本文件
        text_files = list(self.input_dir.glob("*.txt"))
        logger.info(f"找到 {len(text_files)} 个品牌文本文件")

        total_products = 0

        for text_file in text_files:
            try:
                logger.info(f"正在处理品牌: {text_file.stem}")

                # 创建提取器
                extractor = BrandProductExtractor(text_file)

                # 提取商品信息
                # 若目标JSON已存在则跳过
                output_file = self.output_dir / f"{text_file.stem}_products.json"
                if output_file.exists():
                    logger.info(f"目标已存在，跳过: {output_file}")
                    # 记录结果占位（不读取旧文件以节省IO）
                    self.results[text_file.stem] = {
                        'product_count': None,
                        'output_file': str(output_file)
                    }
                    continue

                products = extractor.extract_products()

                if products:
                    # 保存到JSON文件
                    extractor.save_to_json(output_file)

                    # 记录结果
                    self.results[text_file.stem] = {
                        'product_count': len(products),
                        'output_file': str(output_file)
                    }

                    total_products += len(products)

                    # 显示摘要
                    print(extractor.generate_summary())
                else:
                    logger.warning(f"品牌 {text_file.stem} 未提取到任何商品信息")

            except Exception as e:
                logger.error(f"处理品牌 {text_file.stem} 时出错: {e}")
                continue

        return self.results


def main(input_dir, output_dir):
    """主函数"""

    # 显示参数信息
    logger.info("=" * 60)
    logger.info("从raw_text目录提取品牌商品信息脚本")
    logger.info("=" * 60)

    logger.info(f"输入目录: {input_dir}")
    logger.info(f"输出目录: {output_dir}")

    logger.info("=" * 60)

    # 检查输入目录是否存在
    if not Path(input_dir).exists():
        logger.error(f"输入目录不存在: {input_dir}")
        return

    # 创建批量处理器
    processor = BatchBrandProcessor(input_dir, output_dir)

    # 处理所有品牌
    logger.info("开始批量处理品牌数据...")
    results = processor.process_all_brands()

    # 显示总体结果
    print("\n批量处理完成！")
    print(f"共处理 {len(results)} 个品牌")
    print(f"输出目录: {output_dir}")

    if results:
        print("\n各品牌处理结果:")
        for brand, result in results.items():
            print(f"  {brand}: {result['product_count']} 个商品")


if __name__ == "__main__":
    # 以项目根目录为基准
    project_root = Path()

    # 先处理：综合
    input_dir = project_root / f"data/{place_id}/{monthly_type}/raw_text"
    output_dir = project_root / f"data/{place_id}/{monthly_type}/extracted_products_batch"
    main(input_dir, output_dir)

    # # 再处理：新品
    # xinpin_input = project_root / "data/兴业太古汇_新品/raw_text"
    # xinpin_output = project_root / "data/兴业太古汇_新品/extracted_products_batch"
    # main(xinpin_input, xinpin_output)
