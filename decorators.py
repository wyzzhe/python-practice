# newfunc = @decorators(oldfunc())
# 装饰器用于 增加 / 修改 原函数功能

# @装饰器
# 调用 原函数 前执行函数
# 调用 原函数 后执行函数
"""
    内置装饰器
    @staticmethod
    @classmethod
"""

# 类通常大写首字母
class Pizza:
    # 构造方法
    # self 代表实例本身，ingredients 是初始化传入的参数
    def __init__(self, ingredients):
        self.ingredients = ingredients
    
    @classmethod
    # self  是实例引用
    # cls   是类引用
    def margherita(cls):
        return cls(["番茄", "奶酪"])  # 调用__init__
    
    @classmethod
    def prosciutto(cls):
        return cls(["番茄", "奶酪", "火腿"])

# 使用类方法创建不同披萨
p1 = Pizza.margherita()  # 无需知道具体构造细节
p2 = Pizza.prosciutto()

# 实例化披萨
pizza1 = Pizza(["cheese", "tomato"]) # 传入 ingredients
print(pizza1.ingredients) # 输出 ['cheese', 'tomato']
