"""
测试异常处理
"""

import pytest
from deeplog.exceptions import (
    DeepLogError, ModelError, TrainingError, PredictionError,
    DataError, ParsingError, ValidationError, ConfigurationError,
    ResourceError, MemoryError, FileSystemError, ParallelProcessingError,
    handle_error, safe_execute
)


class TestDeepLogError:
    """测试基础异常类"""

    def test_deeplog_error_creation(self):
        """测试基础异常创建"""
        error = DeepLogError("测试错误")

        assert str(error) == "[UNKNOWN_ERROR] 测试错误"
        assert error.error_code == "UNKNOWN_ERROR"
        assert error.message == "测试错误"

    def test_deeplog_error_with_details(self):
        """测试带详细信息的异常"""
        error = DeepLogError(
            "测试错误",
            error_code="TEST_ERROR",
            details={"key": "value"},
            suggestion="修复建议"
        )

        error_str = str(error)
        assert "[TEST_ERROR]" in error_str
        assert "测试错误" in error_str
        assert "key" in error_str
        assert "修复建议" in error_str

    def test_deeplog_error_to_dict(self):
        """测试转换为字典"""
        error = DeepLogError(
            "测试错误",
            error_code="TEST_ERROR",
            details={"param": "value"},
            suggestion="建议"
        )

        error_dict = error.to_dict()
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "测试错误"
        assert error_dict["details"]["param"] == "value"
        assert error_dict["suggestion"] == "建议"


class TestSpecificErrors:
    """测试具体异常类型"""

    def test_training_error(self):
        """测试训练错误"""
        error = TrainingError(
            "训练失败",
            stage="data_preparation",
            model_type="LogKeyModel"
        )

        assert error.error_code == "TRAINING_ERROR"
        assert error.details["stage"] == "data_preparation"
        assert error.details["model_type"] == "LogKeyModel"

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError(
            "参数无效",
            field="window_size",
            value=0,
            expected_type="positive integer"
        )

        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "window_size"
        # value会被转换为字符串存储
        assert error.details["value"] == "0"

    def test_configuration_error(self):
        """测试配置错误"""
        error = ConfigurationError(
            "参数超出范围",
            parameter="batch_size",
            current_value=1000,
            valid_range="1-100"
        )

        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details["parameter"] == "batch_size"

    def test_memory_error(self):
        """测试内存错误"""
        error = MemoryError(
            "内存不足",
            memory_usage_mb=900,
            available_memory_mb=1000
        )

        assert error.error_code == "MEMORY_ERROR"
        assert error.details["memory_usage_mb"] == 900

    def test_filesystem_error(self):
        """测试文件系统错误"""
        error = FileSystemError(
            "文件不存在",
            file_path="/tmp/model.pkl",
            operation="read"
        )

        assert error.error_code == "FILESYSTEM_ERROR"
        assert error.details["file_path"] == "/tmp/model.pkl"


class TestErrorHandlingFunctions:
    """测试错误处理函数"""

    def test_handle_error_with_deeplog_error(self):
        """测试处理DeepLog错误"""
        original_error = DeepLogError("原始错误")
        handled_error = handle_error(original_error, "上下文")

        assert handled_error is original_error

    def test_handle_error_with_standard_error(self):
        """测试处理标准异常"""
        original_error = ValueError("值错误")
        handled_error = handle_error(original_error, "测试上下文")

        assert isinstance(handled_error, ValidationError)
        assert "测试上下文" in handled_error.message

    def test_handle_error_with_memory_error(self):
        """测试处理内存错误"""
        original_error = MemoryError("内存不足")
        handled_error = handle_error(original_error)

        assert isinstance(handled_error, MemoryError)

    def test_safe_execute_success(self):
        """测试安全执行成功情况"""
        def test_func(x, y):
            return x + y

        result = safe_execute(test_func, 1, 2)
        assert result == 3

    def test_safe_execute_failure(self):
        """测试安全执行失败情况"""
        def failing_func():
            raise ValueError("测试错误")

        with pytest.raises(ValidationError):
            safe_execute(failing_func, error_context="测试上下文")


class TestErrorSuggestions:
    """测试错误建议功能"""

    def test_training_error_suggestions(self):
        """测试训练错误建议"""
        error = TrainingError("训练失败", stage="data_preparation")
        assert "检查训练数据的格式和完整性" in error.suggestion

        error = TrainingError("训练失败", stage="model_building", model_type="LogKeyModel")
        assert "LogKeyModel" in error.suggestion

    def test_configuration_error_suggestions(self):
        """测试配置错误建议"""
        error = ConfigurationError("错误", parameter="window_size")
        assert "窗口大小应为正整数" in error.suggestion

        error = ConfigurationError("错误", parameter="batch_size")
        assert "批次大小应为正整数" in error.suggestion

    def test_memory_error_suggestions(self):
        """测试内存错误建议"""
        error = MemoryError("内存不足")
        assert "尝试减小批次大小" in error.suggestion

    def test_filesystem_error_suggestions(self):
        """测试文件系统错误建议"""
        error = FileSystemError("错误", operation="read")
        assert "检查文件是否存在" in error.suggestion

        error = FileSystemError("错误", operation="write")
        assert "检查目录权限" in error.suggestion