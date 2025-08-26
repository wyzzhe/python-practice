# tools/parking.py
from factory import parking
from factory.parking_factory import ParkingStrategyFactory

@tool
async def find_car(place_id: int, session_id: str):
    """查找用户车辆"""
    ctx = RedisRequestContext(place_id=place_id, session_id=session_id)
    sender = SendService(ctx.str_random_uuid)

    # 1. 获取对应的停车策略
    try: # 不同场的返回的停车策略不一样
        parking_strategy = ParkingStrategyFactory.create_strategy(place_id)
    except ValueError as e:
        sender.sendMsg(f"暂不支持该场地的停车查询: {e}")
    
    # 2. 提取车牌号
    plate = extract_plate(ctx.user_input)

    # 3. 查询用户绑定的车牌
    car_plate_list = []
    if plate is None:
        member_info = ShopApiClient.get_member_info(ctx.user_id)
        if member_info is not None:
            plates = member_info.get("carPlateList", [])
            for item in plates:
                car_plate_list.append(item.get("carPlate"))
    else:
        car_plate_list = [plate]

    # 4. 查询所有车牌的停车信息
    parking_info_list = []

    for item_plate in car_plate_list:
        # 使用策略模式调用对应的API，已获取具体场的停车策略，直接调用即可
        fee_info = await parking_strategy.get_parking_fee(item_plate)

        if fee_info.get("error") is None and fee_info.get("resCode") == 0:
            parking_info = {
                "place_id": place_id,
                "car_no": item_plate,
                "parking_space_no": "",
                "area_name": "",
                "floor_name": "",
                "parking_time": time_since_str(fee_info.get("inTime", "")),
                "parking_fee": fen_to_yuan(fee_info.get("chargeMoney", "")),
                "end_floor": "",
                "end_position": "",
                "end_name": ""
            }
            
            # 查询车辆位置信息
            if parking_info["parking_fee"] != "":
            # 使用策略模式调用对应的API，已获取具体场的停车策略，直接调用即可
                nav_info = await parking_strategy.get_nav_info(item_plate)
                if nav_info.get("error") is None and nav_info.get("error_no") == 0:
                    info = nav_info.get("data", {})
                    parking_info["end_floor"] = info.get("floorName", "")
                    parking_info["end_position"] = info.get("spaceNo", "")
                    parking_info["end_name"] = parking_info["end_floor"] + "-" + parking_info["end_position"]
            
            parking_info_list.append(parking_info)

    # 5. 处理结果
    if len(parking_info_list) == 0:
        # 没有找到停车信息
        prompt, model = getPrompt(place_id, "findCarResult", {})
        await doModelAgent(model, [], [], [], prompt, ctx.user_input, True, place_id, session_id, sender)
    else:
        # 有停车信息，统一由AI处理
        promptName = "findCarMultiResult" if len(parking_info_list) > 1 else "findCarResult"
        prompt, model = getPrompt(place_id, promptName, {"car_list": parking_info_list})
        await doModelAgent(model, [], [], [], prompt, ctx.user_input, True, place_id, session_id, sender)
    
    del_current_intention(place_id, ctx.user_id)
    return True

