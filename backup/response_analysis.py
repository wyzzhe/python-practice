# ==========================================
# 停车场车辆查找API响应数据分析
# ==========================================

# 原始API响应数据（车辆未找到的情况）
original_response = {
    "data": {
        "car_plate": "",           # 车牌号码 - 空值表示未找到车辆
        "group": "",               # 停车场分组 - 当前停车场标识
        "floor": "",               # 楼层信息 - 如B1、B2、L1等
        "lot": "",                 # 停车位编号 - 具体车位号
        "lot_display_name": "",    # 车位显示名称 - 用户友好的车位描述
        "zone": "",                # 停车区域 - 停车场内的区域划分
        "lot_group": "",           # 车位分组 - 车位所属的分组
        "last_position": None,     # 最后位置 - 车辆GPS坐标（经纬度）
        "last_in_time": "",        # 最后进入时间 - 车辆进入停车场的时间
        "last_update_time": 0,     # 最后更新时间 - Unix时间戳
        "time_difference": 0,      # 时间差 - 当前时间与最后更新的时间差（秒）
        "velocity": None,          # 车辆速度 - 如果车辆在移动时的速度
        "candidate_cars": [],      # 候选车辆 - 可能匹配的车辆列表
        "image_url": "",           # 图像URL - 车辆照片链接
        "status": 0,               # 状态码 - 0=未找到，1=已找到
        "image_1": "",             # 图像1 - 车辆照片1
        "image_2": "",             # 图像2 - 车辆照片2
        "image_3": ""              # 图像3 - 车辆照片3
    },
    "error_msg": "car not exist",  # 错误消息 - 车辆不存在的提示
    "error_no": 605,              # 错误代码 - 605表示车辆未找到
    "request_id": "354a1c25-2fb8-4ce5-a4c0-d5ee39febcdd"  # 请求ID - 唯一标识符
}

# ==========================================
# 响应状态分析
# ==========================================

def analyze_response(response_data):
    """分析API响应数据"""
    print("=" * 60)
    print("停车场车辆查找API响应分析")
    print("=" * 60)
    
    # 检查响应状态
    error_no = response_data.get("error_no")
    error_msg = response_data.get("error_msg")
    
    print(f"错误代码: {error_no}")
    print(f"错误消息: {error_msg}")
    print(f"请求ID: {response_data.get('request_id')}")
    print()
    
    # 分析车辆数据
    car_data = response_data.get("data", {})
    
    if error_no == 605:
        print("❌ 车辆未找到")
        print("可能的原因:")
        print("  - 车牌号码输入错误")
        print("  - 车辆已离开停车场")
        print("  - 车辆不在当前停车场")
        print("  - 系统数据同步延迟")
    else:
        print("✅ 车辆已找到")
        print("车辆详细信息:")
        print(f"  车牌号: {car_data.get('car_plate')}")
        print(f"  楼层: {car_data.get('floor')}")
        print(f"  车位: {car_data.get('lot')}")
        print(f"  区域: {car_data.get('zone')}")
        print(f"  最后进入时间: {car_data.get('last_in_time')}")
        print(f"  状态: {'在线' if car_data.get('status') == 1 else '离线'}")
    
    print("=" * 60)

# ==========================================
# 字段详细说明
# ==========================================

def print_field_descriptions():
    """打印字段详细说明"""
    print("\n字段详细说明:")
    print("-" * 40)
    
    fields = {
        "car_plate": "车牌号码，用于标识特定车辆",
        "group": "停车场分组标识，区分不同的停车场",
        "floor": "停车场楼层，如B1（地下1层）、B2（地下2层）",
        "lot": "具体停车位编号，如A-001、B-002等",
        "lot_display_name": "停车位显示名称，用户友好的描述",
        "zone": "停车区域，停车场内的区域划分",
        "lot_group": "车位所属的分组，用于车位管理",
        "last_position": "车辆最后GPS位置坐标",
        "last_in_time": "车辆最后进入停车场的时间",
        "last_update_time": "数据最后更新的Unix时间戳",
        "time_difference": "当前时间与最后更新的时间差（秒）",
        "velocity": "车辆移动速度（如果车辆在移动）",
        "candidate_cars": "可能匹配的候选车辆列表",
        "image_url": "车辆照片的URL链接",
        "status": "车辆状态：0=未找到，1=已找到",
        "error_msg": "错误消息描述",
        "error_no": "错误代码：605=车辆未找到",
        "request_id": "请求唯一标识符，用于追踪请求"
    }
    
    for field, description in fields.items():
        print(f"{field:20}: {description}")

# 执行分析
if __name__ == "__main__":
    analyze_response(original_response)
    print_field_descriptions() 