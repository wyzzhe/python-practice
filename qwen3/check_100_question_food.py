import sys
import os
from datetime import datetime

import pandas as pd

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import requests
import csv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from settings import HISTORY_REDIS_TTL
from utils.context import RedisUserContext
from utils.redis_utils import del_current_intention, redis_client

questions = [
    "有日料店吗？",
    "火锅店有哪些推荐的",
    "网红店有哪些",
    "河南特色菜",
    "清真饭店有吗",
    "有没有适合老年人吃的饭店",
    "环境好，适合拍照打卡的店有哪些",
    "带娃来商场吃饭，有适合孩子、安全卫生的餐厅吗？",
    "人均消费在50-100的店铺有哪些",
    "哪个餐厅允许带宠物进入",
    "不能吃辣，有推荐吗",
    "商场有猪肚鸡吗",
    "奶茶店",
    "这里都有啥好吃的推荐呢",
    "瑞幸咖啡在几楼",
    "米村拌饭",
    "劳力士怎么走",
    "周大福在哪",
    "去喜茶",
    "有喜茶吗",
    "喜茶店",
    "霸王茶姬在哪里",
    "带我去附近的星巴克",
    "哪里有名创优品",
    "有没有名创优品",
    "名创优品精品店",
    "商场茶百道的位置",
    "茶百道在一楼吗",
    "商场里有泡泡玛特吗",
    "带我去长申超市",
    "长申超市在商场B1哪个位置",
    "母婴室在哪里",
    "商场哪一层有休息椅",
    "你知道最近的卫生间吗",
    "商场的客服中心在哪里",
    "这附近有没有雨伞租赁处",
    "哪里有婴儿车",
    "哪里可以免费充电",
    "这附近有没有寄存行李的地方",
    "礼宾处在哪里",
    "哪里有直饮水",
    "哪里可以租充电宝",
    "礼品包装处在哪里",
    "哪里可以包扎伤口",
    "化妆室在哪里",
    "从当前位置到最近的电梯口怎么走",
    "轮椅在哪里领",
    "这个停车场怎么缴费啊",
    "用支付宝缴费",
    "在哪里交停车费吗",
    "停车场一小时多少钱",
    "在哪里可以看到我的停车时长",
    "从当前位置到我的车那里怎么走",
    "能不能提前预约停车位",
    "我的车停在哪里了",
    "能帮我定位一下我的车吗",
    "我找不到自己的车了",
    "我记着车位 A001，在哪里",
    "缴费页面",
    "停车一晚上的话咋收费",
    "你是哪个公司开发的",
    "你都有哪些功能啊",
    "你是AI智能体吗",
    "商场的Wi-Fi密码你知道吗",
    "客服电话是多少？",
    "你多大了",
    "能不能给我讲个笑话",
    "王者荣耀和英雄联盟哪个好玩",
    "失恋了，你可以安慰我一下吗",
    "最近有哪些电视剧很火吗",
    "扫码点餐有积分吗？",
    "邀请好友注册得多少积分？",
    "会员都有几级",
    "黄金会员都有那些特权",
    "积分能兑换什么？",
    "我的积分能兑换哪些商品",
    "积分能抵现或换现金吗？",
    "是否有免排队/专属座位权益？",
    "会员积分",
    "会员积分兑换记录在哪里查？",
    "会员积分会过期吗",
    "如何注册会员？",
    "我想买猫粮",
    "我要买电脑",
    "哪里可以买厨具",
    "手机店",
    "哪里可以刮彩票",
    "哪里有超市卖打火机的",
    "我想回收奢侈品",
    "给老人买个颈椎按摩器",
    "去店里看看汽车",
    "去买几条首饰",
    "该买短袖了",
    "我去买条裤子",
    "给对象买钻戒",
    "带小孩买双儿童鞋",
    "买一台学习机",
    "有没有假发卖",
    "我想剪头发",
    "去哪里做面部保养",
]

intentions = [
    "food"
]

place_id = 801
user_id = "G1q3vgHQhy8cZ000"

filename = "check_100_question_food.csv"
fieldnames = ["text", "old_intention", "result"]
if __name__ == "__main__":
    t = datetime.now()
    final_result = []
    global_info = RedisUserContext(place_id=place_id, user_id=user_id)
    for s in questions:
        for old_intention in intentions:
            url = "https://screen.aibee.cn/mall_ai_model/question" # 正式
            # url = "https://screen.aibee.cn/ai_model/question" # 测试
            # url = "https://screen.aibee.cn/demo_ai_model/question" # demo
            headers = {
                "Content-Type": "application/json",
                "token": "G1q3vgHQhy8cZ000",
                "session_id": "G1q3vgHQhy8cZ000",
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
    # with open(filename, mode='a', newline='', encoding='utf-8') as file:
    #     writer = csv.DictWriter(file, fieldnames=fieldnames)
    #
    #     # 写入表头
    #     writer.writeheader()
    #
    #     # 写入数据行
    #     writer.writerows(final_result)

    # print(f"数据已成功写入 {filename}")
    filename= f'check_100_question_food_{place_id}_{datetime.now().strftime("%Y%m%d%H")}.xlsx'
    pd.DataFrame(final_result).to_excel(filename)
    print(f"数据已入到文件{filename}")
    print(f"开始时间：{t}")
    print(f"结束时间：{datetime.now()}")
    print(f"耗时：{datetime.now() - t}")
