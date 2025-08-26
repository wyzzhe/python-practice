import requests
import json
import hashlib
from datetime import datetime

group_id = "HUALIAN_chengdu_skptfpk"       #填写上自己的group_id
apiKey = "iew86mtg"           #填写上自己的apiKey
apiSecret = "3e058bd22c58260ecd3ef1d172a82eec" #填写上自己的apiSecret
car_plate = "辽A66D6J"

url = "https://park-api.aibee.cn/car/v1/app/car-loc"
# url = "https://park-api.aibee.cn/car/v1/car/all-cars"
body = {"group_id":group_id, "car_plate":car_plate}
# body = {"group_id":group_id, "floor":"NB1F"}

timestamp = int(datetime.timestamp(datetime.now()))
print("timestamp =", timestamp)

signstr = json.dumps(body) + str(timestamp) + apiSecret
apiSign = hashlib.sha1(signstr.encode('utf-8')).hexdigest()
print("apiSign: ", apiSign)

headers = {}
headers["Content-type"] = "application/json"
headers["Aibee-Auth-ApiKey"] = apiKey
headers["Aibee-Auth-Sign"] = apiSign
headers["Aibee-Auth-Timestamp"] = str(timestamp)
headers["group_id"] = group_id

resp = requests.post(url, data=json.dumps(body), headers=headers)

print("resp.code:", resp.status_code, ", resp.text:", resp.text)