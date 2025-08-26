import requests
import json
import hashlib
from datetime import datetime

# ==========================================
# 成都SKP停车场车辆查找API调用示例
# ==========================================

# API配置参数
group_id = "HUALIAN_chengdu_skptfpk"       # 停车场分组ID
apiKey = "iew86mtg"                         # API密钥
apiSecret = "3e058bd22c58260ecd3ef1d172a82eec"  # API密钥签名
car_plate = "川ADM641"                      # 要查询的车牌号码

# API端点
url = "https://park-api.aibee.cn/car/v1/app/car-loc"

# 请求体数据
body = {
    "group_id": group_id,    # 停车场分组ID
    "car_plate": car_plate   # 车牌号码
}

# 生成当前时间戳（用于API签名）
timestamp = int(datetime.timestamp(datetime.now()))
print("timestamp =", timestamp)

# 生成API签名
# 签名算法：JSON请求体 + 时间戳 + API密钥
signstr = json.dumps(body) + str(timestamp) + apiSecret
apiSign = hashlib.sha1(signstr.encode('utf-8')).hexdigest()
print("apiSign: ", apiSign)

# 设置请求头
headers = {}
headers["Content-type"] = "application/json"           # 内容类型
headers["Aibee-Auth-ApiKey"] = apiKey                 # API密钥
headers["Aibee-Auth-Sign"] = apiSign                  # API签名
headers["Aibee-Auth-Timestamp"] = str(timestamp)      # 时间戳
headers["group_id"] = group_id                        # 分组ID

# 发送POST请求到车辆定位API
resp = requests.post(url, data=json.dumps(body), headers=headers)

# 输出响应结果
print("resp.code:", resp.status_code, ", resp.text:", resp.text)

# ==========================================
# 响应处理示例
# ==========================================

if resp.status_code == 200:
    # 解析JSON响应
    response_data = resp.json()
    
    # 检查是否找到车辆
    if response_data.get("error_no") == 605:
        print("车辆未找到")
        print(f"错误信息: {response_data.get('error_msg')}")
    else:
        # 车辆找到，处理车辆信息
        car_data = response_data.get("data", {})
        print("车辆信息:")
        print(f"  车牌号: {car_data.get('car_plate')}")
        print(f"  楼层: {car_data.get('floor')}")
        print(f"  车位: {car_data.get('lot')}")
        print(f"  区域: {car_data.get('zone')}")
        print(f"  最后进入时间: {car_data.get('last_in_time')}")
else:
    print(f"API请求失败，状态码: {resp.status_code}") 