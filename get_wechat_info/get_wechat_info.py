import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import re
import os

# 配置pytesseract路径（如果是Windows需要配置）
import os
tesseract_path = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def get_wechat_article_content(url):
    """爬取微信公众号文章内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取文章标题
    title = soup.find('h1', id='activity-name')
    title = title.text.strip() if title else '未找到标题'
    
    # 提取文章内容
    content = soup.find('div', class_='rich_media_content')
    content_text = ''
    if content:
        content_text = content.text.strip()
    
    # 提取图片链接
    images = []
    img_tags = content.find_all('img') if content else []
    for img in img_tags:
        img_url = img.get('data-src') or img.get('src')
        if img_url:
            images.append(img_url)
    
    return {
        'title': title,
        'content': content_text,
        'images': images
    }

def download_image(url):
    """下载图片"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    return Image.open(io.BytesIO(response.content))

def ocr_image(image):
    """使用OCR识别图片内容，包含图片预处理步骤"""
    try:
        # 图片预处理
        # 如果是RGBA格式，转换为RGB
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # 转换为灰度图
        gray_image = image.convert('L')
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(2.0)  # 对比度调整倍数
        
        # 应用阈值处理
        threshold_image = enhanced_image.point(lambda x: 0 if x < 128 else 255, '1')
        
        # 应用中值滤波减少噪声
        filtered_image = threshold_image.filter(ImageFilter.MedianFilter(size=3))
        
        # 进行OCR识别，设置Tesseract参数
        # psm 6: Assume a single uniform block of text
        # oem 3: Default OCR Engine Mode (Legacy + LSTM)
        # whitelist: 只识别中文、英文和数字
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ一-龥'
        text = pytesseract.image_to_string(filtered_image, lang='chi_sim+eng', config=custom_config)
        return text
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("Tesseract OCR未安装或路径配置错误，请检查Tesseract是否正确安装并配置环境变量")
        return ""

def extract_activity_info(image_text):
    """从OCR结果中提取活动信息"""
    activity_info = {
        '活动标题': '',
        '活动内容': '',
        '时间': ''
    }
    
    # 提取活动标题 - 寻找可能的标题行（通常是较突出的文本）
    # 尝试匹配包含"派对"、"活动"、"优惠"、"促销"等关键词的行
    title_match = re.search(r'(.+?[派对|活动|优惠|促销|庆典].+?)\n', image_text) or \
                 re.search(r'(.+?\n.+?[派对|活动|优惠|促销|庆典].+?)', image_text) or \
                 re.search(r'(.{10,50})', image_text)  # 提取中间长度的文本作为候选标题
    if title_match:
        activity_info['活动标题'] = title_match.group(1).strip()
    
    # 提取活动内容 - 寻找包含具体信息的文本
    content_match = re.search(r'(.+?[\d\w].+?)', image_text, re.DOTALL) or \
                   re.search(r'(.+?\n.+?)', image_text, re.DOTALL)
    if content_match:
        activity_info['活动内容'] = content_match.group(1).strip()
    
    # 提取日期信息 - 支持多种格式 (e.g., 11.14-11.16, 2025.11.14-11.16, 11/14-11/16)
    date_match = re.search(r'(\d{4}?\.?\d{2}\.\d{2}-\d{2}\.\d{2})', image_text) or \
                 re.search(r'(\d{2}\.\d{2}-\d{2}\.\d{2})', image_text) or \
                 re.search(r'(\d{4}?/?\d{2}/\d{2}-\d{2}/\d{2})', image_text) or \
                 re.search(r'(\d{2}/\d{2}-\d{2}/\d{2})', image_text)
    if date_match:
        activity_info['时间'] = date_match.group(1).strip()
    
    # 提取时间范围信息
    time_match = re.search(r'(\d{2}:\d{2}-\d{2}:\d{2})', image_text)
    if time_match:
        if activity_info['活动内容']:
            activity_info['活动内容'] += ' ' + time_match.group(1).strip()
        else:
            activity_info['活动内容'] = time_match.group(1).strip()
    
    return activity_info

def main():
    # 支持多个URL的列表
    urls = ['https://mp.weixin.qq.com/s/pzRA-ibAIxwNW4ypy56Tlg']
    
    # 创建保存数据的基础目录
    base_dir = 'wechat_data'
    os.makedirs(base_dir, exist_ok=True)
    
    for url in urls:
        print(f'\n\n===== 处理URL: {url} =====')
        
        # 爬取微信文章内容
        article = get_wechat_article_content(url)
        
        # 下载并识别所有图片
        all_activity_info = {
            '活动标题': '',
            '活动内容': '',
            '时间': ''
        }
        
        # 保存提取的文本信息
        title = article['title']
        # 过滤文件名中的非法字符
        sanitized_title = re.sub(r'[\\/:"*?<>|]+', '_', title)
        folder_name = sanitized_title or '未命名文章'
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # 下载并保存所有图片
        images_folder = os.path.join(folder_path, 'images')
        os.makedirs(images_folder, exist_ok=True)
        
        for i, img_url in enumerate(article['images']):
            print(f'\n识别第{i+1}张图片: {img_url}')
            image = download_image(img_url)
            
            # 保存图片
            image_filename = f'image_{i+1:03d}.png'
            image_save_path = os.path.join(images_folder, image_filename)
            image.save(image_save_path)
            print(f'图片已保存: {image_save_path}')
            
            # 进行OCR识别
            text = ocr_image(image)
            print('OCR结果:', text)
            
            # 提取活动信息
            activity_info = extract_activity_info(text)
            if any(activity_info.values()):
                print('提取的活动信息:', activity_info)
                
                # 合并活动信息
                if activity_info['活动标题']:
                    all_activity_info['活动标题'] = activity_info['活动标题']
                
                if activity_info['活动内容']:
                    if all_activity_info['活动内容']:
                        all_activity_info['活动内容'] += ' ' + activity_info['活动内容']
                    else:
                        all_activity_info['活动内容'] = activity_info['活动内容']
                
                if activity_info['时间']:
                    all_activity_info['时间'] = activity_info['时间']
        
        # 如果从图片中提取到标题，使用图片标题作为文章标题
        if all_activity_info['活动标题']:
            article['title'] = all_activity_info['活动标题']
        
        # 保存文本信息到文件
        text_info = f"文章标题: {article['title']}\n"
        text_info += f"文章内容: {article['content']}\n"
        text_info += f"活动信息: {str(all_activity_info)}\n"
        
        with open(os.path.join(folder_path, 'info.txt'), 'w', encoding='utf-8') as f:
            f.write(text_info)
        
        print(f"\n\n最终提取结果已保存到: {folder_path}")
        print(f"文章标题: {article['title']}")
        print(f"文章内容: {article['content']}")
        print(f"活动信息: {all_activity_info}")

if __name__ == '__main__':
    main()