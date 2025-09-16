from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import asyncio
from openai import APITimeoutError
import time

load_dotenv()

try:
    stream_print = True
    first_token_time = None

    chat = ChatOpenAI(
        temperature=0,
        model="doubao-1.5-lite-32k-250115",
        openai_api_key=os.environ.get("ARK_API_KEY"),
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        streaming=False,
        timeout=100, # 首token超时时间
        max_retries=1, # 最大重试次数
    )

    # 系统消息
    system_message = SystemMessage(content="你是人工智能助手")

    # 用户消息
    human_message = HumanMessage(content="给我写篇作文")

    # AI回复消息
    ai_message = AIMessage(content="你好！我是AI助手...")

    messages=[
        system_message,
        human_message,
        # ai_message,
    ]

    start = time.time()

    if stream_print:
        for chunk in chat.stream(messages):
            if not first_token_time:
                first_token_time = time.time()- start
                print(first_token_time)
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="")
    else:
        response = chat.invoke(messages)
        print(response.content)
        print(time.time()- start)

except APITimeoutError as e:
    print(time.time()- start)
    print(e)