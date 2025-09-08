print("# 序列类型")
print("## 列表")
for item in [1, 2, 3]:
    print(item)

print("## 元组")
for item in (1, 2, 3):
    print(item)

print("## 字符串")
for item in "hello":
    print(item)

print("## 范围")
for item in range(5):
    print(item)

print("# 集合类型")
print("## 集合")
for item in {1, 2, 3}:
    print(item)

print("## 字典")
print("键")
for key in {"a":1, "b": 2}:
    print(key)
print("值")
for value in {"a":1, "b": 2}.values():
    print(value)
print("键值对")
for key, value in {"a":1, "b":2}.items():
    print(key, value)

print("文件对象")
with open("file.txt", "r") as f:
    for line in f:
        print(line.rstrip('\n'))