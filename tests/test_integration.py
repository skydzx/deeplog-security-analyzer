"""
集成测试
测试各个组件之间的协作
"""

import pytest
import tempfile
import os


class TestBasicIntegration:
    """基本集成测试"""

    def test_parser_utils_integration(self):
        """测试解析器和工具函数的集成"""
        try:
            from deeplog.parser import LogParser
            from deeplog.utils import extract_log_key, extract_parameters

            # 创建解析器
            parser = LogParser()

            # 测试日志
            test_log = "2024-01-01 10:00:00 INFO User login user_id=12345"

            # 解析日志
            entry = parser.parse(test_log)

            # 验证解析结果
            assert entry.raw_message == test_log
            assert entry.timestamp is not None
            assert isinstance(entry.log_key, str)
            assert isinstance(entry.parameters, list)

            # 验证工具函数与解析器的一致性
            manual_key = extract_log_key(test_log)
            manual_params = extract_parameters(test_log, manual_key)

            assert entry.log_key == manual_key
            assert entry.parameters == manual_params

        except ImportError:
            pytest.skip("无法导入所需模块，跳过测试")


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_training_data(self):
        """测试无效训练数据"""
        try:
            from deeplog import DeepLog
            from deeplog.exceptions import ValidationError

            deeplog = DeepLog()

            # 空数据
            with pytest.raises(ValidationError):
                deeplog.train([])

        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")

    def test_detection_without_training(self):
        """测试未训练就检测"""
        try:
            from deeplog import DeepLog
            from deeplog.exceptions import DeepLogError

            deeplog = DeepLog()

            with pytest.raises(DeepLogError):
                deeplog.detect("INFO Test")

        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")


class TestConfiguration:
    """配置测试"""

    @pytest.mark.parametrize("window_size,top_g", [
        (3, 2),
        (5, 3),
        (10, 5),
    ])
    def test_different_configurations(self, window_size, top_g, sample_logs):
        """测试不同配置的兼容性"""
        try:
            from deeplog import DeepLog

            deeplog = DeepLog(
                window_size=window_size,
                top_g=top_g,
                lstm_layers=1,
                lstm_units=16
            )

            # 验证配置生效
            assert deeplog.window_size == window_size
            assert deeplog.top_g == top_g

        except ImportError:
            pytest.skip("DeepLog无法导入，跳过测试")