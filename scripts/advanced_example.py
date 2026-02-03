"""
DeepLog高级使用示例
展示批量检测和参数值异常检测
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from deeplog import DeepLog
from datetime import datetime, timedelta
import random


def generate_normal_logs_with_timestamps(count=50):
    """生成带时间戳的正常日志"""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    logs = []
    timestamps = []
    
    log_templates = [
        "INFO Starting application",
        "INFO Connected to database",
        "INFO User login successful user_id={}",
        "INFO Processing request request_id=req{:03d}",
        "INFO Request completed in {:.2f} seconds",
        "INFO User logout user_id={}",
    ]
    
    user_id = 1000
    for i in range(count):
        template_idx = i % len(log_templates)
        template = log_templates[template_idx]
        
        if "user_id" in template:
            log = template.format(user_id)
            if i % 5 == 0:
                user_id += 1
        elif "request_id" in template:
            log = template.format(i)
        elif "seconds" in template:
            log = template.format(random.uniform(0.1, 1.0))
        else:
            log = template
        
        timestamp = base_time + timedelta(seconds=i)
        logs.append(log)
        timestamps.append(timestamp)
    
    return logs, timestamps


def generate_anomaly_logs():
    """生成异常日志"""
    anomalies = [
        "ERROR Database connection timeout",
        "WARN High memory usage detected: 95%",
        "INFO Unauthorized access attempt from IP 192.168.1.100",
        "INFO Request completed in 30.5 seconds",  # 异常：响应时间过长
        "CRITICAL System crash detected",
    ]
    return anomalies


def main():
    print("=" * 60)
    print("DeepLog 高级使用示例")
    print("=" * 60)
    
    # 1. 初始化DeepLog
    print("\n1. 初始化DeepLog...")
    deeplog = DeepLog(window_size=10, top_g=5, lstm_layers=2, lstm_units=64)
    
    # 2. 生成并训练
    print("\n2. 生成训练数据...")
    normal_logs, timestamps = generate_normal_logs_with_timestamps(100)
    print(f"训练日志数量: {len(normal_logs)}")
    
    print("\n3. 训练模型...")
    try:
        deeplog.train(
            normal_logs,
            timestamps=timestamps,
            train_key_model=True,
            train_param_models=True,
            epochs=10,
            batch_size=16
        )
        print("训练完成！")
    except Exception as e:
        print(f"训练出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 批量检测
    print("\n4. 批量检测日志...")
    test_logs, test_timestamps = generate_normal_logs_with_timestamps(20)
    anomaly_logs = generate_anomaly_logs()
    all_test_logs = test_logs + anomaly_logs
    
    results = deeplog.detect_batch(all_test_logs)
    
    print(f"\n检测了 {len(results)} 条日志:")
    normal_count = 0
    anomaly_count = 0
    
    for i, (is_anomaly, anomaly_type, details) in enumerate(results):
        log = all_test_logs[i]
        if is_anomaly:
            anomaly_count += 1
            print(f"\n[异常 #{anomaly_count}]")
            print(f"  日志: {log}")
            print(f"  类型: {anomaly_type}")
            if details.get('key_anomaly'):
                print(f"  日志键异常: {details['log_key']}")
                if details.get('predictions'):
                    print(f"  预测: {details['predictions'][:3]}")
            if details.get('parameter_anomaly'):
                print(f"  参数值异常，MSE: {details.get('mse', 'N/A'):.4f}")
        else:
            normal_count += 1
    
    print(f"\n检测结果统计:")
    print(f"  正常: {normal_count}")
    print(f"  异常: {anomaly_count}")
    print(f"  异常率: {anomaly_count / len(results) * 100:.2f}%")
    
    # 5. 展示预测信息
    print("\n5. 展示预测信息...")
    sample_log = test_logs[0] if test_logs else normal_logs[0]
    is_anomaly, _, details = deeplog.detect(sample_log)
    
    if details.get('predictions'):
        print(f"\n对于日志: {sample_log}")
        print("预测的下一个可能的日志键:")
        for i, (key, prob) in enumerate(details['predictions'][:5], 1):
            print(f"  {i}. {key}: {prob:.4f}")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

