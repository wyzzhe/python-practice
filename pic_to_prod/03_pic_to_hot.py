from PIL import Image
import json
import os

def crop_products(original_img_path, products_json_path, output_dir="cropped"):
    """
    根据商品的box裁剪图片，并关联is_recommended状态
    :param original_img_path: 原始图片路径（如 "original.jpg"）
    :param products_json_path: 商品JSON文件路径（包含box和is_recommended）
    :param output_dir: 裁剪后子图的输出目录
    :return: 包含子图路径、is_recommended、box的匹配结果列表
    """
    # 1. 读取原始图片和JSON数据
    try:
        original_img = Image.open(original_img_path)
        with open(products_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            products = data.get("products", [])
    except Exception as e:
        print(f"读取文件失败：{e}")
        return []

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    match_results = []  # 保存裁剪结果和is_recommended的匹配关系
    img_width, img_height = original_img.size  # 原始图片尺寸

    for idx, product in enumerate(products):
        # 提取商品信息
        box = product.get("box", [0, 0, 0, 0])
        is_rec = product.get("is_recommended", False)
        sub_path = product.get("sub_image_path", f"product_{idx+1}.jpg")
        sub_path = os.path.join(output_dir, sub_path)  # 拼接输出路径

        # 2. 处理box坐标（防止越界）
        x1, y1, x2, y2 = box
        # 确保坐标在图片范围内
        x1 = max(0, min(x1, img_width))
        y1 = max(0, min(y1, img_height))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        # 确保x1 < x2，y1 < y2（避免无效裁剪）
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        box = (x1, y1, x2, y2)

        # 3. 裁剪并保存子图
        try:
            if x1 < x2 and y1 < y2:  # 有效裁剪区域
                cropped_img = original_img.crop(box)
                cropped_img.save(sub_path)
                print(f"成功裁剪：{sub_path} (box: {box})")
            else:
                print(f"无效裁剪区域（跳过）：{box}")
                continue

            # 4. 记录匹配结果
            match_results.append({
                "sub_image_path": sub_path,
                "is_recommended": is_rec,
                "original_box": product.get("box", []),  # 原始box坐标
                "name": product.get("name", "")  # 商品名称（可选）
            })
        except Exception as e:
            print(f"裁剪失败（商品：{product.get('name', '未知')}）：{e}")

    # 5. 保存匹配结果到JSON
    with open("match_results.json", "w", encoding="utf-8") as f:
        json.dump(match_results, f, indent=2)

    return match_results


if __name__ == "__main__":
    # ---------- 配置参数 ----------
    original_img_path = "C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json\\JORDAN\\images\\629b0cc142b6466983de6029155ed4cd_3_f.jpg"       # 原始图片路径（替换为你的图片）
    products_json_path = "C:\\Users\\wyz\\Desktop\\dev-2025\\python-practice\\pic_to_prod\\panorama_json\\JORDAN\\analysis\\629b0cc142b6466983de6029155ed4cd_3_f.json"     # 商品JSON路径（替换为你的JSON）
    output_dir = "cropped_products"          # 裁剪后子图的输出目录

    # ---------- 执行裁剪 ----------
    results = crop_products(
        original_img_path=original_img_path,
        products_json_path=products_json_path,
        output_dir=output_dir
    )

    print(f"\n共裁剪 {len(results)} 个商品，结果已保存到 match_results.json")