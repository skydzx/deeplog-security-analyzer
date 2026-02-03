"""
评估示例
展示如何使用评估器
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from deeplog import DeepLog, Evaluator, evaluate_on_dataset


def generate_test_data():
    """生成测试数据（包含正常和异常日志）"""
    normal_logs = [
        "2024-01-01 10:00:00 INFO Starting application",
        "2024-01-01 10:00:01 INFO Connected to database",
        "2024-01-01 10:00:02 INFO User login successful",
        "2024-01-01 10:00:03 INFO Processing request",
        "2024-01-01 10:00:04 INFO Request completed",
    ]
    
    anomaly_logs = [
        "2024-01-01 10:00:05 ERROR Database connection failed",
        "2024-01-01 10:00:06 INFO User login successful",
        "2024-01-01 10:00:07 CRITICAL System crash detected",
    ]
    
    all_logs = normal_logs + anomaly_logs
    ground_truth = [False] * len(normal_logs) + [True] * len(anomaly_logs)
    
    return all_logs, ground_truth


def main():
    print("=" * 60)
    print("评估示例")
    print("=" * 60)
    
    # 1. 训练模型
    print("\n1. 训练模型...")
    deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=16)
    
    # 使用正常日志训练
    training_logs = [
        "2024-01-01 10:00:00 INFO Starting application",
        "2024-01-01 10:00:01 INFO Connected to database",
        "2024-01-01 10:00:02 INFO User login successful",
        "2024-01-01 10:00:03 INFO Processing request",
        "2024-01-01 10:00:04 INFO Request completed",
        "2024-01-01 10:00:05 INFO Starting application",
        "2024-01-01 10:00:06 INFO Connected to database",
        "2024-01-01 10:00:07 INFO User login successful",
    ]
    deeplog.train(training_logs, epochs=5, batch_size=4)
    
    # 2. 准备测试数据
    print("\n2. 准备测试数据...")
    test_logs, ground_truth = generate_test_data()
    print(f"测试日志数量: {len(test_logs)}")
    print(f"正常日志: {sum(1 for x in ground_truth if not x)}")
    print(f"异常日志: {sum(1 for x in ground_truth if x)}")
    
    # 3. 评估
    print("\n3. 执行评估...")
    metrics = evaluate_on_dataset(deeplog, test_logs, ground_truth)
    
    # 4. 显示结果
    print("\n4. 评估结果:")
    evaluator = Evaluator()
    evaluator.true_positives = int(metrics['true_positives'])
    evaluator.false_positives = int(metrics['false_positives'])
    evaluator.true_negatives = int(metrics['true_negatives'])
    evaluator.false_negatives = int(metrics['false_negatives'])
    evaluator.print_report()
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

