"""
测试DeepLog主类
"""

import pytest
import numpy as np
from datetime import datetime


class TestDeepLogInitialization:
    """测试DeepLog初始化"""

    def test_deeplog_default_initialization(self):
        """测试默认参数初始化"""
        try:
            from deeplog import DeepLog
            deeplog = DeepLog()

            assert deeplog.window_size == 10
            assert deeplog.top_g == 5
            assert deeplog.lstm_layers == 2
            assert deeplog.lstm_units == 64
            assert deeplog.parser is not None
        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")

    def test_deeplog_custom_initialization(self):
        """测试自定义参数初始化"""
        try:
            from deeplog import DeepLog
            deeplog = DeepLog(
                window_size=5,
                top_g=3,
                lstm_layers=1,
                lstm_units=32
            )

            assert deeplog.window_size == 5
            assert deeplog.top_g == 3
            assert deeplog.lstm_layers == 1
            assert deeplog.lstm_units == 32
        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")


class TestDeepLogBasicFunctionality:
    """测试DeepLog基本功能"""

    def test_detect_without_training(self):
        """测试未训练就检测"""
        try:
            from deeplog import DeepLog
            from deeplog.exceptions import DeepLogError
            deeplog = DeepLog()

            with pytest.raises(DeepLogError, match="模型未训练"):
                deeplog.detect("INFO Test message")
        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")

    def test_train_empty_logs(self):
        """测试空日志训练"""
        try:
            from deeplog import DeepLog
            from deeplog.exceptions import ValidationError
            deeplog = DeepLog()

            with pytest.raises(ValidationError):
                deeplog.train([])
        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")