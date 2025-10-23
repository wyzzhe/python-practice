from PIL import Image
import json

# 1. 加载JSON数据和原始图片
with open("C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json\\JORDAN\\analysis\\629b0cc142b6466983de6029155ed4cd_3_f.json", "r", encoding="utf-8") as f:
    data = json.load(f)
original_img = Image.open("C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json\\JORDAN\\images\\629b0cc142b6466983de6029155ed4cd_3_f.jpg")

# 2. 遍历每个商品，根据box切割图片并按is_recommended分类
for product in data["products"]:
    box = product["box"]  # box格式：[x1, y1, x2, y2]
    is_recommended = product["is_recommended"]
    sub_image_path = product["sub_image_path"]
    
    # 切割图片（PIL的crop方法接收(left, top, right, bottom)元组）
    cropped_img = original_img.crop((box[0], box[1], box[2], box[3]))
    
    # 根据is_recommended保存到不同目录（若目录不存在则创建）
    save_dir = "recommended" if is_recommended else "not_recommended"
    import os
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 保存切割后的图片
    cropped_img.save(os.path.join(save_dir, sub_image_path))
    print(f"已保存 {sub_image_path} 到 {save_dir} 目录")