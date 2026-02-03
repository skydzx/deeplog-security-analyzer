"""
异常检测模块
"""

from typing import List, Tuple, Optional, Dict
from collections import deque
from .parser import LogParser, LogEntry
from .models import LogKeyModel, ParameterValueModel


class DeepLogDetector:
    """DeepLog异常检测器"""
    
    def __init__(self, log_key_model: LogKeyModel, 
                 parameter_models: Dict[str, ParameterValueModel],
                 top_g: int = 5):
        """
        初始化检测器
        
        Args:
            log_key_model: 日志键异常检测模型
            parameter_models: 参数值异常检测模型字典（按日志键索引）
            top_g: top-g个候选键被视为正常
        """
        self.log_key_model = log_key_model
        self.parameter_models = parameter_models
        self.top_g = top_g
        self.parser = LogParser()
        
        # 维护历史窗口
        self.key_history = deque(maxlen=log_key_model.window_size)
        self.param_history = {}  # 按日志键维护历史
        
    def detect(self, log_entry: LogEntry) -> Tuple[bool, str, Dict]:
        """
        检测日志条目是否异常
        
        Args:
            log_entry: 日志条目
            
        Returns:
            (是否异常, 异常类型, 详细信息)
        """
        details = {
            'log_key': log_entry.log_key,
            'key_anomaly': False,
            'parameter_anomaly': False,
            'predictions': None,
            'mse': None
        }
        
        # 1. 检测日志键异常
        is_key_anomaly = self._detect_key_anomaly(log_entry.log_key)
        details['key_anomaly'] = is_key_anomaly
        details['predictions'] = self._get_predictions()
        
        if is_key_anomaly:
            self.key_history.append(log_entry.log_key)
            return True, "执行路径异常", details
        
        # 2. 如果日志键正常，检测参数值异常
        if log_entry.log_key in self.parameter_models and log_entry.parameters:
            is_param_anomaly, mse = self._detect_parameter_anomaly(
                log_entry.log_key, log_entry.parameters
            )
            details['parameter_anomaly'] = is_param_anomaly
            details['mse'] = mse
            
            if is_param_anomaly:
                # 更新历史
                self.key_history.append(log_entry.log_key)
                self._update_param_history(log_entry.log_key, log_entry.parameters)
                return True, "参数值异常", details
        
        # 正常，更新历史
        self.key_history.append(log_entry.log_key)
        if log_entry.parameters:
            self._update_param_history(log_entry.log_key, log_entry.parameters)
        
        return False, "正常", details
    
    def _detect_key_anomaly(self, log_key: str) -> bool:
        """检测日志键是否异常"""
        # 检查日志键是否在词汇表中（训练时是否见过）
        if self.log_key_model.vocab and log_key not in self.log_key_model.vocab:
            # 未在训练数据中出现的日志键，视为异常
            return True
        
        if len(self.key_history) < self.log_key_model.window_size:
            # 历史不足，无法检测，视为正常
            return False
        
        # 获取预测
        history = list(self.key_history)
        predictions = self.log_key_model.predict(history, top_k=self.top_g)
        
        # 检查实际日志键是否在top-g预测中
        predicted_keys = [key for key, _ in predictions]
        return log_key not in predicted_keys
    
    def _get_predictions(self) -> List[Tuple[str, float]]:
        """获取当前预测结果"""
        if len(self.key_history) < self.log_key_model.window_size:
            return []
        
        history = list(self.key_history)
        return self.log_key_model.predict(history, top_k=self.top_g)
    
    def _detect_parameter_anomaly(self, log_key: str, parameters: List[float]) -> Tuple[bool, float]:
        """检测参数值是否异常"""
        if log_key not in self.parameter_models:
            return False, 0.0
        
        model = self.parameter_models[log_key]
        
        # 获取该日志键的历史
        if log_key not in self.param_history:
            self.param_history[log_key] = deque(maxlen=model.window_size)
        
        history = self.param_history[log_key]
        
        if len(history) < model.window_size:
            # 历史不足，无法检测
            return False, 0.0
        
        # 检测异常
        is_anomaly, mse = model.is_anomaly(list(history), parameters)
        return is_anomaly, mse
    
    def _update_param_history(self, log_key: str, parameters: List[float]):
        """更新参数历史"""
        if log_key not in self.param_history:
            self.param_history[log_key] = deque(maxlen=self.log_key_model.window_size)
        
        self.param_history[log_key].append(parameters)
    
    def reset(self):
        """重置检测器状态（清空历史）"""
        self.key_history.clear()
        self.param_history.clear()

