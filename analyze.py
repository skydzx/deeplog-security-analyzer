#!/usr/bin/env python3
"""
DeepLog日志分析工具 - 统一入口
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from deeplog import DeepLog


def main():
    print("DeepLog日志异常检测工具")
    print("=" * 40)

    # 创建示例数据
    print("准备示例数据...")

    # 训练数据
    train_logs = [
        "INFO Server started on port 8080",
        "INFO Database connection established",
        "INFO User login successful user_id=12345",
        "INFO Processing request request_id=req001",
        "INFO Request completed in 0.5 seconds",
    ] * 10

    # 测试数据
    test_logs = [
        "INFO Server started on port 8080",  # 正常
        "INFO Database connection established",  # 正常
        "ERROR Database connection failed",  # 异常
        "CRITICAL Server crashed",  # 异常
        "INFO Request completed in 0.3 seconds",  # 正常
    ]

    # 初始化和训练模型
    print("初始化DeepLog模型...")
    deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=32)

    print("训练模型...")
    deeplog.train(train_logs, epochs=2, batch_size=8)
    print("模型训练完成!")

    # 分析测试日志
    print("\n分析测试日志:")
    print("-" * 40)

    anomaly_count = 0
    for i, log in enumerate(test_logs, 1):
        is_anomaly, anomaly_type, details = deeplog.detect(log)

        status = "异常" if is_anomaly else "正常"
        if is_anomaly:
            anomaly_count += 1

        print("2d"
    print("
统计结果:"    print(f"总日志数: {len(test_logs)}")
    print(f"异常日志: {anomaly_count}")
    print(f"正常日志: {len(test_logs) - anomaly_count}")
    print(".1f"
    # 交互式测试
    print("
现在可以输入自己的日志进行检测 (输入 'quit' 退出):"    while True:
        try:
            user_input = input("\n日志: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见!")
                break

            if not user_input:
                continue

            is_anomaly, anomaly_type, details = deeplog.detect(user_input)

            if is_anomaly:
                print("结果: 异常日志")
            else:
                print("结果: 正常日志")

        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    main()