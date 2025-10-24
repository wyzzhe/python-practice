#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
店铺数据对比脚本
对比stores_202510241428.csv与美食店铺801.csv+通识店铺801.csv中的店铺数据
"""

import pandas as pd
import os

def load_csv_data():
    """加载CSV数据"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件路径
    stores_file = os.path.join(current_dir, 'stores_202510241428.csv')
    food_file = os.path.join(current_dir, '美食店铺801.csv')
    general_file = os.path.join(current_dir, '通识店铺801.csv')
    
    # 读取stores_202510241428.csv
    print("正在读取stores_202510241428.csv...")
    try:
        stores_df = pd.read_csv(stores_file, encoding='utf-8')
    except:
        stores_df = pd.read_csv(stores_file, encoding='gbk')
    print(f"stores_202510241428.csv 包含 {len(stores_df)} 条记录")
    
    # 读取美食店铺801.csv
    print("正在读取美食店铺801.csv...")
    try:
        food_df = pd.read_csv(food_file, encoding='utf-8', on_bad_lines='skip')
    except:
        food_df = pd.read_csv(food_file, encoding='gbk', on_bad_lines='skip')
    print(f"美食店铺801.csv 包含 {len(food_df)} 条记录")
    
    # 读取通识店铺801.csv
    print("正在读取通识店铺801.csv...")
    try:
        general_df = pd.read_csv(general_file, encoding='utf-8', on_bad_lines='skip')
    except:
        general_df = pd.read_csv(general_file, encoding='gbk', on_bad_lines='skip')
    print(f"通识店铺801.csv 包含 {len(general_df)} 条记录")
    
    return stores_df, food_df, general_df

def extract_store_names(df, name_column='store_name'):
    """提取店铺名称并去重"""
    if name_column in df.columns:
        # 去除空值和重复值
        names = df[name_column].dropna().unique()
        return set(names)
    else:
        print(f"警告: 未找到列 '{name_column}'")
        return set()

def compare_stores():
    """对比店铺数据"""
    # 加载数据
    stores_df, food_df, general_df = load_csv_data()
    
    # 提取店铺名称
    print("\n提取店铺名称...")
    stores_names = extract_store_names(stores_df, 'store_name')
    food_names = extract_store_names(food_df, 'store_name')
    general_names = extract_store_names(general_df, 'store_name')
    
    print(f"stores_202510241428.csv 去重后店铺数量: {len(stores_names)}")
    print(f"美食店铺801.csv 去重后店铺数量: {len(food_names)}")
    print(f"通识店铺801.csv 去重后店铺数量: {len(general_names)}")
    
    # 合并美食店铺和通识店铺
    combined_names = food_names.union(general_names)
    print(f"美食店铺+通识店铺 合并后去重数量: {len(combined_names)}")
    
    # 找出stores_202510241428独有的店铺
    stores_only = stores_names - combined_names
    print(f"\nstores_202510241428 独有的店铺数量: {len(stores_only)}")
    
    # 找出美食店铺+通识店铺独有的店铺
    combined_only = combined_names - stores_names
    print(f"美食店铺+通识店铺 独有的店铺数量: {len(combined_only)}")
    
    # 找出共同的店铺
    common_stores = stores_names.intersection(combined_names)
    print(f"共同的店铺数量: {len(common_stores)}")
    
    # 准备输出内容
    output_lines = []
    
    # 输出详细结果
    output_lines.append("\n" + "="*80)
    output_lines.append("详细对比结果")
    output_lines.append("="*80)
    
    if stores_only:
        output_lines.append(f"\n📋 stores_202510241428 独有的店铺 ({len(stores_only)}个):")
        output_lines.append("-" * 50)
        for i, name in enumerate(sorted(stores_only), 1):
            output_lines.append(f"{i:3d}. {name}")
    else:
        output_lines.append("\n📋 stores_202510241428 没有独有的店铺")
    
    if combined_only:
        output_lines.append(f"\n🍽️ 美食店铺+通识店铺 独有的店铺 ({len(combined_only)}个):")
        output_lines.append("-" * 50)
        for i, name in enumerate(sorted(combined_only), 1):
            output_lines.append(f"{i:3d}. {name}")
    else:
        output_lines.append("\n🍽️ 美食店铺+通识店铺 没有独有的店铺")
    
    if common_stores:
        output_lines.append(f"\n🤝 共同的店铺 ({len(common_stores)}个):")
        output_lines.append("-" * 50)
        for i, name in enumerate(sorted(common_stores), 1):
            output_lines.append(f"{i:3d}. {name}")
    
    # 统计信息
    output_lines.append("\n" + "="*80)
    output_lines.append("统计摘要")
    output_lines.append("="*80)
    output_lines.append(f"stores_202510241428.csv 总店铺数: {len(stores_names)}")
    output_lines.append(f"美食店铺801.csv 总店铺数: {len(food_names)}")
    output_lines.append(f"通识店铺801.csv 总店铺数: {len(general_names)}")
    output_lines.append(f"美食店铺+通识店铺 合并后总数: {len(combined_names)}")
    output_lines.append(f"stores_202510241428 独有: {len(stores_only)}")
    output_lines.append(f"美食店铺+通识店铺 独有: {len(combined_only)}")
    output_lines.append(f"共同店铺: {len(common_stores)}")
    
    # 计算覆盖率
    if len(stores_names) > 0:
        coverage = len(common_stores) / len(stores_names) * 100
        output_lines.append(f"美食店铺+通识店铺 对 stores_202510241428 的覆盖率: {coverage:.1f}%")
    
    if len(combined_names) > 0:
        reverse_coverage = len(common_stores) / len(combined_names) * 100
        output_lines.append(f"stores_202510241428 对 美食店铺+通识店铺 的覆盖率: {reverse_coverage:.1f}%")
    
    # 打印到控制台
    for line in output_lines:
        print(line)
    
    # 保存到文件
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"店铺对比结果_{timestamp}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("店铺数据对比结果\n")
            f.write("="*50 + "\n")
            f.write(f"对比时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"对比文件: stores_202510241428.csv vs 美食店铺801.csv+通识店铺801.csv\n\n")
            
            for line in output_lines:
                f.write(line + "\n")
        
        print(f"\n✅ 结果已保存到文件: {output_file}")
        
        # 同时保存CSV格式的详细数据
        csv_output_file = f"店铺对比详细数据_{timestamp}.csv"
        
        # 创建详细数据DataFrame
        detailed_data = []
        
        # stores_202510241428 独有的店铺
        for name in sorted(stores_only):
            detailed_data.append({
                '店铺名称': name,
                '来源': 'stores_202510241428',
                '类型': '独有'
            })
        
        # 美食店铺+通识店铺 独有的店铺
        for name in sorted(combined_only):
            detailed_data.append({
                '店铺名称': name,
                '来源': '美食店铺+通识店铺',
                '类型': '独有'
            })
        
        # 共同的店铺
        for name in sorted(common_stores):
            detailed_data.append({
                '店铺名称': name,
                '来源': '共同',
                '类型': '共同'
            })
        
        # 保存为CSV
        detailed_df = pd.DataFrame(detailed_data)
        detailed_df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
        print(f"✅ 详细数据已保存到CSV文件: {csv_output_file}")
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
    
    return {
        'stores_only': stores_only,
        'combined_only': combined_only,
        'common_stores': common_stores,
        'stats': {
            'stores_total': len(stores_names),
            'food_total': len(food_names),
            'general_total': len(general_names),
            'combined_total': len(combined_names),
            'stores_only_count': len(stores_only),
            'combined_only_count': len(combined_only),
            'common_count': len(common_stores)
        }
    }

if __name__ == "__main__":
    try:
        result = compare_stores()
        print("\n✅ 对比完成!")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
