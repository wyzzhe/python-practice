import sys
import os
import json
from datetime import datetime

import pandas as pd
import requests
import csv
from time import sleep

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from settings import HISTORY_REDIS_TTL
from utils.context import RedisUserContext
from utils.redis_utils import del_current_intention, redis_client



questions_list = [
    [
        "我要买男裤",
        "哪家男裤价格划算",
        "导航火锅店"
    ],
    [
        "奶茶店",
        "哪里有福建菜",
        "导航到瑞幸咖啡",
        "虎丫炒鸡"
    ],
    [
        "火锅店",
        "河南特色菜有哪些",
        "哪里有服务台",
        "洗手间在哪"
    ],
    [
        "自助餐厅推荐",
        "我的车哪里了",
        "怎么找我的车",
        "人均消费在50-100的餐厅有哪些"
    ],
    [
        "有没有适合老年人吃的饭店",
        "网红店有哪些",
        "商场Wi-Fi密码是多少",
        "你是哪个公司开发的"
    ],
    [
        "环境好，适合拍照打卡的店有哪些",
        "如何注册会员？",
        "会员积分兑换记录在哪里查？",
        "有哪些值得推荐的餐厅吗"
    ],
    [
        "商场有泡泡玛特吗",
        "如何注册会员？",
        "积分可以兑换什么礼品",
        "劳力士怎么走"
    ],
    [
        "推荐一家火锅店",
        "就去这家吧",
        "清真饭店有吗",
        "OK，这家店在什么位置"
    ],
    [
        "有日料店吗",
        "有哪些值得去的餐厅",
        "不能吃辣，有推荐吗",
        "有哪些值得去的餐厅"
    ],
    [
        "可以带宠物的饭店",
        "适合老人吃的饭店",
        "这家饭店有什么优惠吗",
        "火啫啫有什么优惠活动"
    ],
    [
        "今日风向标-按钮",
        "适合老人吃的饭店",
        "今日风向标-按钮",
    ],
    [
        "哪里可以免费充电",
        "哪里有直饮水",
        "我的车在哪",
        "停车缴费",
    ],
    [
        "哪里租婴儿车",
        "轮椅在哪里领取",
        "你好呀",
        "商场客服电话是多少",
    ],
    [
        "你知道最近的卫生间吗",
        "带我去洗手间",
        "积分能抵现或换现金吗",
        "会员积分会过期吗",
    ],
    [
        "这附近有没有寄存包的地方",
        "导航到服务台",
        "导航至名创优品",
    ],
    [
        "母婴室",
        "礼宾处在哪里",
        "好的",
        "你知道最近的卫生间吗",
    ],
    [
        "你知道最近的卫生间吗",
        "带我去洗手间",
        "带小孩买双儿童鞋",
        "买一台学习机",
    ],
    [
        "化妆室在哪里",
        "有没有医疗箱",
        "商场有什么优惠活动吗",
        "瑞幸咖啡",
    ],
    [
        "寻车缴费",
        "你这么厉害",
        "你是哪个公司开发的呀",
        "那你知道我车停哪里了吗",
    ],
    [
        "停车缴费页面",
        "我还有多少积分",
        "停车场在几层",
    ],
    [
        "停车场在几层",
        "导航到巴奴火锅",
        "我的车停的位置",
        "停车怎么收费",
    ],
    [
        "停车场在几层",
        "我想剪头发",
        "商场哪里可以做面部保养",
        "停车怎么收费",
    ],
    [
        "哪家店今天有活动",
        "长申超市今天有优惠吗",
        "回家找我的车",
        "交停车费",
    ],
    [
        "失恋了，你可以安慰我一下吗",
        "我要买游戏机",
        "会员等级有哪些",
        "怎么才能升级到黄金会员呀",
    ],
    [
        "你都有哪些功能啊",
        "那我想去瑞幸咖啡",
        "你好厉害",
        "哪你知道霸王茶姬在几楼",
    ],
    [
        "该买短袖了",
        "你给我推荐几个潮牌服装店吧",
        "你都有哪些功能呀",
        "哪家店有猫粮",
    ],
    [
        "你好你好",
        "有哪些店今天办活动吗",
        "O'EAT是不是经常有优惠",
    ],
    [
        "查询积分",
        "带我去火锅店消费一波",
        "我的积分可以兑换什么",
    ],
    [
        "带小孩买双儿童鞋",
        "积分能抵现或换现金吗？",
        "有哪些值得去的美食餐厅",
        "会员是否有免排队/专属座位权益？"
    ],
    [
        "哪些店铺有优惠活动",
        "蔡澜点心有什么优惠活动",
        "我想买个手链",
        "哪里卖运动鞋"
    ],
]

place_id = 801
user_id = "G1N2J67Qb0IGp000"

filename = "check_dialogue_question.csv"
fieldnames = ["text", "old_intention", "result"]
if __name__ == "__main__":
    t = datetime.now()
    final_result = []
    global_info = RedisUserContext(place_id=place_id, user_id=user_id)
    for questions in questions_list:
        del_current_intention(place_id, user_id)
        global_info.food_history_user = []
        global_info.food_history_assistant = []
        global_info.historyStoreIDList = []
        global_info.historyStoreType = None
        global_info.exclude_store_list = []
        global_info.old_rewritten_question = None
        text = ""
        response = ""
        for s in questions:
            text += s
            text += "，"
            sleep(5)
            if "按钮" in s:
                url = "https://screen.aibee.cn/mall_ai_model/today_index"  # 正式
                # url = "https://screen.aibee.cn/ai_model/today_index"  # 测试
                headers = {
                    "Content-Type": "application/json",
                    "token": "G1N2J67Qb0IGp000",
                    "session_id": "G1N2J67Qb0IGp000",
                }
                dataDict = {
                    "place_id": place_id
                }
                data = json.dumps(dataDict)
                response = requests.post(url, data=data, headers=headers)
            else:
                url = "https://screen.aibee.cn/mall_ai_model/question"  # 正式
                # url = "https://screen.aibee.cn/ai_model/question" # 测试
                headers = {
                    "Content-Type": "application/json",
                    "token": "G1N2J67Qb0IGp000",
                    "session_id": "G1N2J67Qb0IGp000",
                }

                dataDict = {
                    "user_input": s,
                    "place_id": place_id
                }

                data = json.dumps(dataDict)
                response = requests.post(url, data=data, headers=headers)

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
                "text": text,
                "result": sendResult
            }
            print(resDict)
            final_result.append(resDict)
    # with open(filename, mode='w', newline='', encoding='utf-8') as file:
    #     writer = csv.DictWriter(file, fieldnames=fieldnames)
    #
    #     # 写入表头
    #     writer.writeheader()
    #
    #     # 写入数据行
    #     writer.writerows(final_result)

    # print(f"数据已成功写入 {filename}")
    filename=f'check_dialogue_question_{place_id}_{datetime.now().strftime("%Y%m%d%H")}.xlsx'
    pd.DataFrame(final_result).to_excel(filename)
    print(f"数据已入到文件{filename}")
    print(f"开始时间：{t}")
    print(f"结束时间：{datetime.now()}")
    print(f"耗时：{datetime.now() - t}")


