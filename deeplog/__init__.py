"""
DeepLog: 基于深度学习的系统日志异常检测框架
"""

from .deeplog import DeepLog
from .parser import LogParser
from .models import LogKeyModel, ParameterValueModel
from .workflow import WorkflowBuilder, WorkflowModel
from .evaluator import Evaluator, evaluate_on_dataset, compare_methods
from .exceptions import (
    DeepLogError, ModelError, TrainingError, PredictionError,
    DataError, ParsingError, ValidationError, ConfigurationError,
    ResourceError, MemoryError, FileSystemError, ParallelProcessingError,
    handle_error, safe_execute
)

__version__ = "0.1.0"
__all__ = [
    "DeepLog",
    "LogParser",
    "LogKeyModel",
    "ParameterValueModel",
    "WorkflowBuilder",
    "WorkflowModel",
    "Evaluator",
    "evaluate_on_dataset",
    "compare_methods",
    # 异常类
    "DeepLogError", "ModelError", "TrainingError", "PredictionError",
    "DataError", "ParsingError", "ValidationError", "ConfigurationError",
    "ResourceError", "MemoryError", "FileSystemError", "ParallelProcessingError",
    "handle_error", "safe_execute"
]

