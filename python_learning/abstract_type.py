from abc import ABC, abstractmethod
import math

"""
多人合作开发时, 抽象基类可以防止每个子类的方法名和参数不一致, 即每个人写的函数都不一样, 难以调用
"""

"""
动物抽象基类示例
"""
# 定义抽象基类
class Animal(ABC):
    def __init__(self, name):
        self.name = name # 类的实例的属性 self.name 赋值为 实例化类时向类传入的 name 参数值

    # 定义一个抽象方法, 子类必须实现抽象方法
    @abstractmethod
    def make_sound(self):
        pass

    # 定义一个普通方法, 可以被子类继承
    def eat(self):
        print(f"{self.name} is eating.")

# 定义一个子类继承抽象基类
class Dog(Animal):
    def make_sound(self): # Dog 继承了 Animal, 自动继承了 Animal 的初始化方法, 自动初始化 name 属性
        print(f"{self.name} says: Woof!")

# 定义另一个子类继承抽象基类
class Cat(Animal):
    def make_sound(self):
        print(f"{self.name} says: Meow!")

# 测试代码
dog = Dog("buddy")
dog.make_sound()
dog.eat()

cat = Cat("Whiskeys")

"""
图形抽象基类示例
"""
# 定义一个抽象基类
class Shape(ABC):
    @abstractmethod
    def draw(self):
        """绘制图形"""
        ...

    @abstractmethod
    def area(self):
        """计算图形的面积"""
        ...

# 定义一个矩形类
class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def draw(self):
        print(f"Drawing a rectangle with width {self.width} and height {self.height}")

    def area(self):
        return self.width * self.height

# 定义一个圆形类
class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def draw(self):
        print(f"Drawing a circle with radius {self.radius}")

    def area(self):
        return math.pi * self.radius ** 2

# 测试代码
rectangle = Rectangle(4, 5)
circle = Circle(3)

# 绘制图形并计算面积
shapes = [rectangle, circle]

for shape in shapes:
    # 画图形
    shape.draw()
    # 算面积
    print(f"Area: {shape.area()}")