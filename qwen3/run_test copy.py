import subprocess
import time
import re

def run_test(base_url, route, place_id, token, count, concurrency):
    """执行单次压力测试并返回关键结果"""
    try:
        print(f"\n开始测试 - 并发数: {concurrency}, 请求数: {count}")
        print(f"目标地址: {base_url}{route}")
        
        command = [
            "uv", "run", "qwen3/model_concurrency_test.py",
            "--base-url", base_url,
            "--route", route,
            "--place-id", place_id,
            "--token", token,
            "--mode", "并发",
            "--count", count,
            "--concurrency", concurrency,
            "--timeout", "120"
        ]
        
        start_time = time.time()
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        end_time = time.time()
        
        print("测试完成！")
        
        # 解析输出结果提取关键信息
        output = result.stdout
        success_rate = re.search(r'成功率: (\d+\.\d+)%', output)
        avg_response = re.search(r'平均响应时间: (\d+\.\d+)秒', output)
        max_response = re.search(r'最大响应时间: (\d+\.\d+)秒', output)
        qps = re.search(r'每秒响应数: (\d+\.\d+)', output)
        
        # 存储结果
        test_result = {
            'concurrency': int(concurrency),
            'count': int(count),
            'success_rate': float(success_rate.group(1)) if success_rate else None,
            'avg_response': float(avg_response.group(1)) if avg_response else None,
            'max_response': float(max_response.group(1)) if max_response else None,
            'qps': float(qps.group(1)) if qps else None,
            'duration': end_time - start_time,
            'success': True
        }
        
        return test_result
        
    except subprocess.CalledProcessError as e:
        print(f"测试失败！错误信息: {e.stderr}")
        return {
            'concurrency': int(concurrency),
            'count': int(count),
            'success': False,
            'error': str(e)
        }

def main():
    # 配置测试参数
    base_url = "https://screen.aibee.cn" # 线上
    # base_url = "http://127.0.0.1:8888" # 本地
    route = "/demo_ai_model/question" # 线上demo路由
    # route = "/mall_ai_model/question" # 本地demo默认正式路由
    place_id = "801"
    token = "G200000000000000"
    
    # 定义要测试的并发级别和每个级别的请求数
    # 可以根据需要调整这些值
    # test_configs = [{'concurrency': str(i), 'count': str(i)} for i in range(1, 301)]
    test_configs = [
        {'concurrency': '1', 'count': '1'},
        {'concurrency': '1', 'count': '1'},
        {'concurrency': '1', 'count': '1'},
        {'concurrency': '1', 'count': '1'},
        {'concurrency': '1', 'count': '1'},
        {'concurrency': '2', 'count': '2'},
        {'concurrency': '3', 'count': '3'},
        {'concurrency': '4', 'count': '4'},
        {'concurrency': '5', 'count': '5'},
        {'concurrency': '10', 'count': '10'},
        {'concurrency': '15', 'count': '15'},
        {'concurrency': '16', 'count': '16'},
        {'concurrency': '17', 'count': '17'},
        {'concurrency': '18', 'count': '18'},
        {'concurrency': '19', 'count': '19'},
        {'concurrency': '20', 'count': '20'},
        {'concurrency': '25', 'count': '25'},
        {'concurrency': '30', 'count': '30'},
        {'concurrency': '35', 'count': '35'},
        {'concurrency': '40', 'count': '40'},
        {'concurrency': '45', 'count': '45'},
        {'concurrency': '50', 'count': '50'},
        {'concurrency': '100', 'count': '100'},
        {'concurrency': '110', 'count': '110'},
        {'concurrency': '120', 'count': '120'},
        {'concurrency': '130', 'count': '130'},
        {'concurrency': '140', 'count': '140'},
        {'concurrency': '150', 'count': '150'},
        {'concurrency': '160', 'count': '160'},
        {'concurrency': '170', 'count': '170'},
        {'concurrency': '180', 'count': '180'},
        {'concurrency': '190', 'count': '190'},
        {'concurrency': '200', 'count': '200'},
        # {'concurrency': '300', 'count': '300'},
        # {'concurrency': '400', 'count': '400'},
        # {'concurrency': '500', 'count': '500'},
        # {'concurrency': '600', 'count': '600'},
        # {'concurrency': '700', 'count': '700'},
        # {'concurrency': '800', 'count': '800'},
        # {'concurrency': '900', 'count': '900'},
        # {'concurrency': '1000', 'count': '1000'},
        # {'concurrency': '2000', 'count': '2000'},
        # {'concurrency': '3000', 'count': '3000'},
        # {'concurrency': '4000', 'count': '4000'},
        # {'concurrency': '5000', 'count': '5000'},
    ]
    
    # 存储所有测试结果
    all_results = []
    
    # 执行所有测试
    for config in test_configs:
        result = run_test(
            base_url, 
            route, 
            place_id, 
            token, 
            config['count'], 
            config['concurrency']
        )

        if result.get('success_rate') != 100.0:
            break

        all_results.append(result)
        
        # 测试之间添加间隔，避免系统过载
        time.sleep(5)
    
    # 输出汇总报告
    print("\n" + "="*50)
    print("压力测试汇总报告")
    print("="*50)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {base_url}{route}")
    print("\n")
    print(f"{'并发数':<5} {'总请求数':<5} {'成功率(%)':<15} {'平均响应时间(s)':<15} {'最大响应时间(s)':<15} {'QPS':<30}")
    print("-"*90)

if __name__ == "__main__":
    main()
