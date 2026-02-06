#!/usr/bin/env python3
"""
测试运行脚本
"""

import sys
import subprocess
import os

def run_tests():
    """运行测试套件"""
    print("=" * 60)
    print("运行DeepLog测试套件")
    print("=" * 60)

    # 检查是否安装了测试依赖
    try:
        import pytest
        import pytest_cov
    except ImportError:
        print("错误: 未安装测试依赖")
        print("请运行: pip install -r requirements.txt")
        return False

    # 运行测试
    cmd = [
        sys.executable, "-m", "pytest",
        "--verbose",
        "--tb=short",
        "--cov=deeplog",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-fail-under=25"
    ]

    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        if result.returncode == 0:
            print("\n[OK] 所有测试通过!")
            return True
        else:
            print(f"\n[ERROR] 测试失败 (退出码: {result.returncode})")
            return False
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def run_specific_test(test_file):
    """运行特定测试文件"""
    print(f"运行测试文件: {test_file}")

    cmd = [sys.executable, "-m", "pytest", f"tests/{test_file}", "--verbose", "--tb=short"]

    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        success = run_tests()

    sys.exit(0 if success else 1)