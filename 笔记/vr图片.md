# vr全景图to店铺分析工作流

## 提示词

```
你是一名「商场数字孪生」视觉解析专家。

任务：仅依据图像内容，返回一段合法 JSON，包含每个商品的「视觉区域（bounding box）」和「子图路径」，尽可能详细填充所有可见信息，禁止无故留空。JSON 字段如下：

{
"products": [ // 商品数据（每个商品需包含视觉区域 + 子图路径）
{
"name": "", // 商品名称
"colors": [], // 可见颜色：必须填写所有可见主色（如 ["白","深蓝","红"]）
"materials": [], // 可见材质：必须根据外观判断填写（如 ["皮革","合成革","织物"]）
"type": "", // 商品类型：必须填写最具体类型（如" 篮球鞋 "而非" 运动鞋 "，" 卫衣 "而非" 上衣 "）
"is_recommended": false, // 是否显眼摆放（展台 / 独立展示台视为显眼）
"box": [0, 0, 0, 0], // 商品视觉区域：[左上角 x, 左上角 y, 右下角 x, 右下角 y]（像素坐标，需根据图像实际位置估算）
"sub_image_path": ""// 子图路径：格式为"product_序号.jpg"（序号从 1 开始，与 products 数组索引 + 1 一致）
}
],
"store_env": { // 店铺环境（同前）
"style": "", // 可见风格（如工业 / 极简 / 科技等）
"lighting": "", // 光线类型（暖光 / 冷光 / 混合，禁止留空）
"space_m2": null, // 估算面积（取整），无法估算留 null
"special_areas": { // 特殊区域
"fitting_room": 0, // 试衣间数量
"full_length_mirror": 0, // 全身镜数量
"lounge_seats": 0 // 休息区座位数
},
"display_method": [], // 陈列方式（如展台 / 挂杆 / 层板等）
"activities": [ // 活动数据（同前）
{
"poster_image": "", // 海报裁剪图（base64，≤200 KB）
"name": "", // 活动名称（OCR 原文）
"date_range": "", // 时间原文
"content": "" // 优惠内容（OCR 原文）
}
]
},
"note": "" // 其他高价值信息（如品牌联名标识等）
}

规则（必须严格遵守）：

所有可见信息必须填写，禁止无故留空：
materials：根据外观判断填写（如皮革 / 织物 / 合成革）；
lighting：必须填写（暖光 / 冷光 / 混合）；
type：填写最具体类型（如篮球鞋而非运动鞋）；
box：需根据图像中商品的实际位置估算像素坐标（左上角 x,y，右下角 x,y）。示例：若商品在图像左上角，宽高约 100x100，则 box 为[10, 10, 110, 110]；
sub_image_path：格式为"product_序号.jpg"，序号从 1 开始（如第 1 个商品为"product_1.jpg"，第 2 个为"product_2.jpg"，依此类推）。
未出现的信息留空字符串 / 空数组 / 0/null；
文字必须为 OCR 原文，不得改写；
同一商品多色 / 多材质拆分为多个对象；
输出仅返回合法 JSON，无额外解释。
```

## 1.图生文（图片产生店铺、商品信息）

### 如何获取爆品

vr单点位多商品图识别结果**is_recommended=true**的认为是爆品



### 1.vr单点位多商品图识别

**Doubao-Seed-1.6-vision**：数据包括

商品：name/colors/materials/type/is_recommended

店铺：style/lighting/space_m2/special_areas/display_method

```
{
    "products": [
        {
            "name": "Jordan黑色圆领卫衣",
            "colors": [
                "黑"
            ],
            "materials": [
                "织物"
            ],
            "type": "圆领卫衣",
            "is_recommended": true,
            "box": [
                190,
                270,
                400,
                555
            ],
            "sub_image_path": "product_1.jpg"
        },
        {
            "name": "Jordan红色圆领卫衣",
            "colors": [
                "红"
            ],
            "materials": [
                "织物"
            ],
            "type": "圆领卫衣",
            "is_recommended": true,
            "box": [
                390,
                360,
                585,
                630
            ],
            "sub_image_path": "product_2.jpg"
        },
        {
            "name": "Jordan黑色双肩背包",
            "colors": [
                "黑",
                "灰"
            ],
            "materials": [
                "织物",
                "合成革"
            ],
            "type": "双肩背包",
            "is_recommended": true,
            "box": [
                635,
                240,
                765,
                400
            ],
            "sub_image_path": "product_3.jpg"
        },
        {
            "name": "Jordan篮球",
            "colors": [
                "棕红",
                "黑",
                "白"
            ],
            "materials": [
                "橡胶"
            ],
            "type": "篮球",
            "is_recommended": true,
            "box": [
                835,
                330,
                925,
                400
            ],
            "sub_image_path": "product_4.jpg"
        },
        {
            "name": "Jordan红色篮球鞋",
            "colors": [
                "红",
                "白",
                "灰"
            ],
            "materials": [
                "合成革",
                "橡胶"
            ],
            "type": "篮球鞋",
            "is_recommended": true,
            "box": [
                845,
                455,
                930,
                500
            ],
            "sub_image_path": "product_5.jpg"
        },
        {
            "name": "Jordan折叠休闲装",
            "colors": [
                "黑",
                "红",
                "黄"
            ],
            "materials": [
                "织物"
            ],
            "type": "折叠卫衣",
            "is_recommended": true,
            "box": [
                630,
                475,
                770,
                510
            ],
            "sub_image_path": "product_6.jpg"
        },
        {
            "name": "Jordan灰色棒球帽",
            "colors": [
                "灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "棒球帽",
            "is_recommended": true,
            "box": [
                480,
                690,
                540,
                755
            ],
            "sub_image_path": "product_7.jpg"
        },
        {
            "name": "Jordan黑色篮球鞋",
            "colors": [
                "黑",
                "白",
                "红"
            ],
            "materials": [
                "合成革",
                "橡胶"
            ],
            "type": "篮球鞋",
            "is_recommended": true,
            "box": [
                460,
                825,
                565,
                890
            ],
            "sub_image_path": "product_8.jpg"
        },
        {
            "name": "Jordan黑色运动长裤",
            "colors": [
                "黑"
            ],
            "materials": [
                "织物"
            ],
            "type": "运动长裤",
            "is_recommended": true,
            "box": [
                260,
                610,
                375,
                995
            ],
            "sub_image_path": "product_9.jpg"
        },
        {
            "name": "Jordan浅灰色连帽卫衣",
            "colors": [
                "浅灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                580,
                570,
                710,
                900
            ],
            "sub_image_path": "product_10.jpg"
        },
        {
            "name": "Jordan浅灰色连帽卫衣",
            "colors": [
                "浅灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                650,
                575,
                740,
                910
            ],
            "sub_image_path": "product_11.jpg"
        },
        {
            "name": "Jordan浅灰色连帽卫衣",
            "colors": [
                "浅灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                710,
                575,
                770,
                920
            ],
            "sub_image_path": "product_12.jpg"
        },
        {
            "name": "Jordan浅灰色连帽卫衣",
            "colors": [
                "浅灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                740,
                575,
                790,
                930
            ],
            "sub_image_path": "product_13.jpg"
        },
        {
            "name": "Jordan浅灰色连帽卫衣",
            "colors": [
                "浅灰"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                770,
                575,
                820,
                940
            ],
            "sub_image_path": "product_14.jpg"
        },
        {
            "name": "Jordan红色连帽卫衣",
            "colors": [
                "红"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                850,
                575,
                910,
                900
            ],
            "sub_image_path": "product_15.jpg"
        },
        {
            "name": "Jordan红色连帽卫衣",
            "colors": [
                "红"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                880,
                575,
                940,
                905
            ],
            "sub_image_path": "product_16.jpg"
        },
        {
            "name": "Jordan红色连帽卫衣",
            "colors": [
                "红"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                910,
                575,
                970,
                910
            ],
            "sub_image_path": "product_17.jpg"
        },
        {
            "name": "Jordan红色连帽卫衣",
            "colors": [
                "红"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                940,
                575,
                990,
                915
            ],
            "sub_image_path": "product_18.jpg"
        },
        {
            "name": "Jordan黑色连帽卫衣",
            "colors": [
                "黑"
            ],
            "materials": [
                "织物"
            ],
            "type": "连帽卫衣",
            "is_recommended": true,
            "box": [
                960,
                575,
                999,
                920
            ],
            "sub_image_path": "product_19.jpg"
        }
    ],
    "store_env": {
        "style": "极简",
        "lighting": "冷光",
        "space_m2": null,
        "special_areas": {
            "fitting_room": 0,
            "full_length_mirror": 0,
            "lounge_seats": 0
        },
        "display_method": [
            "挂杆",
            "层板",
            "展台"
        ],
        "activities": []
    },
    "note": "所有商品均为Jordan品牌（带Jumpman标志），陈列于运动服饰店铺，主打篮球相关装备。"
}
```



### 2.单个商品图识别

#### 1.图片分割

- ~~**doubao-seedream**图生图：会把侧面的图片展示成正面，但是文字会扭曲，图片会有些ai生成的部分。~~
- **meta-segment-everything**: 毛刺较多，可以网页一键分割。

分割出来的图片可以用于ai agent **小图**展示，放大之后毛刺较多。

```
Meta 官方的 Segment Anything（SAM）在线 Demo 本身完全免费，但注意下面几点：
1. 网页版 https://segment-anything.com/demo 目前仍由 Meta 承担算力，无需注册、不限次数、不收费。
2. 如果要把 SAM 接入自己的业务（调 API、批量跑图），Meta 并没有官方云端 API，需要你自己部署。此时只产生 你自己的服务器/显卡成本，3. 模型权重和源码依旧 0 元。
市面上出现的“SAM 接口”第三方平台（Replicate、Hugging Face Inference API、AWS Marketplace 等）会收 GPU 时长费，价格 0.1–0.6 美元/千张不等，那是服务商的计费，和 Meta 无关。
```

#### 2.商品图识别

**Doubao-Seed-1.6-vision**：数据包括name/colors/materials/type

```
{
    "products": [
        {
            "name": "红色圆领卫衣",
            "colors": [
                "红色"
            ],
            "materials": [
                "织物"
            ],
            "type": "卫衣",
            "is_recommended": false
        },
        {
            "name": "黑色圆领卫衣",
            "colors": [
                "黑色"
            ],
            "materials": [
                "织物"
            ],
            "type": "卫衣",
            "is_recommended": false
        },
        {
            "name": "黑色双肩背包",
            "colors": [
                "黑色"
            ],
            "materials": [
                "织物"
            ],
            "type": "双肩背包",
            "is_recommended": false
        },
        {
            "name": "黑红白配色篮球鞋",
            "colors": [
                "黑色",
                "白色",
                "红色"
            ],
            "materials": [
                "合成革",
                "织物"
            ],
            "type": "篮球鞋",
            "is_recommended": false
        },
        {
            "name": "红灰配色篮球鞋",
            "colors": [
                "红色",
                "灰色"
            ],
            "materials": [
                "合成革",
                "织物"
            ],
            "type": "篮球鞋",
            "is_recommended": false
        },
        {
            "name": "黑色棒球帽",
            "colors": [
                "黑色"
            ],
            "materials": [
                "织物"
            ],
            "type": "棒球帽",
            "is_recommended": false
        }
    ],
    "store_env": {
        "style": "",
        "lighting": "",
        "space_m2": null,
        "special_areas": {
            "fitting_room": 0,
            "full_length_mirror": 0,
            "lounge_seats": 0
        },
        "display_method": [
            "挂杆",
            "层板"
        ],
        "activities": []
    },
    "note": "所有商品均带有 Jordan 品牌标志"
}
```

















