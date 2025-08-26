class Pizza:
    def __init__(self, ingredients):
        self.ingredients = ingredients
    
    def margherita(self):
        return Pizza(["番茄", "奶酪"])  # 调用__init__
    
    def prosciutto(self):
        return Pizza(["番茄", "奶酪", "火腿"])

# 使用普通方法创建不同披萨
# p1 = Pizza.margherita()  # 这会报错，因为 margherita 是普通方法，不能直接通过类名调用
# p2 = Pizza.prosciutto()  # 这也会报错