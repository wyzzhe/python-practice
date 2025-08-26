"""
数据类型
"""

# 判断类型
print(isinstance(1, int))

# 数字
a = 10
b = 3.5
c = 2 + 3j

print(a)
print(b)
print(c)
print(c.real, c.imag)

# 字符串
s = "hello world"
print(s.upper())
print(s.lower())
print(s[0]) # h
print(s[-1]) # d
print(s[0:5]) # hello

# 列表
nums = [1, 2, 3, 4]
list1 = ['a']
list2 = [[]]
a = 'a'
print(nums[0])
nums.append(5)
print(nums)
nums[1] = 99
print(nums)

# 元组
t = (1, 2, 3)
print(t[0])

# 字典
person = {"name": "Alice", "age": 25}
print(person["name"])
person["age"] = 26
person["city"] = "Beijing"
print(person)

# 集合
s = {1, 2, 3, 3, 2}
print(s) # 自动去重 -> {1, 2, 3}
s.add(4)
s.remove(2)
print(s)
len(s)

int(3.0)

type(3.0)