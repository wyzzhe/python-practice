# utils/parking_strategy.py
from abc import ABC, abstractmethod
from typing import Dict, Any

# 抽象类相当于接口
# 抽象基类，不能被直接实例化，必须被子类继承并实现抽象方法
# 调用类时只关心抽象类名，而不关心具体子类名，对外调用方式统一
class ParkingStrategy(ABC):
    """停车策略接口"""

    # 核心：不同子类对暴露的方法名和参数一致
    @abstractmethod # 抽象方法，子类必须实现
    async def get_parking_fee(self, plate: str) -> Dict[str, Any]:
        """获取停车费信息"""
        pass

    @abstractmethod
    async def get_nav_info(self, plate: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def find_car(self, plate: str) -> Dict[str, Any]:
        pass