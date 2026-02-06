#!/usr/bin/env python3
"""
DeepLog交互式异常检测演示
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from deeplog import DeepLog

def setup_model():
    """设置和训练模型"""
    print("正在准备DeepLog模型...")

    # 创建训练数据
    normal_logs = [
        "INFO Server started on port 8080",
        "INFO Database connection established",
        "INFO User login successful user_id=12345",
        "INFO Processing request request_id=req001",
        "INFO Request completed in 0.5 seconds",
    ] * 10  # 50条日志

    # 初始化模型
    deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=32)

    # 训练模型
    print("训练中...")
    deeplog.train(normal_logs, epochs=2, batch_size=8)
    print("模型准备完成!")
    return deeplog

def demo_detection(deeplog):
    """演示异常检测"""
    print("\n" + "="*50)
    print("DeepLog异常检测演示")
    print("="*50)
    print("输入日志消息，DeepLog会判断是否异常")
    print("输入 'quit' 退出")
    print("-"*50)

    while True:
        try:
            user_input = input("\n请输入日志消息: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("演示结束!")
                break

            if not user_input:
                print("请输入有效的日志消息")
                continue

            # 检测异常
            is_anomaly, anomaly_type, details = deeplog.detect(user_input)

            print(f"日志: {user_input}")

            if is_anomaly:
                print("结果: 异常日志")
                print("分析: 这条日志偏离了正常模式")
            else:
                print("结果: 正常日志")
                print("分析: 这条日志符合正常模式")

        except KeyboardInterrupt:
            print("\n演示被中断")
            break
        except Exception as e:
            print(f"检测出错: {e}")

def show_examples():
    """显示示例"""
    print("\n建议测试的日志示例:")
    print("正常日志:")
    print("  INFO Server started on port 8080")
    print("  INFO Database connection established")
    print("  INFO User login successful")
    print("\n异常日志:")
    print("  ERROR Database connection failed")
    print("  CRITICAL Server crashed")
    print("  FATAL Application terminated")
    print("  WARNING Memory leak detected")

def main():
    try:
        # 设置模型
        deeplog = setup_model()

        # 显示示例
        show_examples()

        # 开始交互演示
        demo_detection(deeplog)

    except Exception as e:
        print(f"设置过程中出错: {e}")

if __name__ == "__main__":
    main()