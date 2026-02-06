#!/usr/bin/env python3
"""
DeepLog异常检测能力测试脚本
专门测试DeepLog在真实日志数据上的异常检测效果
"""

import sys
import os
import time
from pathlib import Path
from collections import defaultdict, Counter

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from deeplog import DeepLog
from deeplog.exceptions import DeepLogError


def load_test_logs(log_dir='logs', max_logs=2000):
    """加载测试日志数据"""
    import glob
    import random

    log_lines = []
    log_files = []

    # 查找所有日志文件
    for pattern in ['*.txt', '*.log']:
        log_files.extend(glob.glob(os.path.join(log_dir, '**', pattern), recursive=True))

    print(f"找到 {len(log_files)} 个日志文件")

    # 读取日志内容
    for filepath in log_files[:5]:  # 限制文件数量以加快测试
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()][:200]  # 每个文件限制200行
                log_lines.extend(lines)
                print(f"从 {os.path.basename(filepath)} 读取了 {len(lines)} 行日志")
        except Exception as e:
            print(f"读取文件失败 {filepath}: {e}")
            continue

    # 限制总数
    if len(log_lines) > max_logs:
        log_lines = log_lines[:max_logs]

    print(f"总共加载了 {len(log_lines)} 行日志")
    return log_lines


def generate_anomalous_logs(normal_logs, num_anomalies=20):
    """基于正常日志生成异常日志"""
    anomalous_logs = []

    # 1. 完全不同的错误日志
    error_patterns = [
        "ERROR Database connection failed",
        "CRITICAL System crash detected",
        "FATAL Application terminated unexpectedly",
        "WARNING Memory leak detected",
        "Exception in thread main",
        "NullPointerException",
        "Segmentation fault",
        "Permission denied",
        "Connection timeout",
        "Disk space full"
    ]

    anomalous_logs.extend(error_patterns)

    # 2. 基于现有日志的变异
    if normal_logs:
        for i in range(min(10, len(normal_logs))):
            # 替换正常日志中的关键词
            normal_log = normal_logs[i]
            if "INFO" in normal_log:
                anomalous = normal_log.replace("INFO", "ERROR", 1)
                anomalous_logs.append(anomalous)
            elif "Connected" in normal_log:
                anomalous = normal_log.replace("Connected", "Failed to connect", 1)
                anomalous_logs.append(anomalous)

    print(f"生成了 {len(anomalous_logs)} 条异常日志")
    return anomalous_logs


def test_anomaly_detection():
    """测试异常检测能力"""
    print("=" * 60)
    print("DeepLog异常检测能力测试")
    print("=" * 60)

    # 1. 加载训练数据
    print("\n1. 加载训练数据...")
    try:
        train_logs = load_test_logs(max_logs=1500)
        if len(train_logs) < 100:
            print("警告: 训练数据不足，使用示例数据")
            train_logs = [
                "2024-01-01 10:00:00 INFO Starting application",
                "2024-01-01 10:00:01 INFO Connected to database",
                "2024-01-01 10:00:02 INFO User login successful user_id=12345",
                "2024-01-01 10:00:03 INFO Processing request request_id=req001",
                "2024-01-01 10:00:04 INFO Request completed in 0.5 seconds",
            ] * 20  # 重复以增加数据量

        print(f"训练数据: {len(train_logs)} 条日志")

    except Exception as e:
        print(f"加载训练数据失败: {e}")
        return

    # 2. 初始化和训练模型
    print("\n2. 初始化DeepLog模型...")
    try:
        deeplog = DeepLog(
            window_size=3,  # 较小的窗口以适应小数据集
            top_g=2,
            lstm_layers=1,
            lstm_units=32
        )

        print("开始训练...")
        start_time = time.time()
        deeplog.train(
            train_logs,
            epochs=3,  # 减少训练轮数以加快测试
            batch_size=8
        )
        train_time = time.time() - start_time
        print(f"训练完成，耗时: {train_time:.2f}秒")
    except Exception as e:
        print(f"模型训练失败: {e}")
        return

    # 3. 准备测试数据
    print("\n3. 准备测试数据...")

    # 正常测试数据（从训练数据中选择）
    normal_test_logs = []
    if len(train_logs) > 10:
        normal_test_logs = train_logs[-10:]  # 最后10条作为正常测试

    # 生成异常测试数据
    anomalous_test_logs = generate_anomalous_logs(train_logs)

    print(f"正常测试数据: {len(normal_test_logs)} 条")
    print(f"异常测试数据: {len(anomalous_test_logs)} 条")

    # 4. 执行异常检测
    print("\n4. 执行异常检测测试...")

    results = {
        'normal': {'correct': 0, 'total': 0},
        'anomalous': {'correct': 0, 'total': 0}
    }

    detection_details = []

    # 测试正常日志
    print("\n测试正常日志:")
    for i, log in enumerate(normal_test_logs):
        try:
            is_anomaly, anomaly_type, details = deeplog.detect(log)
            results['normal']['total'] += 1

            if not is_anomaly:
                results['normal']['correct'] += 1
                status = "✓ 正确"
            else:
                status = "✗ 误报"

            print("2d")
            detection_details.append({
                'log': log[:80] + "..." if len(log) > 80 else log,
                'expected': 'normal',
                'detected': 'anomaly' if is_anomaly else 'normal',
                'correct': not is_anomaly,
                'type': anomaly_type,
                'confidence': 0  # 暂时简化，避免处理复杂的数据结构
            })

        except Exception as e:
            print(f"检测失败: {e}")
            continue

    # 测试异常日志
    print("\n测试异常日志:")
    for i, log in enumerate(anomalous_test_logs):
        try:
            is_anomaly, anomaly_type, details = deeplog.detect(log)
            results['anomalous']['total'] += 1

            if is_anomaly:
                results['anomalous']['correct'] += 1
                status = "✓ 正确"
            else:
                status = "✗ 漏报"

            print("2d")
            detection_details.append({
                'log': log[:80] + "..." if len(log) > 80 else log,
                'expected': 'anomaly',
                'detected': 'anomaly' if is_anomaly else 'normal',
                'correct': is_anomaly,
                'type': anomaly_type,
                'confidence': 0  # 暂时简化，避免处理复杂的数据结构
            })

        except Exception as e:
            print(f"检测失败: {e}")
            continue

    # 5. 计算和显示结果
    print("\n5. 检测结果统计")
    print("-" * 40)

    # 准确率计算
    normal_accuracy = (results['normal']['correct'] / results['normal']['total'] * 100) if results['normal']['total'] > 0 else 0
    anomalous_accuracy = (results['anomalous']['correct'] / results['anomalous']['total'] * 100) if results['anomalous']['total'] > 0 else 0
    overall_accuracy = ((results['normal']['correct'] + results['anomalous']['correct']) /
                       (results['normal']['total'] + results['anomalous']['total']) * 100) if (results['normal']['total'] + results['anomalous']['total']) > 0 else 0

    print("\n准确率统计:")
    print(f"正常日志准确率: {normal_accuracy:.1f}%")
    print(f"异常日志准确率: {anomalous_accuracy:.1f}%")
    print(f"整体准确率: {overall_accuracy:.1f}%")
    print("\n详细统计:")
    print(f"正常日志 - 正确: {results['normal']['correct']}/{results['normal']['total']}")
    print(f"异常日志 - 正确: {results['anomalous']['correct']}/{results['anomalous']['total']}")

    # 错误分析
    false_positives = [d for d in detection_details if d['expected'] == 'normal' and not d['correct']]
    false_negatives = [d for d in detection_details if d['expected'] == 'anomaly' and not d['correct']]

    print("\n错误分析:")
    print(f"误报 (正常日志被误判为异常): {len(false_positives)} 例")
    print(f"漏报 (异常日志被误判为正常): {len(false_negatives)} 例")

    if false_positives:
        print("\n误报示例:")
        for fp in false_positives[:3]:  # 只显示前3个
            print(f"  - {fp['log']}")

    if false_negatives:
        print("\n漏报示例:")
        for fn in false_negatives[:3]:  # 只显示前3个
            print(f"  - {fn['log']}")

    # 6. 性能评估
    print("\n6. 性能评估")
    print("-" * 40)

    if overall_accuracy >= 80:
        performance = "优秀"
        color = "[EXCELLENT]"
    elif overall_accuracy >= 70:
        performance = "良好"
        color = "[GOOD]"
    elif overall_accuracy >= 60:
        performance = "一般"
        color = "[FAIR]"
    else:
        performance = "需要改进"
        color = "[NEEDS_IMPROVEMENT]"

    print(f"整体表现: {color} {performance} ({overall_accuracy:.1f}%)")

    # 给出建议
    print("\n📋 建议:")
    if overall_accuracy < 70:
        print("• 增加训练数据量，提高模型泛化能力")
        print("• 调整模型参数 (window_size, lstm_units等)")
        print("• 增加训练轮数")
        print("• 检查日志数据的质量和多样性")
    else:
        print("• 模型表现良好，可以用于实际场景")
        print("• 建议在更多真实数据上测试")
        print("• 可以考虑微调参数以进一步提升性能")

    print(f"\n训练耗时: {train_time:.2f}秒")
    print(f"检测速度: 约{(results['normal']['total'] + results['anomalous']['total']) / max(train_time, 0.1):.1f}条/秒")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_different_scenarios():
    """测试不同场景下的异常检测"""
    print("\n\n7. 场景测试")
    print("-" * 40)

    # 简单的场景测试
    scenarios = [
        {
            'name': '标准INFO日志序列',
            'logs': [
                'INFO Application started',
                'INFO Database connected',
                'INFO User authenticated',
                'INFO Request processed'
            ],
            'expected_anomalies': 0
        },
        {
            'name': '包含ERROR的序列',
            'logs': [
                'INFO Application started',
                'INFO Database connected',
                'ERROR Connection failed',
                'INFO User authenticated'
            ],
            'expected_anomalies': 1
        },
        {
            'name': '异常时间序列',
            'logs': [
                'INFO Normal operation',
                'INFO Normal operation',
                '2024-01-01 25:00:00 INFO Invalid time',  # 无效时间
                'INFO Normal operation'
            ],
            'expected_anomalies': 1
        }
    ]

    # 这里可以添加更详细的场景测试
    print("场景测试功能预留，可以根据需要扩展")


if __name__ == "__main__":
    try:
        test_anomaly_detection()
        test_different_scenarios()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()