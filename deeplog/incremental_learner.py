"""
增量学习模块
支持在线更新模型以适应新模式
"""

from typing import List, Tuple, Optional
from collections import deque
from .parser import LogParser, LogEntry
from .models import LogKeyModel
from .utils import create_sequences, build_vocabulary


class IncrementalLearner:
    """增量学习器"""
    
    def __init__(self, log_key_model: LogKeyModel, 
                 window_size: int,
                 learning_rate: float = 0.001,
                 batch_size: int = 1):
        """
        初始化增量学习器
        
        Args:
            log_key_model: 日志键模型
            window_size: 窗口大小
            learning_rate: 学习率
            batch_size: 批次大小（用于批量更新）
        """
        self.log_key_model = log_key_model
        self.window_size = window_size
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        
        # 存储待更新的样本
        self.update_buffer = deque(maxlen=100)  # 最多缓存100个样本
        self.parser = LogParser()
        
    def add_false_positive(self, log_line: str, timestamp=None):
        """
        添加假阳性样本（正常但被误判为异常）
        
        Args:
            log_line: 日志行
            timestamp: 时间戳
        """
        entry = self.parser.parse(log_line, timestamp)
        self.update_buffer.append(('false_positive', entry))
    
    def add_new_pattern(self, log_sequence: List[str]):
        """
        添加新的正常模式
        
        Args:
            log_sequence: 日志键序列
        """
        if len(log_sequence) >= self.window_size + 1:
            self.update_buffer.append(('new_pattern', log_sequence))
    
    def update_model(self, epochs: int = 1):
        """
        更新模型
        
        Args:
            epochs: 训练轮数
        """
        if len(self.update_buffer) < self.batch_size:
            return  # 样本不足，不更新
        
        # 准备训练数据
        sequences = []
        labels = []
        
        for item in self.update_buffer:
            if item[0] == 'false_positive':
                # 假阳性：需要从历史中构建序列
                # 这里简化处理，实际需要维护历史窗口
                continue
            elif item[0] == 'new_pattern':
                # 新模式：直接使用序列
                seq = item[1]
                if len(seq) >= self.window_size + 1:
                    seqs, labs = create_sequences(seq, self.window_size)
                    sequences.extend(seqs)
                    labels.extend(labs)
        
        if not sequences:
            return
        
        # 准备训练数据（将标签添加到序列末尾）
        training_sequences = [seq + [label] for seq, label in zip(sequences, labels)]
        
        # 更新模型（使用较小的学习率进行微调）
        if self.log_key_model.model:
            # 使用较小的学习率进行增量更新
            original_lr = self.log_key_model.model.optimizer.learning_rate.numpy()
            self.log_key_model.model.optimizer.learning_rate.assign(self.learning_rate)
            
            try:
                X, y = self.log_key_model.prepare_sequences(training_sequences)
                if len(X) > 0:
                    self.log_key_model.model.fit(
                        X, y,
                        epochs=epochs,
                        batch_size=min(self.batch_size, len(X)),
                        verbose=0
                    )
            finally:
                # 恢复原始学习率
                self.log_key_model.model.optimizer.learning_rate.assign(original_lr)
        
        # 清空缓冲区
        self.update_buffer.clear()
    
    def update_vocabulary(self, new_log_keys: List[str]):
        """
        更新词汇表（添加新的日志键）
        
        Args:
            new_log_keys: 新的日志键列表
        """
        if not self.log_key_model.vocab:
            return
        
        # 检查是否有新键
        new_keys = [key for key in new_log_keys if key not in self.log_key_model.vocab]
        if not new_keys:
            return
        
        # 扩展词汇表
        current_size = len(self.log_key_model.vocab)
        for i, key in enumerate(new_keys):
            self.log_key_model.vocab[key] = current_size + i
        
        # 更新反向词汇表
        self.log_key_model.reverse_vocab = {
            v: k for k, v in self.log_key_model.vocab.items()
        }
        
        # 重建模型（需要增加输出层大小）
        old_vocab_size = self.log_key_model.vocab_size
        self.log_key_model.vocab_size = len(self.log_key_model.vocab)
        
        if self.log_key_model.model:
            # 需要重新构建模型以支持新的词汇表大小
            # 这里简化处理：提示用户需要重新训练
            print(f"警告：检测到 {len(new_keys)} 个新日志键，建议重新训练模型以包含这些键")

