import time
import asyncio

def syncDoModelAgent(user_id):
    print(f"用户{user_id}的任务开始(同步)")
    time.sleep(3) # 模拟等待大模型回复
    print(f"用户{user_id}的回复：找到车位在{user_id}区1层")

async def asyncDoModelAgent(user_id):
    print(f"用户{user_id}的任务开始(异步)")
    await asyncio.sleep(3) # 模拟等待大模型回复
    print(f"用户{user_id}的回复：找到车位在{user_id}区1层")

def sync_multi_user():
    start_time = time.time()
    syncDoModelAgent("A")
    syncDoModelAgent("B")
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f}秒\n")

async def async_multi_user():
    start_time = time.time()
    await asyncio.gather(
        asyncDoModelAgent("A"),
        asyncDoModelAgent("B")
    )
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f}秒\n")

sync_multi_user()
asyncio.run(async_multi_user())