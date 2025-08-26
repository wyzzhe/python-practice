from datetime import datetime
from typing import overload
from pandas._typing import IntStrT
import mock_asyncio
from pandas.core.base import PandasObject # 从 module (文件 / 文件夹) 中引入 类
from pandas.core import indexing # 从 module (文件 / 文件夹) 中引入 module (文件 / 文件夹)

# 父类
# (PandasObject, indexing.IndexingMixin) 多重继承
# IndexingMixin 是 indexing 的嵌套类
class NDFrame(PandasObject, indexing.IndexingMixin): # 多重继承
    def fillna():
        ...

# 子类 继承父类所有方法
class DataFrame(NDFrame): # DataFrame 可以.引用 NDFrame 的 fillna 函数
    ...

class GenFoodShopNote:
    def __init__(self, place_id):
        self.place_id = place_id # self 定义类属性

    async def gen_one_shop(self, store):
        print(f"调用ai生成任务{store}")
        print(f"场id:{self.place_id}") # self 访问类属性

    async def run(self): # self 是实例, 用于访问类的属性和方法
        print("开始执行店铺文案生成任务")
        for i in range(1, 6): # 生成五次
            store = []
            self.gen_one_shop(store) # self 访问类方法

        print("结束执行店铺文案生成任务")


@overload # 重载, 提供不同函数签名, 支持不同的参数组合
def read_excel(sheet_name: str) -> DataFrame: # 读取单个工作表, 返回 DataFrame
    ... # 重载无具体执行

@overload
def read_excel(sheet_name: list[IntStrT]) -> dict[IntStrT, DataFrame]: # 读取多个工作表, 返回 工作表名称: DataFrame
    ...

# 函数具体实现, 处理两个重载
def read_excel(sheet_name: str | list[IntStrT]) -> DataFrame | dict[IntStrT, DataFrame] :
    if isinstance(sheet_name, (str | int)): # sheet_name 的数据类型是 str 或 int 则为 True
        print(sheet_name)

if __name__ == '__main__':
    print(f"开始执行:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # asyncio.run() 把_异步函数的协程对象_放到事件循环里等待执行
    mock_asyncio.run(GenFoodShopNote(801).run()) # 异步 run() 不会立即执行, 而是返回一个协程对象

    read_excel()
    read_excel("")
    read_excel([])

    print(f"结束执行:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")