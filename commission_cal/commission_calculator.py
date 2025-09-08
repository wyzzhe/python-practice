#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提成计算器
根据销售额计算提成金额
"""

class CommissionCalculator:
    """提成计算器类"""
    
    def __init__(self):
        # 提成规则：[(最小金额, 最大金额, 提成率), ...]
        # 金额单位为元
        self.commission_rules = [
            (0, 100000, 0.01),      # 0-10万元，1%
            (100000, 200000, 0.015),    # 10-20万元，1.5%
            (200000, 300000, 0.02),     # 20-30万元，2%
            (300000, 500000, 0.025),    # 30-50万元，2.5%
            (500000, float('inf'), 0.03),    # 50万元以上，3%
        ]
    
    def calculate_commission(self, sales_amount):
        """
        计算提成金额
        
        Args:
            sales_amount (float): 销售额（元）
            
        Returns:
            dict: 包含详细计算信息的字典
        """
        if sales_amount < 0:
            return {
                'error': '销售额不能为负数',
                'total_commission': 0,
                'breakdown': []
            }
        
        total_commission = 0
        breakdown = []
        remaining_amount = sales_amount
        
        for min_amount, max_amount, rate in self.commission_rules:
            if remaining_amount <= 0:
                break
                
            # 计算当前档位的金额
            if max_amount == float('inf'):
                # 50万元以上的部分，全部按3%计算
                tier_amount = remaining_amount
                tier_commission = tier_amount * rate
                total_commission += tier_commission
                
                breakdown.append({
                    'tier_range': "50万元以上",
                    'amount': tier_amount,
                    'rate': rate,
                    'commission': tier_commission
                })
                
                remaining_amount = 0
            else:
                tier_amount = min(remaining_amount, max_amount - min_amount)
                if tier_amount > 0:
                    tier_commission = tier_amount * rate
                    total_commission += tier_commission
                    
                    breakdown.append({
                        'tier_range': f"{min_amount//10000}-{max_amount//10000}万元",
                        'amount': tier_amount,
                        'rate': rate,
                        'commission': tier_commission
                    })
                    
                    remaining_amount -= tier_amount
        
        return {
            'sales_amount': sales_amount,
            'total_commission': total_commission,
            'breakdown': breakdown,
            'effective_rate': total_commission / sales_amount if sales_amount > 0 else 0
        }
    
    def get_commission_rules(self):
        """获取提成规则"""
        return self.commission_rules


def main():
    """主函数，用于测试"""
    calculator = CommissionCalculator()
    
    # 测试用例（单位：元）
    test_amounts = [50000, 150000, 250000, 400000, 800000, 1200000]
    
    print("提成计算器测试")
    print("=" * 50)
    
    for amount in test_amounts:
        result = calculator.calculate_commission(amount)
        print(f"\n销售额: {amount:,}元 ({amount/10000:.1f}万元)")
        print(f"总提成: {result['total_commission']:,.2f}元 ({result['total_commission']/10000:.4f}万元)")
        print(f"有效提成率: {result['effective_rate']:.2%}")
        print("详细计算:")
        for item in result['breakdown']:
            print(f"  {item['tier_range']}: {item['amount']:,.0f}元 × {item['rate']:.1%} = {item['commission']:,.2f}元")


if __name__ == "__main__":
    main()
