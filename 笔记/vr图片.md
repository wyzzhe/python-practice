| 字母  | 全称          | 中文方向 | 常用坐标系（OpenGL 风格） |
| ----- | ------------- | -------- | ------------------------- |
| **b** | back          | 后       | +Z（远离观察者）          |
| **d** | down / bottom | 下       | -Y                        |
| **f** | front         | 前       | -Z（朝向观察者）          |
| **l** | left          | 左       | -X                        |
| **r** | right         | 右       | +X                        |
| **t** | top / up      | 上       | +Y                        |



prompt_**vr_pic_to_product**

```
我在做一款商场场景下的ai agent，需要商场里店铺的品牌和商品信
这些图片是vr扫描出来的全景图，在全景图（立方体展开图/Cubemap）里，这六个字母的顺序是标准的 立方体六个面 的缩写，对应关系如下：
表格
复制
字母	全称	中文方向	常用坐标系（OpenGL 风格）
b	back	后	+Z（远离观察者）
d	down / bottom	下	-Y
f	front	前	-Z（朝向观察者）
l	left	左	-X
r	right	右	+X
t	top / up	上	+Y

这是我想获取的商品相关的信息示例：
{'id': '902', 'place_id': 801, 'store_id': 83758, 'third_id': '2011906190001', 'shop_id': 'T_3d5a3b9a-9bda-11e8', 'store_name': '泡泡玛特POPMART', 'commercial': '购物-潮流玩具,礼品', 'phone_number': '13653828002', 'node_id': '2DzHwLKQ7Z', 'floor': 'B1', 'cost': '￥131/人', 'store_image': 'https://prod-deployment.oss-cn-hangzhou.aliyuncs.com/0f3fc0f7669846de90ae905ca9d2afe7_17200f984c094678083d2f04bf18467b.jpeg ', 'score': 4.6, 'description': '泡泡玛特POPMART一进店就被各种可爱潮玩包围，满满少女心💕 店铺风格超酷炫，装修独特，随手一拍都出片📷 他家主打各种盲盒，人气单品多到挑花眼。无论是Molly、Dimoo还是毕奇，每个系列都超有吸引力。不管是学生党还是潮玩爱好者，都能在这里找到心头好，快来泡泡玛特开启惊喜盲盒之旅吧🎉这是一件网红店', 'famous': 1, 'categories': 'Molly, BOBO&COCO, CHAKA, CRYBABY, Dimoo, HACIPUPU, HIRONO, KUBO, LABUBU, LiLiOS, MEGA系列, Nyota, PINO JELLY, POLAR, Peach Riot 叛桃, SKULLPANDA, Zsiga, 三丽鸥, 初音未来, 名侦探柯南, 哈利波特, 哪吒, 天线宝宝, 樱桃小丸子, 毕奇精灵, 周深, 王嘉尔, 间谍过家家, 鬼灭之刃, 魔卡少女樱, 漫威, 迪士尼, 共鸣, 盲盒, 潮玩手办, 手办大娃, 吊卡, 可动人偶, IP周边, 冰箱贴, 徽章, 手机壳, 数据线, 耳机套, 背包收纳, 居家周边, 玩趣挂件, 精致香薰, 联名IP, 时尚数码, 毛绒玩偶', 'products': 'POPMART泡泡玛特CRYBABY SHINY SHINY系列灯潮流时尚周边礼物 | POPMART泡泡玛特CRYBABY SHINY SHINY系列发光挂件盲盒潮流周边 | POPMART泡泡玛特航海王·伟大的航路系列模型载具潮流时尚玩具 | POPMART泡泡玛特DIMOO心动特调系列香包挂件套装七夕礼物 | POPMART泡泡玛特DIMOO心动特调系列咖啡杯家居周边七夕礼物 | POPMART泡泡玛特迪士尼公主创想世界系列手办盲盒潮流玩具礼物 | POPMART泡泡玛特DIMOO心动特调系列盲盒亚克力冰箱贴夹子七夕礼物 | POPMART泡泡玛特周深《反深代词》系列毛绒挂饰潮流时尚周边 | POPMART泡泡玛特共鸣 间谍过家家角色系列毛绒盲盒潮流玩具礼物 | POPMART泡泡玛特MEGA α SKULLPANDA 400% 梵高博物馆·向日葵 | POPMART泡泡玛特ΘSKULLPANDA熊怠怠毛绒公仔挂件潮流时尚周边 | POPMART泡泡玛特星星人好梦气象局系列毛绒挂件盲盒潮流时尚礼物 | POPMART泡泡玛特MEGA SPACE MOLLY 100% 奇奇&蒂蒂潮', 'note': '[{"type": "stream", "data": "**[nav type=ar place_id=801 floor=B1 end_name=泡泡玛特POPMART end_position=2DzHwLKQ7Z ](泡泡玛特POPMART) [phone data=\'13653828002\']() [store_info store_id=83758]()**\\n泡泡玛特POPMART是潮流玩具与礼品店，装修酷炫出片，盲盒人气高，风格潮流，满足年轻群体收藏需求。 "}, {"type": "dict", "data": {"component": {"lang": "en", "action": "gift_list", "list": [{"img": "https://img.alicdn.com/bao/uploaded/i4/2885348004/O1CN01fhKjQz28ztCEfDklu_ !!4611686018427382436-0-item_pic.jpg_180x180.jpg", "name": "POPMART泡泡玛特DIMOO心动特调系列香包挂件套装七夕礼物", "url": ""}, {"img": "https://img.alicdn.com/bao/uploaded/i3/2885348004/O1CN01l52FF428ztCFG2pXR_ !!4611686018427382436-0-item_pic.jpg_180x180.jpg", "name": "POPMART泡泡玛特DIMOO心动特调系列咖啡杯家居周边七夕礼物", "url": ""}, {"img": "https://img.alicdn.com/bao/uploaded/i4/2885348004/O1CN01zz7rej28ztCDZL43b_ !!4611686018427382436-0-item_pic.jpg_180x180.jpg", "name": "POPMART泡泡玛特迪士尼公主创想世界系列手办盲盒潮流玩具礼物", "url": ""}, {"img": "https://img.alicdn.com/bao/uploaded/i1/2885348004/O1CN01Cae1Sm28ztCEP2TmJ_ !!4611686018427382436-0-item_pic.jpg_180x180.jpg", "name": "POPMART泡泡玛特DIMOO心动特调系列盲盒亚克力冰箱贴夹子七夕礼物", "url": ""}, {"img": "https://img.alicdn.com/bao/uploaded/i4/2885348004/O1CN01nbRXv728ztCF28zjE_ !!4611686018427382436-0-item_pic.jpg_180x180.jpg", "name": "POPMART泡泡玛特共鸣 间谍过家家角色系列毛绒盲盒潮流玩具礼物", "url": ""}]}}}, {"type": "dict", "data": {"component": {"lang": "zh", "action": "general_store", "data": [{"place_id": 801, "store_id": 83758, "shop_id": "T_3d5a3b9a-9bda-11e8", "store_name": "泡泡玛特POPMART", "score": 4.6, "cost": "￥131/人", "images": "https://prod-deployment.oss-cn-hangzhou.aliyuncs.com/0f3fc0f7669846de90ae905ca9d2afe7_17200f984c094678083d2f04bf18467b.jpeg ", "commercial": "购物-潮流玩具,礼品", "url": "pages/packageC/pages/shop/shop-detail/shop-detail?shopId=T_3d5a3b9a-9bda-11e8"}]}}}]', 'brand_id': '35', 'created_at': Timestamp('2025-06-22 17:47:52'), 'updated_at': Timestamp('2025-09-16 21:58:07'), '别名': 'Pop Mart'}

请帮我分析图片，看看可以提取出来哪些有用的信息
```

