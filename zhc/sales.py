import requests
import hashlib
import hmac
import time

# 测试地址
url = "http://test.jwsaas.cn:58081/api"

# 测试参数
app_key = "ZXzwVaNA2DCwNZD5YmzA"
secret = "56055e8b68657fe273e1d4f6ba8d3c21"
store_id = "880165027498299392"

# 正确的签名函数
def generate_sign(params, secret):
    """
    正确的签名生成函数 - 使用HMAC-SHA256
    格式: secret + key1value1 + key2value2 + ... + secret
    """
    # 过滤掉空值参数
    filtered_params = {k: v for k, v in params.items() if v is not None and v != ''}
    
    # 按key升序排列
    sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])
    
    # 构建签名字符串
    sign_string = secret
    for key, value in sorted_params:
        sign_string += key + str(value)
    sign_string += secret
    
    # 使用HMAC-SHA256加密
    sign = hmac.new(
        secret.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return sign

# 系统参数
system_params = {
    "app_key": app_key,
    "name": "order.store.record.list",
    "version": "1.0",
    "format": "JSON",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
}

# 应用参数
app_params = {
    "pageSize": 10,  # 改为10，这是最大允许值
    "pageNumber": 1,
    "storeId": store_id,
}

# 合并所有参数
all_params = {**system_params, **app_params}

# 生成签名
signature = generate_sign(all_params, secret)
all_params["sign"] = signature

# 打印请求参数，方便调试
print("请求参数:")
for key, value in all_params.items():
    print(f"  {key}: {value}")

print(f"\n生成的签名: {signature}")

# 发送请求 - 使用data=而不是json=
try:
    """
    data=表单数据
    json=JSON数据
    headers=请求头
    timeout=请求超时时间
    params=?后面拼接的查询参数
    auth=认证
    allow_redirects=允许重定向
    verify=禁用SSL验证
    proxies=代理
    """
    response = requests.post(
        url, 
        data=all_params,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    
    print(f"\nHTTP状态码: {response.status_code}")
    print("响应内容:", response.json())
    
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")