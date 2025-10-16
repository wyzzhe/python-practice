# 导航

意图识别 0.78s

数据检索 1.75s 可优化

店铺匹配 5.89s 可优化

![image-20251014151759253](C:\Users\wyz\AppData\Roaming\Typora\typora-user-images\image-20251014151759253.png)

![image-20251014161417652](C:\Users\wyz\AppData\Roaming\Typora\typora-user-images\image-20251014161417652.png)

![image-20251014161426583](C:\Users\wyz\AppData\Roaming\Typora\typora-user-images\image-20251014161426583.png)

为您找到店铺啦。[store_id]|||[nav type={type} place_id=732 floor={floor} end_name={name} end_position={node_id}] 位于【{floor}】

为您找到以下店铺，您看看要去哪一家呢？[store_id1,store_id2]|||1.[nav type={type1} place_id=732 floor={floor1} end_name={name1} end_position={node_id1}] 位于【{floor1}】；2.[nav type={type2} place_id=732 floor={floor2} end_name={name2} end_position={node_id2}] 位于【{floor2}】



原先：

https://open.feishu.cn/open-apis/bot/v2/hook/cedf1eea-f238-4bc4-9921-54da199f9b86

2fB6ItLNAFde1gysESGL3g

现在：

https://open.feishu.cn/open-apis/bot/v2/hook/edfbf489-b32e-45c9-b990-0e4f0b67aae3

A0QWAvn6KLm8Ke17jxk1ge



获取店铺列表

​	豆包知识库召回十个内容

​	问题：带我去lv

​	召回：0.39 * 3 (相关) , 0.36 * 7 (无关)	`DoubaoRetriever` 

​	切片：取前4条数据

​	<u>别名：收集这4条数据的别名</u>	`getDocPrompt`

​		优化点：用python处理，而不是大模型处理，提速**1.5s**

​	匹配店铺：从这4条数据中选择最相关的3条	`matchStore` 

​		优化点：？？？耗时**11.5s**



获取店铺导航信息



导航到店铺



timeout=6s 保证无论是否成功都在17s内返回数据



# 科大讯飞

中英识别大模型

​	pcm, 60s内音频实时返回文字结果。支持中英文+方言

​	免费：20万次, 并发50

​	2300：100万次, 并发50

​	5050：250万次, 并发50

​	16500：1000万次, 并发30

方言识别大模型

​	 pcm, 60s内音频。支持中英文+方言

​	免费：5万次, 并发2

​	2500：50万次, 并发10

​	6750：150万次, 并发15

​	18500：500万次, 并发30

录音文件转写大模型

​	wav, 非实时返回文字结果。支持中英文+方言

​	免费：50小时

​	198：80小时

​	4000：2000小时

实时语音转写大模型

​	pcm, 即将不限时长? 实时返回文字结果。支持中英文+方言

​	免费：50小时

​	198：40小时

​	4000：1000小时





# AibeeAiAgent自建表

### 用户表

`user_id`  

​	正弘城：G2GJV8RPoUh35wLd

​	其他场：user_mgrprfq3_j4nyq8

`user_open_id` 

`created_at` 

### 商场表

`place_id`

`place_name` 



### 车牌表

`plate_id` 

`plate_number` 

​	川A12345



### 用户-商场-车牌关联

`id` 自增

`user_id  ` G2GJV8RPoUh35wLd / user_mgrprfq3_j4nyq8

`place_id` 801 / 720 / 726 / 837

`plate_number` 川A12345

`created_at`

联合索引 `user_id, place_id, plate_number`



### 工作流

第一次找车

agent识别到车牌川A12345，川A23456

查数据库

​	没有 -> 存入数据库



第二次找车

车牌来源：

​	1 用户输入

​	2 用户绑定

​	3 历史记忆

​			查数据库

​				有 -> 车牌川A12345，川A23456 添加到agent

对以上车牌去重

agent识别到新的车牌川A99999

查数据库

​	有 -> 忽略

​	没有 -> 存入数据库

agent识别到车牌川A12345，川A23456



第一次：

用户输入车牌：京A12345

car_plate_list = [京A12345]



用户没输入车牌：查会员库：津A12345, 黑A12345

car_plate_list = [津A12345, 黑A12345]



mia数据库

car_plate_list =  [京A12345] / [津A12345, 黑A12345]



第二次：

用户输入车牌：京A23456

car_plate_list = [京A23456]



用户没输入车牌：查会员库：津A12345, 黑A12345

car_plate_list = [津A12345, 黑A12345]



mia数据库

car_plate_list =  [京A12345, 京A23456]

​							[京A12345, 津A12345, 黑A12345]

​							[津A12345, 黑A12345, 京A23456]

​							[津A12345, 黑A12345]





