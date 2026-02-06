#!/usr/bin/env python3
"""
DeepLog基本功能测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """测试导入"""
    print("测试1: 导入DeepLog...")
    try:
        from deeplog import DeepLog
        print("成功: 导入成功")
        return True
    except Exception as e:
        print(f"失败: 导入失败 - {e}")
        return False

def test_init():
    """测试初始化"""
    print("\n测试2: 初始化...")
    try:
        from deeplog import DeepLog
        deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=16)
        print("成功: 初始化成功")
        return deeplog
    except Exception as e:
        print(f"失败: 初始化失败 - {e}")
        return None

def test_quick_train():
    """测试快速训练"""
    print("\n测试3: 快速训练...")
    try:
        from deeplog import DeepLog
        deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=16)

        # 很少的数据
        logs = ["INFO test message"] * 10

        print("训练中...")
        deeplog.train(logs, epochs=1, batch_size=4)
        print("成功: 训练成功")
        return deeplog
    except Exception as e:
        print(f"失败: 训练失败 - {e}")
        return None

def test_detect(deeplog):
    """测试检测"""
    print("\n测试4: 异常检测...")
    if not deeplog:
        print("失败: 没有模型")
        return False

    test_log = "INFO normal message"
    try:
        is_anomaly, anomaly_type, details = deeplog.detect(test_log)
        result = "异常" if is_anomaly else "正常"
        print(f"成功: 检测结果 - {result}")
        return True
    except Exception as e:
        print(f"失败: 检测失败 - {e}")
        return False

def main():
    print("DeepLog基本功能测试")
    print("=" * 30)

    success_count = 0
    total_tests = 4

    # 测试导入
    if test_import():
        success_count += 1

    # 测试初始化
    deeplog = test_init()
    if deeplog:
        success_count += 1

    # 测试训练
    trained_model = test_quick_train()
    if trained_model:
        success_count += 1

    # 测试检测
    if test_detect(trained_model):
        success_count += 1

    print(f"\n结果: {success_count}/{total_tests} 个测试通过")

    if success_count == total_tests:
        print("结论: DeepLog工作正常!")
    elif success_count >= 2:
        print("结论: 基本功能正常")
    else:
        print("结论: 需要检查配置")

if __name__ == "__main__":
    main()