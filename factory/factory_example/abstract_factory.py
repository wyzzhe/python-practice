from abc import ABC, abstractmethod

# 抽象产品A
class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

# 抽象产品B
class Food(ABC):
    @abstractmethod
    def eat(self):
        pass

# 具体产品狗狗
class Dog(Animal):
    def speak(self):
        return "汪汪！"

# 具体产品狗粮
class DogFood(Food):
    def eat(self):
        return "吃狗粮"

# 具体产品猫猫
class Cat(Animal):
    def speak(self):
        return "喵喵！"

# 具体产品猫粮
class CatFood(Food):
    def eat(self):
        return "吃猫粮"

# 抽象工厂
class PetFactory(ABC):
    @abstractmethod
    def create_animal(self):
        pass

    @abstractmethod
    def create_food(self):
        pass

# 狗狗相关工厂：制造狗狗和狗粮(产品族)
class DogFactory(PetFactory):
    def create_animal(self):
        return Dog()

    def create_food(self):
        return DogFood()

# 猫猫相关工厂：制造猫猫和猫粮
class CatFactory(PetFactory):
    def create_animal(self):
        return Cat()

    def create_food(self):
        return CatFood()

# 实例化狗狗相关工厂，使用狗狗相关工厂生产狗狗和狗粮
dog_factory = DogFactory()
dog = dog_factory.create_animal()
dog_food = dog_factory.create_food()
print(dog.speak(), dog_food.eat())