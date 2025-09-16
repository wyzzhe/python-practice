# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import time
# import asyncio  # 暂时注释掉，如需要异步功能可取消注释

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
streaming = False
# Non-streaming:
if not streaming:
    print("----- standard request -----")
    non_streaming_start = datetime.now()
    completion = client.chat.completions.create(
        model="doubao-1-5-lite-32k-250115",
        messages=[
            {"role": "system", "content": "你是人工智能助手"},
            {"role": "user", "content": "给我写篇作文"},
        ],
    )
    non_streaming_end = datetime.now()
    non_streaming_spend = non_streaming_end - non_streaming_start
    print(f"non_streaming_spend {non_streaming_spend}")
    print(completion.choices[0].message.content)
    
    # 输出 token 消耗统计
    if hasattr(completion, 'usage') and completion.usage:
        usage = completion.usage
        print("\n=== Token 消耗统计 ===")
        print(f"输入 tokens (prompt_tokens): {usage.prompt_tokens}")
        print(f"输出 tokens (completion_tokens): {usage.completion_tokens}")
        print(f"总 tokens (total_tokens): {usage.total_tokens}")
        if hasattr(usage, 'input_tokens'):
            print(f"输入 tokens (input_tokens): {usage.input_tokens}")
        if hasattr(usage, 'output_tokens'):
            print(f"输出 tokens (output_tokens): {usage.output_tokens}")

# Streaming:
elif streaming:
    print("----- streaming request -----")

    first_delay_time = 0
    rounds = 1  # 修正循环次数
    for i in range(rounds):
        start_time = time.time()
        stream = client.chat.completions.create(
            model="doubao-1-5-lite-32k-250115",
            messages=[
                {"role": "system", "content": "## 你是一个天气查询机器人"},
                {"role": "user", "content": "郑州今天天气怎么样"},
            ],

            # 响应内容是否流式返回
            stream=True,
        )
        first_chunk_time = None
        usage_info = None  # 存储 token 使用信息
        
        for chunk in stream:
            if not chunk.choices:
                continue

            if first_chunk_time is None:
                first_chunk_time = time.time()
                first_delay_time += first_chunk_time - start_time
                if i < 3:
                    print(f"首字延迟 {(first_chunk_time - start_time):.3f}秒")
            
            # 检查是否有内容输出
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
            
            # 检查是否有 usage 信息（通常在最后一个 chunk 中）
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = chunk.usage
                
    print()
    print(f"平均 {rounds} 次首字延迟 {(first_delay_time / rounds):.3f}秒")
    
    # 输出流式请求的 token 消耗统计
    if usage_info:
        print("\n=== 流式请求 Token 消耗统计 ===")
        print(f"输入 tokens (prompt_tokens): {usage_info.prompt_tokens}")
        print(f"输出 tokens (completion_tokens): {usage_info.completion_tokens}")
        print(f"总 tokens (total_tokens): {usage_info.total_tokens}")
        if hasattr(usage_info, 'input_tokens'):
            print(f"输入 tokens (input_tokens): {usage_info.input_tokens}")
        if hasattr(usage_info, 'output_tokens'):
            print(f"输出 tokens (output_tokens): {usage_info.output_tokens}")
    else:
        print("\n注意：流式请求中未获取到 token 使用信息")
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


"""
查天气
"""

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Openai客户端，从环境变量中读取您的API Key
# bot_client = OpenAI(
#     # 此为默认路径，您可根据业务所在地域进行配置
#     base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
#     # 从环境变量中获取您的 API Key
#     api_key=os.environ.get("ARK_API_KEY")
# )

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
# print("----- streaming request -----")
# stream = bot_client.chat.completions.create(
#     model="bot-20250910105252-sqqc5",  # bot-20250910105252-sqqc5 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
#     messages=[
#         {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
#         {"role": "user", "content": "常见的十字花科植物有哪些？"},
#     ],
#     stream=True,
# )
# for chunk in stream:
#     if hasattr(chunk, "references"):
#         print(chunk.references)
#     if not chunk.choices:
#         continue
#     if chunk.choices[0].delta.content:
#         print(chunk.choices[0].delta.content, end="")
# print()