import requests
import hashlib
import time
import json

# 示例参数
api_key = "iew86mtg"  # 替换为你的实际 Aibee-Auth-ApiKey
api_secret = "3e058bd22c58260ecd3ef1d172a82eec"  # 替换为你的实际 ApiSecret
group_id = "HUALIAN_chengdu_skptfpk"  # 替换为你的实际 group_id

# 生成时间戳
timestamp = int(time.time())

# 请求体
data = {
    "group_id": group_id,
    "floor": "B2"
}

# 将请求体转换为 JSON 格式
request_body = json.dumps(data)

# 拼接字符串
sign_str1 = f"{request_body}{timestamp}{api_secret}"
sign_str2 = request_body + str(timestamp) + api_secret
print("str(timestamp): ", str(timestamp))
print("apiSign: ", sign_str2)

# 生成签名
signature = hashlib.sha1(sign_str2.encode('utf-8')).hexdigest()
print("signature: ", signature)

# 请求头
headers = {
    "Aibee-Auth-ApiKey": api_key,
    "Aibee-Auth-Sign": signature,
    "Aibee-Auth-Timestamp": str(timestamp),
    "group_id": group_id,
    "Content-Type": "application/json"
}

# 发送 POST 请求
# response = requests.post("https://park-api.aibee.cn/car/v1/car/all-cars", headers=headers, json=data)
response = requests.post("http://180.76.96.211:1308/car/v1/lot/basic", headers=headers, json=data)

# 打印响应
print("Response:", response.json())