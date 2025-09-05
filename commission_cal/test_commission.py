#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试提成计算器功能
"""

from commission_calculator import CommissionCalculator

def test_commission_calculator():
    """测试提成计算器"""
    calculator = CommissionCalculator()
    
    # 测试用例（单位：元）
    test_cases = [
        (50000, "5万元销售额"),
        (150000, "15万元销售额"),
        (250000, "25万元销售额"),
        (400000, "40万元销售额"),
        (800000, "80万元销售额"),
        (1200000, "120万元销售额"),
        (0, "0元销售额"),
        (-50000, "负数销售额")
    ]
    
    print("提成计算器测试结果")
    print("=" * 60)
    
    for amount, description in test_cases:
        result = calculator.calculate_commission(amount)
        print(f"\n{description}:")
        print(f"  销售额: {amount:,}元 ({amount/10000:.1f}万元)")
        
        if 'error' in result:
            print(f"  错误: {result['error']}")
        else:
            print(f"  总提成: {result['total_commission']:,.2f}元 ({result['total_commission']/10000:.4f}万元)")
            print(f"  有效提成率: {result['effective_rate']:.2%}")
            print("  详细计算:")
            for item in result['breakdown']:
                print(f"    {item['tier_range']}: {item['amount']:,.0f}元 × {item['rate']:.1%} = {item['commission']:,.2f}元")

if __name__ == "__main__":
    test_commission_calculator()
