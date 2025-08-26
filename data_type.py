# keyword
"""
    False
    None
    True
    and
    as
    assert
    async
    await
    break
    class
    continue
    def
    del
    elif
    else
    except
    finally
    for
    from
    global
    if
    import
    in
    is
    lambda
    nonlocal
    not
    or
    pass
    raise
    return
    try
    while
    with
    yield
"""
num1 = 1
num2 = True
num3 = 1.23
num4 = 1 + 2j

str1 = r"this is a line with \n"
str2 = "this is a line with \n"


# 列表 | 内存连续存储  |  元素有序，类型可以不同，可变
t = ['a', 123] # print: 'a' 123

# 元组 | 元素类型可以不同，不可变
tuple = ('abc', 123) # print: 123 'abc'

# 集合 | 基于哈希表   |  元素无序，可变，唯一
set = {"abc", 123}

# 字典 | 基于哈希表   |  键唯一
dict = {'a': 1, 'b': 2}

string_type = type("黑马程序员")
int_type = type(666)
float_type = type(3.14)

int_change = int(3.14)
float_change = float(3)
str_change = str(1)
print("qqq%3.4f" % 3.34564, float_change, str_change)

for item in ["string", 123]:
    print(item)

nums = range(5)
for item in nums:
    print(item)

for i in range(5):
    print(i)

print(i)

def say_hi():
    return None

none_type = type(say_hi())

test_i = 1
print(test_i)
test_i = "2"
print(test_i)
test_i = None
print(test_i)
test_i = type(say_hi())
print(test_i)

num = 200 # [全局作用域]全局变量
def test_a():
    num = 500 # [局部作用域]局部变量
    pass

def test_b():
    global num
    num = 500 # [局部作用域]局部变量
    pass

test_a()
test_b()
