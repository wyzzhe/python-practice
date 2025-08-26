from abc import ABC, abstractmethod

# 产品接口
class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

# 具体产品
class Dog(Animal):
    def speak(self):
        return "汪汪！"

class Cat(Animal):
    def speak(self):
        return "喵喵！"

# 缺点：每增加一个产品就要增加一个工厂类
# 抽象工厂接口
class AnimalFactory(ABC):
    @abstractmethod
    def create_animal(self):
        pass

# 狗狗工厂：生产狗狗
class DogFactory(AnimalFactory):
    def create_animal(self):
        return Dog()

# 猫猫工厂：生产猫猫
class CatFactory(AnimalFactory):
    def create_animal(self):
        return Cat()

# 实例化狗狗工厂，使用狗狗工厂生产狗狗
dog_factory = DogFactory()
dog = dog_factory.create_animal()
print(dog.speak())