# Python基本语法

>  Python里的一切东西都是对象

## 数据类型

### 序列

序列是**有序**的数据集合，支持索引和切片。

- 列表 `[]` 
- 元组 `()`
- 字符串 `""`
- 字节数组 `bytearray(b"")`
- 字节 `b""`
- 数组 `array`
- 集合 `{}` 
- 有序集合 `{"": ""}` 

###   str的本质

不可变的字符序列

### 字面量

被写在代码中的固定的值（整数、浮点数、字符串）

### 列表 List []

Python里的List也是一个对象，只是它包含了其他对象的指针。

**列表函数**

list.append()	尾部插入一个元素

list.extend()	尾部插入迭代器遍历的多个元素

## 作用域

因为 Python 没有块级作用域，只有函数作用域。

## Continue和Break

Continue不执行后续语句，暂时结束本次循环，进入到一下次循环

Break不执行后续语句，结束所有循环

# 面向对象编程

## 继承

**基类（父类）**

init构造函数

**子类**

super()调用父类的方法

子类继承父类方法和属性

子类可以重写父类方法

## python的类

抽象类（接口）

    方法定义（无实现）

具体类

    属性

    方法（具体实现）

## 策略模式

所有关于停车的**方法**都可以封装到一个停车API类中

停车API 类    抽象类    接口

    获取车辆位置    方法定义

    获取停车费        方法定义

    获取导航信息    方法定义

正弘城停车API类    具体类

    获取车辆位置    方法实现1

    获取停车费        方法实现1

    获取导航信息    方法实现1

成都SKP停车API类    具体类

    获取车辆位置    方法实现2

    获取停车费        方法实现2

    获取导航信息    方法实现2

## 工厂模式

创建策略工厂

根据place_id使用策略工厂生产不同的停车API策略，并使用不同的停车API策略



# python调试器

## 特殊变量

缓存 `__cached__` = `None` 

模块、类、函数的文档字符串 `__doc__` = `'\n数据类型\n'` 

```python
"""						 >>>>>>此处有\n
数据类型				>>>>>>此处有\n
"""
```

```python
"""
module docstring
"""

class A:
	"""
	class docstring
	"""
	
	def get_name:
		"""
		func docstring
		"""
```

当前模块文件路径 `__file__`  = `'/Users/aibee/Downloads/python-try/python-practice/python_learning/data_type.py'` 

模块加载器 `__loader__`  = `None` 

模块名 `__name__` =  `'__main__'`  主模块(python命令直接运行的脚本)

> 被引入的模块是'子模块'

模块所属的包 `__package__` = `''` 模块不属于任何包

模块规格信息 `__spec__` = `None`



# Python底层代码

`len(list_tpye)` 

len函数在`builtins.pyi` python类型提示文件里注解函数签名，在底层`Objects/abstract.c` CPython源码文件里实现。

















