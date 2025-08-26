import requests
import pandas as pd
import numpy as np
import aiohttp
import asyncio
import matplotlib.pyplot as plt

# requests
response = requests.get("https://www.baidu.com")
if response.status_code == 200:
    print("请求成功！")
    try:
        print(response.json())
    except Exception as e:
        print(e)
else:
    print(f"请求失败，状态码：{response.status_code}")

# pandas
data = {"名字": ["Alice", "Bob", "Charlie"], "年龄": [25, 30, 35]}
df = pd.DataFrame(data)
print(df)

arr = np.array([1, 2, 3, 4, 5])

mean = np.mean(arr)
print(f"数组：{arr}")
print(f"平均值：{mean}")

async def fetch_data():
    async with aiohttp.ClientSession() as session: # with as 自动释放 session 资源
        async with session.get("https://www.baidu.com") as response: # with as 自动释放 response 资源
            if response.status == 200:
                data = await response.json()
                print("请求成功！")
                print(data)
            else:
                print(f"请求失败，状态码：{response.status}")

# 运行异步函数
asyncio.run(fetch_data()) # 把函数放入事件循环等待运行

# 数据
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]

# 绘制折线图
plt.plot(x, y, marker="o")
plt.title("简单折线图")
plt.xlabel("X 轴")
plt.ylabel("Y 轴")
plt.grid(True)
plt.show()