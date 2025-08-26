# utils/parking_factory.py
from typing import Dict, Type
from parking_strategy import ParkingStrategy
from parking_strategies import ZhengHongChengStrategy, ChengDuSKPStrategy, NewMallStrategy, AnotherMallStrategy

class ParkingStrategyFactory:
    """停车策略工厂"""

    # 核心/通用商场可以写死，保证主流程稳定。
    # 类型注解 Dict字典 Type类
    _strategies: Dict[int, Type[ParkingStrategy]] = {
        801: ZhengHongChengStrategy, # 正弘城
        702: ChengDuSKPStrategy, # 成都SKP
        # 可以继续添加更多场地
    }

    @classmethod # 类方法，cls为类本身
    def create_strategy(cls, place_id: int) -> ParkingStrategy:
        """根据place_id创建对应的停车策略"""
        strategy_class = cls._strategies.get(place_id) # 调用类本身的属性
        if not strategy_class:
            # 遇到异常时查找except执行异常处理逻辑，未找到程序终止并打印错误信息
            raise ValueError(f"不支持的场ID: {place_id}") 
        return strategy_class() # 调用实例类的构造函数，创建该类的实例

    # 新增/定制/第三方商场建议用注册方式，保证灵活扩展。
    # 即使以后有几十个场地，也不用每次都修改工厂类，只需要在独立文件中动态注册即可
    @classmethod
    def register_strategy(cls, place_id: int, strategy_class: Type[ParkingStrategy]):
        """注册新的策略"""
        cls._strategies[place_id] = strategy_class

# 注册新场地策略
ParkingStrategyFactory.register_strategy(999, NewMallStrategy)
ParkingStrategyFactory.register_strategy(1001, AnotherMallStrategy)