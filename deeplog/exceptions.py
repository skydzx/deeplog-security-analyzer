"""
DeepLog异常类定义
提供完整的异常处理体系
"""

from typing import Dict, Any, Optional


class DeepLogError(Exception):
    """
    DeepLog基础异常类

    所有DeepLog相关的异常都应该继承此类
    """

    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None,
                 suggestion: Optional[str] = None):
        """
        初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 详细错误信息
            suggestion: 建议的解决方法
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.suggestion = suggestion

    def __str__(self):
        """字符串表示"""
        parts = [f"[{self.error_code}] {self.message}"]

        if self.details:
            parts.append(f"Details: {self.details}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion
        }


class ModelError(DeepLogError):
    """模型相关异常"""
    pass


class TrainingError(ModelError):
    """训练相关异常"""

    def __init__(self, message: str, stage: str = "unknown",
                 model_type: str = "unknown", **kwargs):
        details = {"stage": stage, "model_type": model_type}
        details.update(kwargs)
        super().__init__(
            message,
            error_code="TRAINING_ERROR",
            details=details,
            suggestion=self._get_training_suggestion(stage, model_type)
        )

    def _get_training_suggestion(self, stage: str, model_type: str) -> str:
        """根据训练阶段提供建议"""
        suggestions = {
            "data_preparation": "检查训练数据的格式和完整性",
            "model_building": f"检查{model_type}模型的参数配置",
            "training_loop": "尝试减小批次大小或学习率",
            "validation": "检查验证数据的格式"
        }
        return suggestions.get(stage, "检查训练配置和数据")


class PredictionError(ModelError):
    """预测相关异常"""

    def __init__(self, message: str, model_type: str = "unknown",
                 input_shape: Optional[tuple] = None, **kwargs):
        details = {"model_type": model_type}
        if input_shape:
            details["input_shape"] = input_shape
        details.update(kwargs)
        super().__init__(
            message,
            error_code="PREDICTION_ERROR",
            details=details,
            suggestion=self._get_prediction_suggestion(model_type)
        )

    def _get_prediction_suggestion(self, model_type: str) -> str:
        """根据模型类型提供预测建议"""
        suggestions = {
            "LogKeyModel": "确保输入是长度为window_size的日志键序列",
            "ParameterValueModel": "检查参数值的格式和维度"
        }
        return suggestions.get(model_type, "检查输入数据的格式")


class DataError(DeepLogError):
    """数据相关异常"""
    pass


class ParsingError(DataError):
    """解析相关异常"""

    def __init__(self, message: str, line_content: Optional[str] = None,
                 line_number: Optional[int] = None, **kwargs):
        details = {}
        if line_content:
            details["line_content"] = line_content[:100]  # 限制长度
        if line_number:
            details["line_number"] = line_number
        details.update(kwargs)
        super().__init__(
            message,
            error_code="PARSING_ERROR",
            details=details,
            suggestion=self._get_parsing_suggestion()
        )

    def _get_parsing_suggestion(self) -> str:
        """提供解析建议"""
        return "检查日志格式是否符合预期，或使用自定义解析器"


class ValidationError(DataError):
    """数据验证异常"""

    def __init__(self, message: str, field: str = "unknown",
                 value: Any = None, expected_type: str = "unknown", **kwargs):
        details = {"field": field, "expected_type": expected_type}
        if value is not None:
            details["value"] = str(value)[:50]  # 限制长度
        details.update(kwargs)
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details=details,
            suggestion=self._get_validation_suggestion(expected_type)
        )

    def _get_validation_suggestion(self, expected_type: str) -> str:
        """提供验证建议"""
        suggestions = {
            "list": "确保输入是列表或数组格式",
            "str": "确保输入是字符串格式",
            "int": "确保输入是整数格式",
            "float": "确保输入是浮点数格式"
        }
        return suggestions.get(expected_type, "检查输入数据的类型和格式")


class ConfigurationError(DeepLogError):
    """配置相关异常"""

    def __init__(self, message: str, parameter: str = "unknown",
                 current_value: Any = None, valid_range: Any = None, **kwargs):
        details = {"parameter": parameter}
        if current_value is not None:
            details["current_value"] = current_value
        if valid_range is not None:
            details["valid_range"] = valid_range
        details.update(kwargs)
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            suggestion=self._get_config_suggestion(parameter)
        )

    def _get_config_suggestion(self, parameter: str) -> str:
        """提供配置建议"""
        suggestions = {
            "window_size": "窗口大小应为正整数，通常在3-20之间",
            "top_g": "top_g应为正整数，通常在1-10之间",
            "batch_size": "批次大小应为正整数，通常在8-128之间",
            "epochs": "训练轮数应为正整数，通常在5-100之间"
        }
        return suggestions.get(parameter, "检查参数的有效范围")


class ResourceError(DeepLogError):
    """资源相关异常"""
    pass


class MemoryError(ResourceError):
    """内存相关异常"""

    def __init__(self, message: str, memory_usage_mb: Optional[float] = None,
                 available_memory_mb: Optional[float] = None, **kwargs):
        details = {}
        if memory_usage_mb is not None:
            details["memory_usage_mb"] = memory_usage_mb
        if available_memory_mb is not None:
            details["available_memory_mb"] = available_memory_mb
        details.update(kwargs)
        super().__init__(
            message,
            error_code="MEMORY_ERROR",
            details=details,
            suggestion=self._get_memory_suggestion()
        )

    def _get_memory_suggestion(self) -> str:
        """提供内存优化建议"""
        return "尝试减小批次大小、使用批处理、或增加系统内存"


class FileSystemError(ResourceError):
    """文件系统异常"""

    def __init__(self, message: str, file_path: Optional[str] = None,
                 operation: str = "unknown", **kwargs):
        details = {"operation": operation}
        if file_path:
            details["file_path"] = file_path
        details.update(kwargs)
        super().__init__(
            message,
            error_code="FILESYSTEM_ERROR",
            details=details,
            suggestion=self._get_fs_suggestion(operation)
        )

    def _get_fs_suggestion(self, operation: str) -> str:
        """提供文件系统建议"""
        suggestions = {
            "read": "检查文件是否存在、权限是否正确",
            "write": "检查目录权限和磁盘空间",
            "save": "检查保存路径的权限和空间",
            "load": "检查文件是否存在且未损坏"
        }
        return suggestions.get(operation, "检查文件和目录权限")


class ParallelProcessingError(DeepLogError):
    """并行处理异常"""

    def __init__(self, message: str, n_workers: Optional[int] = None,
                 failed_task: Optional[str] = None, **kwargs):
        details = {}
        if n_workers:
            details["n_workers"] = n_workers
        if failed_task:
            details["failed_task"] = failed_task
        details.update(kwargs)
        super().__init__(
            message,
            error_code="PARALLEL_ERROR",
            details=details,
            suggestion=self._get_parallel_suggestion()
        )

    def _get_parallel_suggestion(self) -> str:
        """提供并行处理建议"""
        return "尝试减少并行进程数，或使用顺序处理"


# 便捷函数
def handle_error(error: Exception, context: str = "") -> DeepLogError:
    """
    将普通异常转换为DeepLog异常

    Args:
        error: 原始异常
        context: 错误上下文信息

    Returns:
        DeepLog异常对象
    """
    if isinstance(error, DeepLogError):
        return error

    message = f"{context}: {str(error)}" if context else str(error)

    # 根据异常类型映射到相应的DeepLog异常
    if isinstance(error, MemoryError):
        return MemoryError(message)
    elif isinstance(error, FileNotFoundError) or isinstance(error, PermissionError):
        return FileSystemError(message)
    elif isinstance(error, ValueError):
        return ValidationError(message)
    else:
        return DeepLogError(message, suggestion="检查错误详情并重试")


def safe_execute(func, *args, error_context: str = "", **kwargs):
    """
    安全执行函数，自动处理异常

    Args:
        func: 要执行的函数
        error_context: 错误上下文
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        函数结果或None（如果出错）

    Raises:
        DeepLogError: 如果执行失败
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        deeplog_error = handle_error(e, error_context)
        raise deeplog_error from e