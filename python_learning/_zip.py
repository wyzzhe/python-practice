import json

# zip 多个可迭代对象打包成一个迭代器元组
oldUser = ['{"name": "Alice", "age": 25}', '{"name": "Bob", "age": 30}']
oldAssistant = ['{"response": "Hello Alice"}', '{"response": "Hello Bob"}']

zipped = zip(oldUser, oldAssistant)
# print(list(zipped))
# [('你好', '你好啊'), ('我想喝奶茶', '喝沪上阿姨吧'), ('我想吃火锅', '吃巴奴吧')]

"""
    有效的json格式：
    字典{}
    列表[]
"""

for item1, item2 in zipped:
    # str -> dict
    jsonStr = json.loads(item1)
    print(jsonStr)