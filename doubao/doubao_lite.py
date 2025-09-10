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

"""
对话机器人
"""
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
# print("----- streaming request -----")

# first_delay_time = 0
# for i in range(1):
#     start_time = time.time()
#     stream = client.chat.completions.create(
#         model="doubao-1-5-lite-32k-250115",
#         messages=[
#             {"role": "system", "content": "## 你是一个天气查询机器人"},
#             {"role": "user", "content": "郑州今天天气怎么样"},
#         ],

#         # 响应内容是否流式返回
#         stream=True,
#     )
#     first_chunk_time = None
#     for chunk in stream:
#         if not chunk.choices:
#             continue

#         if first_chunk_time is None:
#             first_chunk_time = time.time()
#             first_delay_time += first_chunk_time - start_time
#             if i < 3:
#                 print(f"首字延迟 {(first_chunk_time - start_time):.3f}秒")
#         print(chunk.choices[0].delta.content, end="")
# print()
# print(f"平均 {i} 次首字延迟 {(first_delay_time / 100):.3f}秒")
# print()

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


"""
查天气
"""

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Openai客户端，从环境变量中读取您的API Key
bot_client = OpenAI(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    # 从环境变量中获取您的 API Key
    api_key=os.environ.get("ARK_API_KEY")
)

# Non-streaming:
# print("----- standard request -----")
# completion = bot_client.chat.completions.create(
#     model="bot-20250910105252-sqqc5",  # bot-20250910105252-sqqc5 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
#     messages=[
#         {"role": "system", "content": "你是一个天气查询机器人，根据用户输入的城市如北京市，河南省郑州市查询天气。"},
#         {"role": "user", "content": "郑州2025年9月10日天气"},
#     ],
# )
# print(completion.choices[0].message.content)
# if hasattr(completion, "references"):
#     print(completion.references)


# # Multi-round：
# print("----- multiple rounds request -----")
# completion = bot_client.chat.completions.create(
#     model="bot-20250910105252-sqqc5",  # bot-20250910105252-sqqc5 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
#     messages=[  # 通过会话传递历史信息，模型会参考上下文消息
#         {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
#         {"role": "user", "content": "花椰菜是什么？"},
#         {"role": "assistant", "content": "花椰菜又称菜花、花菜，是一种常见的蔬菜。"},
#         {"role": "user", "content": "再详细点"},
#     ],
# )
# print(completion.choices[0].message.content)
# if hasattr(completion, "references"):
#     print(completion.references)

# Streaming:
print("----- streaming request -----")
stream = bot_client.chat.completions.create(
    model="bot-20250910105252-sqqc5",  # bot-20250910105252-sqqc5 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
    messages=[
        {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
        {"role": "user", "content": "常见的十字花科植物有哪些？"},
    ],
    stream=True,
)
for chunk in stream:
    if hasattr(chunk, "references"):
        print(chunk.references)
    if not chunk.choices:
        continue
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()