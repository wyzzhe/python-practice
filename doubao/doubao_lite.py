# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from dotenv import load_dotenv
import time
import asyncio

load_dotenv()

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Openai客户端，从环境变量中读取您的API Key
client = OpenAI(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 从环境变量中获取您的 API Key
    api_key=os.environ.get("ARK_API_KEY"),
)

# # Non-streaming:
# print("----- standard request -----")
# completion = client.chat.completions.create(
#     model="doubao-1-5-lite-32k-250115",
#     messages=[
#         {"role": "system", "content": "你是人工智能助手"},
#         {"role": "user", "content": "你好"},
#     ],
# )
# print(completion.choices[0].message.content)

# Streaming:
print("----- streaming request -----")

first_delay_time = 0
for i in range(0,100):
    start_time = time.time()
    stream = client.chat.completions.create(
        model="doubao-1-5-lite-32k-250115",
        messages=[
            {"role": "system", "content": "## 你是一个设施匹配的机器人，根据用户输入，匹配用户需要找的设施，并返回设施对应的id。如果用户输入并非设施，也不与设施功能相关，则返回数字-2\n\n## 设施功能与场景关联说明\n- 洗手间：解决如厕、洗手需求\n- 母婴室：解决婴儿护理、哺乳需求\n- 医用急救箱：解决伤口处理（如包扎、消毒）、突发身体不适（如头晕、轻微外伤）等医疗相关需求\n- 礼品包装处：仅用于礼品包装，与身体护理无关\n- 其他设施：按名称直接匹配功能（如“充电宝租赁”对应租借充电宝需求）\n\n## 设施和设施id对应关系\n洗手间:4303\n母婴室:4306\n服务台:4307\n大屏:4327\n礼宾处:4347\n自动存包处:4372\n公共休闲椅:4373\n女神百宝箱:4374\n共享童车:4375\n雨伞租赁:4377\n医用急救箱:4378\n轮椅/婴儿车/宠物车:4379\n化妆室:4380\n车辆服务:4381\n充电宝租赁:4382\n礼品包装处:4383\n直饮水处:4384\n免费充电处:4385\n扶梯:4304\n直梯:4305\n电梯口:4305\n存包柜:4372\n\n## 返回规则\n1 用户输入不是设施相关，也不与设施功能与场景相关，返回-2\n2 用户输入属于设施或设施功能场景相关，但未匹配到设施时，返回-1\n3 匹配到相关设施时，返回设备对应id\n4 返回格式：只返回一个数字，不允许返回任何其他内容\n\n# 示例1:\n输入：母婴室怎么走\n返回：4306\n\n# 示例2:\n输入：哪有公共休闲椅\n返回：4373\n\n# 示例3:\n输入：消防栓怎么走\n返回：-1\n\n# 示例4:\n输入：星巴克有什么优惠吗？\n返回：-2"},
            {"role": "user", "content": "导航去最近的星巴克"},
        ],

        # 响应内容是否流式返回
        stream=True,
    )
    first_chunk_time = None
    for chunk in stream:
        if not chunk.choices:
            continue

        if first_chunk_time is None:
            first_chunk_time = time.time()
            first_delay_time += first_chunk_time - start_time
            if i < 3:
                print(f"首字延迟 {(first_chunk_time - start_time):.3f}秒")
        print(chunk.choices[0].delta.content, end="")
print(f"平均 {i} 次首字延迟 {(first_delay_time / 100):.3f}秒")
print()

# # 异步调用
# async def main() -> None:
#     stream = await client.chat.completions.create(
#         model="doubao-1-5-lite-32k-250115",
#         messages=[
#             {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
#             {"role": "user", "content": "常见的十字花科植物有哪些？"},
#         ],
#         stream=True
#     )
#     async for completion in stream:
#         print(completion.choices[0].delta.content, end="")
#     print()

# asyncio.run(main())