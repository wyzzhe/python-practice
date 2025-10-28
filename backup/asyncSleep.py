import time
import threading
import asyncio

# def sleep_sync(duration):
#     print(f"Sleeping for {duration} seconds")
#     time.sleep(duration)
#     print(f"Done sleeping for {duration} seconds")

# thread = threading.Thread(target=sleep_sync, args=(5,)) # 单独线程执行睡5s
# thread.start()

# print("Main thread is doing something else")
# thread.join()  # 等待线程完成
# print("Thread finished")

async def sleep_async(duration, name):
    print(f"{name} is sleeping for {duration} seconds")
    await asyncio.sleep(duration)
    print(f"{name} is done sleeping for {duration} seconds")

async def main():
    start = time.time()
    task2 = asyncio.create_task(sleep_async(5, "Task2"))
    task1 = asyncio.create_task(sleep_async(3, "Task1"))

    print("Main coroutine is doing something else")
    await task1
    await task2
    print("Coroutine finished")
    end = time.time()
    print(f"{end - start:.2f}")

asyncio.run(main())