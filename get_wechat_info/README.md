# 微信公众号内容爬取与OCR识别工具

## 功能介绍

该工具用于爬取微信公众号文章内容，并使用OCR技术识别文章中的图片，提取结构化的活动信息。

## 依赖安装

```bash
pip install requests beautifulsoup4 pillow pytesseract
```

## Tesseract OCR 安装

### Windows系统安装步骤：
1. 访问Tesseract GitHub Release页面：https://github.com/UB-Mannheim/tesseract/wiki
2. 下载最新版本的Windows安装程序（推荐下载带有"w64-setup"的版本）
3. 运行安装程序，选择安装简体中文语言包
4. 安装完成后，将Tesseract安装目录添加到系统环境变量PATH中
   - 默安装路径：C:\Program Files\Tesseract-OCR
5. 验证安装：在命令行中运行 `tesseract --version`

### 环境变量配置

如果Tesseract安装在非默认路径，可以通过设置环境变量`TESSERACT_CMD`指定路径：

```bash
set TESSERACT_CMD="D:\Tools\Tesseract-OCR\tesseract.exe"
```

## 使用方法

直接运行脚本即可：

```bash
python get_wechat_info.py
```

## 功能说明

1. **爬取微信文章**：获取指定微信公众号文章的标题、内容和所有图片链接
2. **下载图片**：下载文章中的指定图片
3. **OCR识别**：使用Tesseract OCR识别图片内容
4. **信息提取**：从OCR结果中提取活动标题、活动内容和时间信息

## 输出示例

```
文章标题: 7周年，营业时间调整
文章内容: 25团50/50团1007周年半价美味等你来打卡
图片数量: 60

识别第1张图片: https://mmecoa.qpic.cn/sz_mmecoa_png/...
OCR结果: 星光7遇派对已经开场...
提取的活动信息: {'活动标题': '星光7遇派对', '活动内容': '营业时间调整10:00-22:30', '时间': '11.14-11.16'}
```

## 注意事项

- 请确保网络连接正常，能够访问微信公众号文章
- Tesseract OCR必须正确安装并配置环境变量
- OCR识别准确率受图片质量影响，建议使用清晰的图片