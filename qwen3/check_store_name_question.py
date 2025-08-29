import json
import requests
import csv

from settings import HISTORY_REDIS_TTL
from utils.context import RedisUserContext
from utils.redis_utils import del_current_intention, redis_client

intentions = [
    "", "food"
]

place_id = 801
user_id = "G1N2J67Qb0IGp111"

filename = "check_store_name.csv"
fieldnames = ["text", "old_intention", "result"]
if __name__ == "__main__":
    url = f"https://guide-admin.aibee.cn/api/get-store?place_id={place_id}"
    apiRes = requests.get(url)
    data = json.loads(apiRes.content.decode())
    apiStoreList = data["data"]
    final_result = []
    global_info = RedisUserContext(place_id=place_id, user_id=user_id)
    for apiStore in apiStoreList:
        for old_intention in intentions:
            s = apiStore["store_name"]
            url = "https://screen.aibee.cn/ai_model/question"
            # url = "https://screen.aibee.cn/mall_ai_model/question"
            headers = {
                "Content-Type": "application/json",
                "token": "G1N2J67Qb0IGp111",
                "session_id": "G1N2J67Qb0IGp111",
            }

            dataDict = {
                "user_input": s,
                "place_id": place_id
            }
            if old_intention == "":
                del_current_intention(place_id, user_id)
            else:
                redis_client.set(f"agent_current_intention:{place_id}_{user_id}", old_intention, ex=HISTORY_REDIS_TTL)
            data = json.dumps(dataDict)
            response = requests.post(url, data=data, headers=headers)
            del_current_intention(place_id, user_id)
            global_info.food_history_user = []
            global_info.food_history_assistant = []
            global_info.historyStoreIDList = []
            global_info.historyStoreType = None
            global_info.exclude_store_list = []
            global_info.old_rewritten_question = None

            res = bytearray()
            for chunk in response:
                res.extend(chunk)
            result = res.decode('utf-8')

            temp_str = result.split('event:finish')[-1]
            data_str = temp_str.split('data:')[-1]
            sendResult = ""
            try:
                data_list = json.loads(data_str)
                for data in data_list:
                    msg = data.get("msg", None)
                    component = data.get("component", None)
                    intention = data.get("intention", None)
                    if msg:
                        sendResult += msg
                    elif component:
                        sendResult += json.dumps(data, ensure_ascii=False)
                    elif intention:
                        sendResult += json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print("JSON 解析失败:", e)
            resDict = {
                "text": s,
                "old_intention": old_intention,
                "result": sendResult
            }
            print(resDict)
            final_result.append(resDict)
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # 写入表头
        writer.writeheader()

        # 写入数据行
        writer.writerows(final_result)

    print(f"数据已成功写入 {filename}")
