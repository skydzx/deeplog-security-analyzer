# Exception Handling and Error Management - 异常处理和错误管理技能

## 技能概述

DeepLog 项目的异常处理体系设计和实现技能。专注于创建健壮的错误处理机制，提供用户友好的错误信息和详细的诊断功能。

## 适用场景

- **异常类设计**: 创建层次化的异常体系
- **错误处理策略**: 实现优雅的错误恢复
- **用户体验优化**: 提供清晰的错误信息和修复建议
- **调试支持**: 实现详细的错误诊断和日志记录
- **API设计**: 设计错误友好的接口

## 核心异常体系

### 1. 异常类层次结构

```python
"""
DeepLog 异常类层次结构
遵循单一职责原则和开闭原则
"""

class DeepLogError(Exception):
    """
    基础异常类

    所有 DeepLog 异常的根类，提供统一的错误处理接口
    """

    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None,
                 suggestion: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.suggestion = suggestion

    def __str__(self):
        parts = [f"[{self.error_code}] {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典，便于 API 返回"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
            "timestamp": datetime.now().isoformat()
        }


# 按功能分类的异常类
class ModelError(DeepLogError):
    """模型相关异常"""
    pass

class DataError(DeepLogError):
    """数据相关异常"""
    pass

class ConfigurationError(DeepLogError):
    """配置相关异常"""
    pass

class ResourceError(DeepLogError):
    """资源相关异常"""
    pass

# 具体异常类
class TrainingError(ModelError):
    """训练过程异常"""
    def __init__(self, message: str, stage: str = None, model_type: str = None, **kwargs):
        super().__init__(message, error_code="TRAINING_ERROR", **kwargs)
        self.details.update({
            "stage": stage,  # "data_preparation", "model_compilation", "training_loop"
            "model_type": model_type,  # "LogKeyModel", "ParameterValueModel"
        })

class PredictionError(ModelError):
    """预测过程异常"""
    def __init__(self, message: str, model_type: str = None, input_shape: tuple = None, **kwargs):
        super().__init__(message, error_code="PREDICTION_ERROR", **kwargs)
        self.details.update({
            "model_type": model_type,
            "input_shape": input_shape,
        })

class ParsingError(DataError):
    """日志解析异常"""
    def __init__(self, message: str, line_content: str = None, parser_type: str = None, **kwargs):
        super().__init__(message, error_code="PARSING_ERROR", **kwargs)
        self.details.update({
            "line_content": line_content,
            "parser_type": parser_type,
        })

class ValidationError(DataError):
    """数据验证异常"""
    def __init__(self, message: str, field: str = None, value: Any = None,
                 expected_type: str = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.details.update({
            "field": field,
            "value": str(value) if value is not None else None,
            "expected_type": expected_type,
        })

class MemoryError(ResourceError):
    """内存不足异常"""
    def __init__(self, message: str, requested_mb: int = None,
                 available_mb: int = None, **kwargs):
        super().__init__(message, error_code="MEMORY_ERROR", **kwargs)
        self.details.update({
            "requested_mb": requested_mb,
            "available_mb": available_mb,
        })
        if available_mb and requested_mb:
            self.suggestion = f"减少批次大小或增加内存。当前可用: {available_mb}MB, 请求: {requested_mb}MB"

class FileSystemError(ResourceError):
    """文件系统异常"""
    def __init__(self, message: str, file_path: str = None,
                 operation: str = None, **kwargs):  # "read", "write", "create", "delete"
        super().__init__(message, error_code="FILESYSTEM_ERROR", **kwargs)
        self.details.update({
            "file_path": file_path,
            "operation": operation,
        })
```

### 2. 错误处理策略

```python
class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def safe_execute(func: Callable, *args, error_context: str = "",
                    **kwargs) -> Any:
        """
        安全执行函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            error_context: 错误上下文描述
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            DeepLogError: 执行失败时抛出
        """
        try:
            return func(*args, **kwargs)
        except DeepLogError:
            raise  # 重新抛出 DeepLog 异常
        except Exception as e:
            # 将普通异常转换为 DeepLog 异常
            deeplog_error = ErrorHandler.handle_error(e, error_context)
            raise deeplog_error from e

    @staticmethod
    def handle_error(error: Exception, context: str = "") -> DeepLogError:
        """
        将普通异常转换为 DeepLog 异常

        Args:
            error: 原始异常
            context: 错误上下文

        Returns:
            DeepLogError: 转换后的异常
        """
        message = f"{context}: {str(error)}" if context else str(error)

        # 根据异常类型智能映射
        if isinstance(error, (tf.errors.ResourceExhaustedError, MemoryError)):
            return MemoryError(message, suggestion="尝试减小批次大小或使用更小的模型")
        elif isinstance(error, (OSError, IOError)):
            return FileSystemError(message, suggestion="检查文件权限和磁盘空间")
        elif isinstance(error, ValueError):
            return ValidationError(message, suggestion="检查输入数据的格式和范围")
        elif isinstance(error, tf.errors.InvalidArgumentError):
            return ModelError(message, suggestion="检查模型输入的形状和类型")
        else:
            return DeepLogError(message, suggestion="检查错误详情并重试")

    @staticmethod
    def with_error_handling(error_context: str = ""):
        """
        装饰器：为函数添加错误处理

        Args:
            error_context: 错误上下文描述
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return ErrorHandler.safe_execute(
                    func, *args, error_context=error_context, **kwargs
                )
            return wrapper
        return decorator

    @staticmethod
    def validate_input(**validators):
        """
        输入验证装饰器

        Args:
            **validators: 验证器字典
                key: 参数名
                value: (validator_func, error_message)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取函数签名
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # 验证参数
                for param_name, (validator, error_msg) in validators.items():
                    if param_name in bound_args.arguments:
                        value = bound_args.arguments[param_name]
                        if not validator(value):
                            raise ValidationError(
                                error_msg,
                                field=param_name,
                                value=value
                            )

                return func(*args, **kwargs)
            return wrapper
        return decorator
```

### 3. 错误恢复策略

```python
class ErrorRecovery:
    """错误恢复策略"""

    def __init__(self):
        self.recovery_strategies = {
            'memory_error': self._recover_from_memory_error,
            'filesystem_error': self._recover_from_filesystem_error,
            'network_error': self._recover_from_network_error,
            'model_error': self._recover_from_model_error,
        }

    def attempt_recovery(self, error: DeepLogError, context: Dict = None) -> bool:
        """
        尝试错误恢复

        Args:
            error: 发生的错误
            context: 恢复上下文

        Returns:
            是否成功恢复
        """
        strategy_name = self._get_recovery_strategy(error)
        if strategy_name in self.recovery_strategies:
            try:
                return self.recovery_strategies[strategy_name](error, context)
            except Exception as e:
                logger.warning(f"恢复策略失败: {e}")
                return False
        return False

    def _recover_from_memory_error(self, error: MemoryError, context: Dict) -> bool:
        """内存错误恢复"""
        # 1. 强制垃圾回收
        import gc
        gc.collect()

        # 2. 减小批次大小
        if 'trainer' in context:
            trainer = context['trainer']
            if hasattr(trainer, 'batch_size'):
                trainer.batch_size = max(1, trainer.batch_size // 2)
                logger.info(f"批次大小减小到: {trainer.batch_size}")
                return True

        # 3. 释放未使用的模型
        if 'model_cache' in context:
            model_cache = context['model_cache']
            model_cache.clear_unused_models()

        return False

    def _recover_from_filesystem_error(self, error: FileSystemError, context: Dict) -> bool:
        """文件系统错误恢复"""
        # 1. 检查并创建目录
        if error.details.get('operation') == 'create_directory':
            file_path = error.details.get('file_path')
            if file_path:
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    return True
                except Exception:
                    pass

        # 2. 尝试备用路径
        if 'backup_paths' in context:
            backup_paths = context['backup_paths']
            for backup_path in backup_paths:
                try:
                    # 尝试在备用路径上执行操作
                    self._try_backup_operation(error, backup_path)
                    return True
                except Exception:
                    continue

        return False

    def _recover_from_model_error(self, error: DeepLogError, context: Dict) -> bool:
        """模型错误恢复"""
        # 1. 重新加载模型
        if 'model_path' in context:
            model_path = context['model_path']
            try:
                model = self._reload_model(model_path)
                context['model'] = model
                return True
            except Exception:
                pass

        # 2. 使用备用模型
        if 'backup_model' in context:
            backup_model = context['backup_model']
            context['model'] = backup_model
            return True

        return False
```

## 错误信息设计原则

### 1. 用户友好的错误信息

```python
class ErrorMessageDesigner:
    """错误信息设计器"""

    ERROR_MESSAGES = {
        "MEMORY_ERROR": {
            "user_friendly": "系统内存不足",
            "technical": "TensorFlow/Keras 内存分配失败",
            "suggestions": [
                "减少批次大小 (batch_size)",
                "使用更小的模型架构",
                "增加系统内存",
                "启用内存增长: tf.config.experimental.set_memory_growth"
            ]
        },
        "VALIDATION_ERROR": {
            "user_friendly": "输入数据格式不正确",
            "technical": "数据类型或值范围不符合要求",
            "suggestions": [
                "检查输入数据的类型",
                "确认数值范围在有效区间内",
                "查看数据预处理步骤"
            ]
        }
    }

    @staticmethod
    def create_user_message(error: DeepLogError, language: str = "zh") -> str:
        """创建用户友好的错误信息"""
        error_type = error.error_code

        if error_type in ErrorMessageDesigner.ERROR_MESSAGES:
            template = ErrorMessageDesigner.ERROR_MESSAGES[error_type]
            message = template["user_friendly"]

            if error.details:
                message += f" (详情: {error.details})"

            if template["suggestions"]:
                message += "\n建议解决方案:"
                for i, suggestion in enumerate(template["suggestions"], 1):
                    message += f"\n{i}. {suggestion}"

            return message
        else:
            return str(error)
```

### 2. 错误日志记录

```python
class ErrorLogger:
    """错误日志记录器"""

    def __init__(self, log_file: str = "deeplog_errors.log"):
        self.log_file = log_file
        self.setup_logger()

    def setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger('DeepLog.Errors')
        self.logger.setLevel(logging.ERROR)

        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log_error(self, error: DeepLogError, context: Dict = None):
        """记录错误"""
        error_dict = error.to_dict()
        if context:
            error_dict['context'] = context

        # 结构化日志
        self.logger.error("DeepLog Error", extra={
            'error_data': error_dict,
            'stack_trace': traceback.format_exc()
        })

    def log_recovery_attempt(self, error: DeepLogError, success: bool,
                           strategy: str = None):
        """记录恢复尝试"""
        self.logger.info(f"错误恢复尝试: {error.error_code}, 成功: {success}",
                        extra={
                            'recovery': {
                                'error_code': error.error_code,
                                'success': success,
                                'strategy': strategy,
                                'timestamp': datetime.now().isoformat()
                            }
                        })
```

## 测试和验证

### 1. 异常处理测试

```python
class TestExceptionHandling:
    """异常处理测试"""

    def test_error_hierarchy(self):
        """测试异常层次结构"""
        # 测试继承关系
        assert issubclass(TrainingError, ModelError)
        assert issubclass(ModelError, DeepLogError)
        assert issubclass(DeepLogError, Exception)

    def test_error_serialization(self):
        """测试错误序列化"""
        error = ValidationError(
            "无效参数",
            field="batch_size",
            value=-1,
            suggestion="批次大小必须为正整数"
        )

        error_dict = error.to_dict()
        assert error_dict['error_code'] == 'VALIDATION_ERROR'
        assert 'field' in error_dict['details']
        assert 'suggestion' in error_dict

    def test_safe_execute_success(self):
        """测试安全执行成功情况"""
        def successful_func(x, y):
            return x + y

        result = ErrorHandler.safe_execute(
            successful_func, 1, 2,
            error_context="测试函数"
        )
        assert result == 3

    def test_safe_execute_failure(self):
        """测试安全执行失败情况"""
        def failing_func():
            raise ValueError("测试错误")

        with pytest.raises(DeepLogError) as exc_info:
            ErrorHandler.safe_execute(
                failing_func,
                error_context="测试函数"
            )

        assert exc_info.value.error_code == "UNKNOWN_ERROR"
        assert "测试函数" in str(exc_info.value)

    def test_error_recovery(self):
        """测试错误恢复"""
        recovery = ErrorRecovery()

        # 模拟内存错误
        memory_error = MemoryError("内存不足")
        context = {'trainer': type('MockTrainer', (), {'batch_size': 64})()}

        success = recovery.attempt_recovery(memory_error, context)
        assert success  # 应该成功减小批次大小
        assert context['trainer'].batch_size == 32
```

### 2. 集成测试

```python
class TestErrorIntegration:
    """异常处理集成测试"""

    def test_end_to_end_error_handling(self):
        """端到端错误处理测试"""
        # 创建一个会失败的操作
        deeplog = DeepLog(window_size=10)

        # 测试无效输入
        with pytest.raises(ValidationError) as exc_info:
            deeplog.train([])  # 空列表

        error = exc_info.value
        assert error.error_code == "VALIDATION_ERROR"
        assert "log_lines" in str(error)

        # 验证错误信息完整性
        assert error.details['field'] == 'log_lines'
        assert error.suggestion is not None

    def test_error_logging(self):
        """测试错误日志记录"""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name

        try:
            logger = ErrorLogger(log_file)
            error = TrainingError("训练失败", stage="data_preparation")

            logger.log_error(error, {'user_id': 'test_user'})

            # 验证日志文件
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
                assert 'TRAINING_ERROR' in log_content
                assert 'data_preparation' in log_content

        finally:
            os.unlink(log_file)
```

## 最佳实践

### 1. 异常处理原则

```python
# ✅ 推荐做法
def good_error_handling():
    """良好的错误处理"""
    try:
        # 核心逻辑
        result = risky_operation()
        return result
    except SpecificException as e:
        # 具体异常处理
        logger.warning(f"特定错误: {e}")
        return fallback_result()
    except Exception as e:
        # 通用异常处理
        logger.error(f"意外错误: {e}")
        raise DeepLogError("操作失败", suggestion="联系技术支持") from e

# ❌ 避免的做法
def bad_error_handling():
    """不好的错误处理"""
    try:
        result = risky_operation()
    except:  # 捕获所有异常，不推荐
        pass  # 静默失败，不推荐
```

### 2. 错误信息设计

```python
# ✅ 好的错误信息
error = ValidationError(
    "批次大小无效",
    field="batch_size",
    value=-1,
    expected_type="正整数",
    suggestion="请提供一个正整数值，最小值为1"
)

# ❌ 不好的错误信息
error = ValueError("批次大小必须 > 0")  # 缺乏上下文和建议
```

### 3. 资源清理

```python
# ✅ 正确的资源清理
def with_resource_cleanup():
    resource = None
    try:
        resource = acquire_resource()
        return process_resource(resource)
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
    finally:
        if resource:
            resource.close()  # 确保资源被释放

# 使用装饰器简化
@ErrorHandler.with_error_handling("资源处理")
def safe_resource_operation():
    with managed_resource() as resource:
        return process_resource(resource)
```

这个技能规范为 DeepLog 项目提供了完整的异常处理体系，帮助开发人员编写健壮、用户友好的代码。