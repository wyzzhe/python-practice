# 从 abc 模块中导入 ABC类 和 abstractmethod函数，此时直接使用 ABC 即可
from abc import ABC, abstractmethod

# 产品接口
# ABC 是一个抽象类，不能被实例化，只能被继承，定义接口规范，子类实现特定方法
class Animal(ABC):
    @abstractmethod
    # 抽象方法，声明但未实现
    def speak(self):
        pass

# 具体产品
class Dog(Animal):
    # 重写speak方法
    def speak(self):
        return "汪汪！"

class Cat(Animal):
    # 重写speak方法
    def speak(self):
        return "喵喵！"

# 缺点：添加新产品需要修改工厂类，违反开闭原则
# 简单动物工厂：根据输入动物类型生产狗狗和猫猫
class AnimalFactory:
    @staticmethod # 静态方法，不需要实例化类就能调用
    def create_animal(animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        else:
            raise ValueError("Unknown animal type")

# 直接使用动物工厂生产狗狗
dog = AnimalFactory.create_animal("dog")
print(dog.speak())