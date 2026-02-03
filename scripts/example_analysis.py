#!/usr/bin/env python3
"""
DeepLog日志分析使用示例

这个脚本演示了如何使用DeepLog进行日志分析的完整流程：
1. 准备训练数据
2. 训练异常检测模型
3. 分析新的日志数据
4. 生成分析报告
"""

import sys
from pathlib import Path
import tempfile
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.analyze_logs import LogAnalyzer


def create_sample_data():
    """创建示例数据"""
    print("创建示例日志数据...")

    # 创建临时目录
    temp_dir = Path(tempfile.gettempdir()) / "deeplog_demo"
    temp_dir.mkdir(exist_ok=True)

    # 训练数据文件（正常日志）
    train_file = temp_dir / "train_logs.txt"
    with open(train_file, 'w', encoding='utf-8') as f:
        normal_logs = [
            "INFO Server started on port 8080",
            "INFO Database connection established to localhost:5432",
            "INFO User login successful: user_id=12345, session=abc123",
            "INFO Processing request: request_id=req001, method=GET, path=/api/users",
            "INFO Request completed: request_id=req001, status=200, duration=0.45s",
            "INFO Cache hit: key=user:12345, hits=150",
            "INFO API call successful: endpoint=/api/orders, response_time=0.23s",
            "INFO Health check passed: cpu=45%, memory=60%, disk=70%",
            "INFO Scheduled task completed: task=backup, duration=120s",
            "INFO Connection pool status: active=5, idle=10, waiting=0",
        ]

        # 重复写入多次以增加数据量
        for _ in range(20):
            for log in normal_logs:
                f.write(log + '\n')

    # 测试数据文件（包含异常）
    test_file = temp_dir / "test_logs.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        test_logs = [
            # 正常日志
            "INFO Server started on port 8080",
            "INFO Database connection established to localhost:5432",
            "INFO User login successful: user_id=67890, session=xyz789",

            # 异常日志
            "ERROR Database connection failed: timeout after 30 seconds",
            "CRITICAL Server crashed unexpectedly: segmentation fault",
            "FATAL Application terminated: out of memory",
            "WARNING Memory usage critical: 95% used, 500MB available",
            "Exception in thread main: NullPointerException at line 156",
            "Permission denied: cannot access /var/log/app.log",
            "Connection timeout: failed to connect to redis:6379",
            "Disk space full: only 100MB remaining on /var/log",

            # 更多正常日志
            "INFO Request completed: request_id=req002, status=200, duration=0.32s",
            "INFO Health check passed: all systems operational",
        ]

        for log in test_logs:
            f.write(log + '\n')

    print(f"示例数据已创建:")
    print(f"  训练数据: {train_file}")
    print(f"  测试数据: {test_file}")

    return str(train_file), str(test_file), str(temp_dir)


def demonstrate_analysis():
    """演示完整的日志分析流程"""
    print("DeepLog日志分析演示")
    print("=" * 60)

    try:
        # 1. 创建示例数据
        train_file, test_file, temp_dir = create_sample_data()

        # 2. 创建分析器
        analyzer = LogAnalyzer(model_dir=f"{temp_dir}/models")

        # 3. 训练模型
        print("\n第1步: 训练异常检测模型")
        print("-" * 40)
        if analyzer.train_model(train_file, epochs=3):
            print("✓ 模型训练成功")
        else:
            print("✗ 模型训练失败")
            return

        # 4. 分析日志
        print("\n第2步: 分析日志文件")
        print("-" * 40)
        report_file = f"{temp_dir}/analysis_report.txt"
        results = analyzer.analyze_logs(test_file, report_file)

        if results:
            print("✓ 日志分析完成")
            print(f"✓ 报告已保存: {report_file}")

            # 显示关键结果
            summary = results['summary']
            print("\n分析结果:")
            print(f"  总日志数: {summary['total_logs']}")
            print(f"  异常日志: {summary['anomaly_count']}")
            print(f"  正常日志: {summary['normal_count']}")
            print(".1f"            # 显示前几个异常
            if results['anomalies']:
                print("\n检测到的异常:")
                for i, anomaly in enumerate(results['anomalies'][:3]):
                    print(f"  {i+1}. 行{anomaly['line_number']}: {anomaly['content'][:60]}...")
        else:
            print("✗ 日志分析失败")
            return

        # 5. 交互式演示
        print("
第3步: 交互式异常检测"        print("-" * 40)
        print("现在你可以输入自己的日志消息进行检测")
        print("输入 'quit' 退出演示")

        analyzer.interactive_analysis()

    except Exception as e:
        print(f"演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理临时文件（可选）
        print(f"\n演示数据保存在: {temp_dir}")
        print("你可以查看生成的模型文件和分析报告")


def show_usage_examples():
    """显示使用示例"""
    print("\n" + "="*60)
    print("DeepLog日志分析工具使用示例")
    print("="*60)

    print("\n1. 训练模型:")
    print("   python scripts/analyze_logs.py --train logs/normal_logs.txt")

    print("\n2. 分析日志:")
    print("   python scripts/analyze_logs.py --analyze logs/test_logs.txt --output report.txt")

    print("\n3. 训练后立即分析:")
    print("   python scripts/analyze_logs.py --train normal.txt --analyze test.txt")

    print("\n4. 指定模型目录:")
    print("   python scripts/analyze_logs.py --model my_models --analyze logs.txt")

    print("\n5. 交互式分析:")
    print("   python scripts/analyze_logs.py --interactive")

    print("\n6. 查看帮助:")
    print("   python scripts/analyze_logs.py --help")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        show_usage_examples()
    else:
        demonstrate_analysis()