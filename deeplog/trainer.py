"""
训练模块 (优化版本)
"""

from typing import List, Dict, Callable
from .parser import LogParser, LogEntry
from .models import LogKeyModel, ParameterValueModel
from .utils import (
    build_vocabulary, create_sequences, create_sequences_numpy,
    one_hot_encode_batch, memory_efficient_processing, optimize_memory_usage
)
from .parallel_processor import ParallelProcessor, MemoryManager, create_optimized_processor
from .exceptions import TrainingError, ValidationError, MemoryError, safe_execute
from collections import defaultdict
import numpy as np
import gc


class DeepLogTrainer:
    """DeepLog训练器 (优化版本)"""

    def __init__(self, window_size: int = 10, lstm_layers: int = 2, lstm_units: int = 64,
                 use_numpy_optimization: bool = True, batch_processing_size: int = 1000,
                 enable_parallel: bool = True, n_jobs: int = -1):
        """
        初始化训练器

        Args:
            window_size: 历史窗口大小
            lstm_layers: LSTM层数
            lstm_units: 每层LSTM单元数
            use_numpy_optimization: 是否使用NumPy优化
            batch_processing_size: 批处理大小
            enable_parallel: 是否启用并行处理
            n_jobs: 并行作业数 (-1表示使用所有CPU核心)
        """
        self.window_size = window_size
        self.lstm_layers = lstm_layers
        self.lstm_units = lstm_units
        self.use_numpy_optimization = use_numpy_optimization
        self.batch_processing_size = batch_processing_size
        self.enable_parallel = enable_parallel
        self.n_jobs = n_jobs
        self.parser = LogParser()

        # 初始化并行处理器和内存管理器
        if enable_parallel:
            self.parallel_processor = create_optimized_processor(n_jobs)
        else:
            self.parallel_processor = None

        self.memory_manager = MemoryManager()

    def train_log_key_model(self, log_entries: List[LogEntry],
                           epochs: int = 10, batch_size: int = 32) -> LogKeyModel:
        """
        训练日志键异常检测模型 (优化版本)

        Args:
            log_entries: 正常日志条目列表
            epochs: 训练轮数
            batch_size: 批次大小

        Returns:
            训练好的LogKeyModel

        Raises:
            ValidationError: 输入数据无效
            TrainingError: 训练失败
            MemoryError: 内存不足
        """
        if not isinstance(log_entries, list):
            raise ValidationError(
                f"log_entries必须是列表，当前类型: {type(log_entries)}",
                field="log_entries",
                expected_type="list"
            )

        if len(log_entries) == 0:
            raise ValidationError(
                "log_entries不能为空列表",
                field="log_entries"
            )

        # 检查内存使用
        if self.memory_manager:
            memory_usage = self.memory_manager.get_memory_usage()
            if memory_usage.get('percent', 0) > 80:
                print("警告: 内存使用率较高，可能影响训练性能")

        # 提取日志键序列
        try:
            log_keys = safe_execute(
                lambda: [entry.log_key for entry in log_entries],
                error_context="提取日志键序列"
            )
        except Exception as e:
            raise ValidationError(
                f"提取日志键失败: {e}",
                field="log_entries"
            )

        # 构建词汇表
        vocab = build_vocabulary(log_keys)
        vocab_size = len(vocab)

        if vocab_size == 0:
            raise ValidationError(
                "没有有效的日志键，请检查日志解析是否正确",
                field="log_entries"
            )

        # 创建训练序列 (使用优化版本)
        # 注意：NumPy优化目前只适用于数值序列，字符串序列使用标准批处理
        try:
            sequences, labels = create_sequences(log_keys, self.window_size, self.batch_processing_size)
        except Exception as e:
            raise TrainingError(
                f"创建训练序列失败: {e}",
                stage="data_preparation",
                model_type="LogKeyModel"
            )

        if len(sequences) == 0:
            raise ValidationError(
                f"序列长度不足，需要至少{self.window_size + 1}个日志条目",
                field="log_entries",
                suggestion=f"提供更多日志数据，至少需要{self.window_size + 1}个条目"
            )

        # 内存优化：分批处理序列构建
        try:
            training_sequences = self._build_training_sequences_optimized(sequences, labels)
        except MemoryError:
            raise MemoryError(
                "构建训练序列时内存不足",
                suggestion="减小batch_processing_size或增加系统内存"
            )

        # 创建并训练模型
        try:
            model = LogKeyModel(vocab_size, self.window_size, self.lstm_layers, self.lstm_units)
            model.set_vocab(vocab)
            model.build_model()

            # 使用批处理训练以节省内存
            model.train_with_memory_optimization(training_sequences, epochs=epochs, batch_size=batch_size)

        except Exception as e:
            raise TrainingError(
                f"模型训练失败: {e}",
                stage="training_loop",
                model_type="LogKeyModel"
            )

        # 清理内存
        optimize_memory_usage()

        return model

    def _build_training_sequences_optimized(self, sequences, labels):
        """
        优化的训练序列构建 (内存高效)

        Args:
            sequences: 输入序列
            labels: 标签

        Returns:
            训练序列
        """
        # 直接构建训练序列 - 简单有效的方法
        training_sequences = [seq + [label] for seq, label in zip(sequences, labels)]

        # 如果序列太多，进行批处理清理
        if len(training_sequences) > self.batch_processing_size:
            # 定期清理内存
            gc.collect()

        return training_sequences

    def train_parameter_models(self, log_entries: List[LogEntry],
                               epochs: int = 10, batch_size: int = 32) -> Dict[str, ParameterValueModel]:
        """
        训练参数值异常检测模型 (优化版本)

        Args:
            log_entries: 正常日志条目列表
            epochs: 训练轮数
            batch_size: 批次大小

        Returns:
            日志键到模型的映射字典
        """
        # 按日志键分组 (内存优化)
        key_to_entries = defaultdict(list)

        # 分批处理以减少内存使用
        for i in range(0, len(log_entries), self.batch_processing_size):
            batch_entries = log_entries[i:i + self.batch_processing_size]
            for entry in batch_entries:
                if entry.parameters:  # 只处理有参数的日志
                    key_to_entries[entry.log_key].append(entry)

            if i % (self.batch_processing_size * 10) == 0:
                gc.collect()

        models = {}

        if self.enable_parallel and self.parallel_processor and len(key_to_entries) > 5:
            # 使用并行处理训练多个参数模型
            print(f"使用并行处理训练 {len(key_to_entries)} 个参数模型...")

            def create_param_model(log_key: str, entries: List[LogEntry]) -> tuple:
                """为单个日志键创建参数模型"""
                try:
                    if len(entries) < self.window_size + 1:
                        return log_key, None

                    # 提取参数值序列
                    param_sequences = [entry.parameters for entry in entries]

                    # 确定最常见的特征维度
                    from collections import Counter
                    dim_counts = Counter(len(params) for params in param_sequences if len(params) > 0)

                    if not dim_counts:
                        return log_key, None

                    # 使用最常见的维度
                    target_dim = dim_counts.most_common(1)[0][0]

                    # 过滤并填充参数序列
                    filtered_sequences = []
                    for params in param_sequences:
                        if len(params) == target_dim and all(isinstance(p, (int, float)) for p in params):
                            filtered_sequences.append(params)

                    if len(filtered_sequences) < self.window_size + 1:
                        return log_key, None

                    # 创建训练序列
                    sequences, labels = create_sequences(filtered_sequences, self.window_size)

                    if len(sequences) == 0:
                        return log_key, None

                    # 创建参数值模型
                    model = ParameterValueModel(target_dim, self.window_size, epochs=epochs, batch_size=batch_size)
                    model.train(sequences, labels)

                    return log_key, model

                except Exception as e:
                    print(f"训练参数模型失败 {log_key}: {e}")
                    return log_key, None

            # 并行训练
            models = self.parallel_processor.process_parameter_models_parallel(
                key_to_entries, create_param_model
            )

            # 过滤掉None结果
            models = {k: v for k, v in models.items() if v is not None}

        else:
            # 顺序处理
            print(f"顺序训练 {len(key_to_entries)} 个参数模型...")

            for log_key, entries in key_to_entries.items():
                if len(entries) < self.window_size + 1:
                    continue  # 序列太短，跳过

                try:
                    # 提取参数值序列 (优化版本)
                    param_sequences = [entry.parameters for entry in entries]

                    # 确定最常见的特征维度 (优化)
                    from collections import Counter
                    dim_counts = Counter(len(params) for params in param_sequences if len(params) > 0)

                    if not dim_counts:
                        continue

                    # 使用最常见的维度
                    target_dim = dim_counts.most_common(1)[0][0]

                    # 过滤并填充参数序列
                    filtered_sequences = []
                    for params in param_sequences:
                        if len(params) == target_dim and all(isinstance(p, (int, float)) for p in params):
                            filtered_sequences.append(params)

                    if len(filtered_sequences) < self.window_size + 1:
                        continue

                    # 创建训练序列
                    sequences, labels = create_sequences(filtered_sequences, self.window_size)

                    if len(sequences) == 0:
                        continue

                    # 创建参数值模型
                    model = ParameterValueModel(target_dim, self.window_size, epochs=epochs, batch_size=batch_size)
                    model.train(sequences, labels)

                    models[log_key] = model

                except Exception as e:
                    # 记录错误但继续处理其他模型
                    print(f"训练参数模型失败 {log_key}: {e}")
                    continue

                # 定期清理内存
                if len(models) % 10 == 0:
                    optimize_memory_usage()

        # 最终内存清理
        optimize_memory_usage()

        return models