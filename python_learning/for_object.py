from typing import List
from abc import ABC, abstractmethod

def add(x, y):
    return x + y

# 函数 赋给 变量
sum = add

class multi:
    ...

# 类 赋给 类型
time = multi

# 定义一个类, 继承'列表'类, 列表元素类型为字符串
class SuperList(List[str]):
    ...
