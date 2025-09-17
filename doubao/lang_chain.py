from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import asyncio
from openai import APITimeoutError
import time

load_dotenv()

"""
    普通非流式调用  chat.invoke()
    普通流式调用    chat.stream()
    链式非流式调用        chain.invoke()
    批量非流式调用  chat.batch()
    异步非流式调用  await chat.ainvoke()
    异步流式调用    async chat.astream()

"""

try:
    llm_mode = "stream"
    first_token_time = None

    chat = ChatOpenAI(
        temperature=0,
        model="doubao-1.5-lite-32k-250115",
        openai_api_key=os.environ.get("ARK_API_KEY"),
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        streaming=True,
        timeout=100, # 首token超时时间
        max_retries=1, # 最大重试次数
    )

    # 系统消息
    system_message = SystemMessage(content="你是人工智能助手，给我回二十遍'我爱你'并且带编号")

    # 用户消息
    human_message = HumanMessage(content="")

    # AI回复消息
    ai_message = AIMessage(content="你好！我是AI助手...")

    # 用于构造上下文
    history=[
        system_message,
        human_message,
        # ai_message, 
    ]

    start = time.time()

    if llm_mode == "stream":
        for chunk in chat.stream(history):
            if not first_token_time:
                first_token_time = time.time()- start
                print(f"首字时间：{first_token_time}")
                print("-------------------------------------")
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="")
    elif llm_mode == "non_stream":
        response = chat.invoke(history)
        print(response.content)
        if hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})
            print(f"Token使用: {token_usage}")
            print("----------------------------------")
        print(time.time()- start)
    elif llm_mode == "batch":
        questions = ["什么是机器学习？", "什么是深度学习？"]
        messages_list = [
            [SystemMessage(content="请简洁回答"), HumanMessage(content=q)]
            for q in questions
        ]

        responses = chat.batch(messages_list)
        # 非首token
        print(time.time()- start)
        for response in responses:
            print(response.content)
    elif llm_mode == "chain":
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个{role}, 请用{style}的风格回答"),
            ("human", "{question}")
        ])

        output_parser = StrOutputParser()
        chain = prompt | chat | output_parser

        result = chain.invoke({
            "role": "编程导师",
            "style": "简洁专业", 
            "question": "Python中如何实现单例模式？"
        })

        print(result)






except APITimeoutError as e:
    print(time.time()- start)
    print(e)