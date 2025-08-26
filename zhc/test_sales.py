import hashlib
import json
from datetime import datetime
import requests

class ZhengHongChengApi:
    def __init__(self, server_url, app_key, app_secret):
        self.server_url = server_url
        # 相当于公钥    app_key <-> app_secret 对应，不同的'公私钥对'用于标识不同的被许可的客户端，适用于多客户端管理
        self.app_key = app_key
        # 相当于私钥    客户端和服务器都知道 app_secret, 传输者不知道 app_secret, 无法伪造请求，服务器拿app_key去找对应的app_secret
        self.app_secret = app_secret

    def get_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def build_sign(self, params: dict) -> str:
        # 按照 key 升序排列
        sorted_keys = sorted(params.keys())
        param_string = ''.join(f"{k}{params[k]}" for k in sorted_keys)

        # 拼接 secret + 参数 + secret
        source = f"{self.app_secret}{param_string}{self.app_secret}"
        print(f"加密前 ===> {source}")
        return self.md5_encrypt(source).upper()

    @staticmethod
    def md5_encrypt(text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def post(self, method_name: str, data: dict):
        # 构建基础参数
        params = {
            "name": method_name,
            # 发送请求时记录时间戳，服务器接收到请求时如果时间戳过期，则返回响应超时
            "timestamp": self.get_time(),
            "version": "1.0",
            "app_key": self.app_key,
            "data": json.dumps(data, separators=(',', ':')) # json 本质就是个字符串，字典可以转换成json，{'name': 'Alice', 'age': 20} -> '{"name": "Alice", "age": 20}'
        }

        # 添加签名
        params["sign"] = self.build_sign(params)

        print("===== 请求参数 =====")
        print(json.dumps(params, indent=2, ensure_ascii=False))

        # 发起 POST 请求（form 表单方式）
        """
        Get:  请求                -> url参数: 表单     key1=value1&key2=value2
        Post: 少量参数             -> body:   表单     key1=value1&key2=value2
              大量 / 结构化 参数    -> body:   JSON    {"key1": "value1", "key2": "value2"}
        """
        response = requests.post(self.server_url, data=params)
        print("===== 响应内容 =====")
        print(response.text)
        try:
            return response.json()
        except json.JSONDecodeError:
            print("返回内容不是合法 JSON")
            return {"error": "Invalid JSON", "content": response.text}

ZhengHongChengApiClient = ZhengHongChengApi(
    # 正式
    server_url= "https://jw-api.zhcommerce.cn/api",
    app_key="A134YDn8dDixVmNE7p9q",
    app_secret="f280f6632aff408563805a7eed6a1b75",
    # 测试
    # server_url= "http://test.jwsaas.cn:58081/api",
    # app_key="ZXzwVaNA2DCwNZD5YmzA",
    # app_secret="56055e8b68657fe273e1d4f6ba8d3c21",
)

page = 1
PAGE_SIZE = 10
res = ZhengHongChengApiClient.post('order.store.record.list', {'pageNumber': page, 'pageSize': PAGE_SIZE, 'storeId': '1132031823854047232'})
# res = ZhengHongChengApiClient.post('store.list', {'pageNumber': page, 'pageSize': PAGE_SIZE})
print("-----------------------------------------")
# print(res['data']['list'][1])