"""
LSTM模型定义模块
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from typing import List, Dict, Tuple, Optional
import pickle
import os


class LogKeyModel:
    """
    日志键异常检测模型
    使用LSTM预测下一个日志键
    """
    
    def __init__(self, vocab_size: int, window_size: int = 10, 
                 lstm_layers: int = 2, lstm_units: int = 64):
        """
        初始化模型
        
        Args:
            vocab_size: 词汇表大小（不同日志键的数量）
            window_size: 历史窗口大小
            lstm_layers: LSTM层数
            lstm_units: 每层LSTM单元数
        """
        self.vocab_size = vocab_size
        self.window_size = window_size
        self.lstm_layers = lstm_layers
        self.lstm_units = lstm_units
        self.model = None
        self.vocab = None
        self.reverse_vocab = None
        
    def build_model(self):
        """构建LSTM模型"""
        model = keras.Sequential()
        
        # 输入层：one-hot编码的日志键序列
        model.add(layers.Input(shape=(self.window_size, self.vocab_size)))
        
        # LSTM层
        for i in range(self.lstm_layers):
            return_sequences = (i < self.lstm_layers - 1)
            model.add(layers.LSTM(
                self.lstm_units,
                return_sequences=return_sequences,
                dropout=0.2,
                recurrent_dropout=0.2
            ))
        
        # 输出层：softmax分类
        model.add(layers.Dense(self.vocab_size, activation='softmax'))
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def set_vocab(self, vocab: Dict[str, int]):
        """设置词汇表"""
        self.vocab = vocab
        self.reverse_vocab = {v: k for k, v in vocab.items()}
        self.vocab_size = len(vocab)
    
    def prepare_sequences(self, sequences: List[List[str]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            sequences: 日志键序列列表
            
        Returns:
            (输入序列, 标签)
        """
        X = []
        y = []
        
        for seq in sequences:
            if len(seq) != self.window_size + 1:
                continue
                
            # 输入：前window_size个键
            input_seq = seq[:-1]
            # 标签：最后一个键
            label = seq[-1]
            
            # 转换为one-hot编码
            input_one_hot = np.array([
                self._one_hot_encode(key) for key in input_seq
            ])
            label_one_hot = self._one_hot_encode(label)
            
            X.append(input_one_hot)
            y.append(label_one_hot)
        
        return np.array(X), np.array(y)
    
    def _one_hot_encode(self, key: str) -> np.ndarray:
        """将日志键编码为one-hot向量"""
        if self.vocab is None:
            raise ValueError("词汇表未设置")
        
        one_hot = np.zeros(self.vocab_size)
        if key in self.vocab:
            one_hot[self.vocab[key]] = 1.0
        return one_hot
    
    def train(self, sequences: List[List[str]], epochs: int = 10, 
              batch_size: int = 32, validation_split: float = 0.1):
        """
        训练模型
        
        Args:
            sequences: 训练序列
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
        """
        if self.model is None:
            self.build_model()
        
        X, y = self.prepare_sequences(sequences)
        
        if len(X) == 0:
            raise ValueError("没有有效的训练序列")
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        return history

    def train_with_memory_optimization(self, sequences: List[List[str]], epochs: int = 10,
                                      batch_size: int = 32, validation_split: float = 0.1,
                                      memory_batch_size: int = 1000):
        """
        内存优化的训练方法

        Args:
            sequences: 训练序列
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
            memory_batch_size: 内存批处理大小
        """
        if self.model is None:
            self.build_model()

        # 分批处理序列以节省内存
        total_sequences = len(sequences)
        train_size = int(total_sequences * (1 - validation_split))

        # 分批准备训练数据
        X_train_list = []
        y_train_list = []
        X_val_list = []
        y_val_list = []

        for start_idx in range(0, total_sequences, memory_batch_size):
            end_idx = min(start_idx + memory_batch_size, total_sequences)

            batch_sequences = sequences[start_idx:end_idx]
            X_batch, y_batch = self.prepare_sequences(batch_sequences)

            if start_idx < train_size:
                X_train_list.append(X_batch)
                y_train_list.append(y_batch)
            else:
                X_val_list.append(X_batch)
                y_val_list.append(y_batch)

            # 清理临时变量
            del X_batch, y_batch

        # 合并批次数据
        import gc
        X_train = np.concatenate(X_train_list, axis=0) if X_train_list else np.array([])
        y_train = np.concatenate(y_train_list, axis=0) if y_train_list else np.array([])
        X_val = np.concatenate(X_val_list, axis=0) if X_val_list else np.array([])
        y_val = np.concatenate(y_val_list, axis=0) if y_val_list else np.array([])

        # 清理列表
        del X_train_list, y_train_list, X_val_list, y_val_list
        gc.collect()

        if len(X_train) == 0:
            raise ValueError("没有有效的训练序列")

        # 使用生成器进行训练以进一步节省内存
        if len(X_val) > 0:
            validation_data = (X_val, y_val)
        else:
            validation_data = None

        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            verbose=1
        )

        # 清理训练数据
        del X_train, y_train
        if validation_data:
            del X_val, y_val
        gc.collect()

        return history

    def predict(self, history: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        预测下一个日志键
        
        Args:
            history: 历史日志键序列（长度应为window_size）
            top_k: 返回top-k个预测结果
            
        Returns:
            [(日志键, 概率)]列表，按概率降序排列
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        if len(history) != self.window_size:
            raise ValueError(f"历史序列长度应为{self.window_size}，实际为{len(history)}")
        
        # 准备输入
        input_seq = np.array([self._one_hot_encode(key) for key in history])
        input_seq = input_seq.reshape(1, self.window_size, self.vocab_size)
        
        # 预测
        predictions = self.model.predict(input_seq, verbose=0)[0]
        
        # 获取top-k
        top_indices = np.argsort(predictions)[-top_k:][::-1]
        results = [
            (self.reverse_vocab[i], float(predictions[i]))
            for i in top_indices
        ]
        
        return results
    
    def save(self, filepath: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        # 保存模型权重
        model_dir = os.path.dirname(filepath)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        
        self.model.save_weights(filepath + '.weights.h5')
        
        # 保存词汇表和配置
        config = {
            'vocab': self.vocab,
            'window_size': self.window_size,
            'lstm_layers': self.lstm_layers,
            'lstm_units': self.lstm_units,
            'vocab_size': self.vocab_size
        }
        with open(filepath + '.config.pkl', 'wb') as f:
            pickle.dump(config, f)
    
    def load(self, filepath: str):
        """加载模型"""
        # 加载配置
        with open(filepath + '.config.pkl', 'rb') as f:
            config = pickle.load(f)
        
        self.vocab = config['vocab']
        self.reverse_vocab = {v: k for k, v in self.vocab.items()}
        self.window_size = config['window_size']
        self.lstm_layers = config['lstm_layers']
        self.lstm_units = config['lstm_units']
        self.vocab_size = config['vocab_size']
        
        # 重建模型并加载权重
        self.build_model()
        self.model.load_weights(filepath + '.weights.h5')


class ParameterValueModel:
    """
    参数值异常检测模型
    使用LSTM检测参数值序列中的异常
    """
    
    def __init__(self, feature_dim: int, window_size: int = 10,
                 lstm_layers: int = 2, lstm_units: int = 64):
        """
        初始化模型
        
        Args:
            feature_dim: 特征维度（参数值向量的长度）
            window_size: 历史窗口大小
            lstm_layers: LSTM层数
            lstm_units: 每层LSTM单元数
        """
        self.feature_dim = feature_dim
        self.window_size = window_size
        self.lstm_layers = lstm_layers
        self.lstm_units = lstm_units
        self.model = None
        self.mean = None  # 全局均值（向后兼容）
        self.std = None   # 全局标准差（向后兼容）
        self.feature_means = None  # 每个特征维度的均值
        self.feature_stds = None   # 每个特征维度的标准差
        self.mse_threshold = None  # 异常检测阈值
        
    def build_model(self):
        """构建LSTM模型"""
        model = keras.Sequential()
        
        # 输入层
        model.add(layers.Input(shape=(self.window_size, self.feature_dim)))
        
        # LSTM层
        for i in range(self.lstm_layers):
            return_sequences = (i < self.lstm_layers - 1)
            model.add(layers.LSTM(
                self.lstm_units,
                return_sequences=return_sequences,
                dropout=0.2,
                recurrent_dropout=0.2
            ))
        
        # 输出层：回归预测
        model.add(layers.Dense(self.feature_dim))
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def normalize_parameters(self, sequences: List[List[List[float]]]) -> Tuple[List[List[List[float]]], np.ndarray, np.ndarray]:
        """
        归一化参数序列（按特征维度单独归一化）
        
        Args:
            sequences: 参数值序列列表（每个序列是 List[List[float]]）
            
        Returns:
            (归一化后的序列, 特征均值数组, 特征标准差数组)
        """
        # 收集所有参数向量
        all_params = []
        for seq in sequences:
            for params in seq:
                if len(params) == self.feature_dim:
                    all_params.append(params)
        
        if not all_params:
            # 如果没有有效数据，返回默认值
            self.feature_means = np.zeros(self.feature_dim)
            self.feature_stds = np.ones(self.feature_dim)
            self.mean = 0.0
            self.std = 1.0
            return sequences, self.feature_means, self.feature_stds
        
        # 转换为numpy数组
        all_params_array = np.array(all_params)  # shape: (n_samples, feature_dim)
        
        # 按特征维度计算统计量（每列单独计算）
        self.feature_means = np.mean(all_params_array, axis=0)  # shape: (feature_dim,)
        self.feature_stds = np.std(all_params_array, axis=0)   # shape: (feature_dim,)
        
        # 避免除零
        self.feature_stds = np.where(self.feature_stds == 0, 1.0, self.feature_stds)
        
        # 计算全局统计量（用于向后兼容）
        self.mean = np.mean(all_params_array)
        self.std = np.std(all_params_array)
        if self.std == 0:
            self.std = 1.0
        
        # 异常值裁剪：使用3-sigma规则
        # 计算每个特征维度的上下限
        feature_mins = self.feature_means - 3 * self.feature_stds
        feature_maxs = self.feature_means + 3 * self.feature_stds
        
        # 归一化并裁剪异常值
        normalized = []
        for seq in sequences:
            norm_seq = []
            for params in seq:
                if len(params) != self.feature_dim:
                    # 如果长度不匹配，跳过或填充
                    continue
                
                params_array = np.array(params)
                
                # 裁剪异常值
                params_array = np.clip(params_array, feature_mins, feature_maxs)
                
                # 按特征维度归一化
                norm_params = (params_array - self.feature_means) / self.feature_stds
                
                # 再次裁剪到合理范围（防止极端归一化值）
                norm_params = np.clip(norm_params, -5.0, 5.0)
                
                norm_seq.append(norm_params.tolist())
            
            if norm_seq:  # 只添加非空序列
                normalized.append(norm_seq)
        
        return normalized, self.feature_means, self.feature_stds
    
    def prepare_sequences(self, sequences: List[List[List[float]]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据（序列应该已经归一化）
        
        Args:
            sequences: 已归一化的参数值序列列表
            
        Returns:
            (输入序列, 标签)
        """
        X = []
        y = []
        
        for seq in sequences:
            if len(seq) < self.window_size + 1:
                continue
            
            # 序列应该已经归一化，直接使用
            for i in range(len(seq) - self.window_size):
                input_seq = seq[i:i + self.window_size]
                label = seq[i + self.window_size]
                
                # 确保长度匹配
                if len(input_seq) == self.window_size and len(label) == self.feature_dim:
                    X.append(input_seq)
                    y.append(label)
        
        if len(X) == 0:
            return np.array([]), np.array([])
        
        return np.array(X), np.array(y)
    
    def train(self, sequences: List[List[List[float]]], epochs: int = 10,
              batch_size: int = 32, validation_split: float = 0.1):
        """
        训练模型
        
        Args:
            sequences: 训练序列
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
        """
        if self.model is None:
            self.build_model()
        
        # 归一化并准备数据
        normalized, self.mean, self.std = self.normalize_parameters(sequences)
        X, y = self.prepare_sequences(normalized)
        
        if len(X) == 0:
            raise ValueError("没有有效的训练序列")
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        # 计算验证集上的MSE分布以确定阈值
        self._calculate_threshold(X, y, validation_split)
        
        return history
    
    def _calculate_threshold(self, X: np.ndarray, y: np.ndarray, validation_split: float):
        """计算异常检测阈值"""
        split_idx = int(len(X) * (1 - validation_split))
        val_X = X[split_idx:]
        val_y = y[split_idx:]
        
        predictions = self.model.predict(val_X, verbose=0)
        mses = np.mean((predictions - val_y) ** 2, axis=1)
        
        # 使用高斯分布的置信区间（例如95%）
        mean_mse = np.mean(mses)
        std_mse = np.std(mses)
        self.mse_threshold = mean_mse + 2 * std_mse  # 2-sigma
        
    def predict(self, history: List[List[float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        预测下一个参数值向量
        
        Args:
            history: 历史参数值序列（长度应为window_size）
            
        Returns:
            (预测的参数值向量, 特征均值数组, 特征标准差数组)
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        if self.feature_means is None or self.feature_stds is None:
            raise ValueError("归一化参数未初始化")
        
        if len(history) != self.window_size:
            raise ValueError(f"历史序列长度应为{self.window_size}，实际为{len(history)}")
        
        # 归一化历史序列（按特征维度）
        norm_history = []
        for h in history:
            if len(h) != self.feature_dim:
                # 如果长度不匹配，填充或截断
                if len(h) < self.feature_dim:
                    h = list(h) + [0.0] * (self.feature_dim - len(h))
                else:
                    h = h[:self.feature_dim]
            
            h_array = np.array(h)
            
            # 裁剪异常值
            feature_mins = self.feature_means - 3 * self.feature_stds
            feature_maxs = self.feature_means + 3 * self.feature_stds
            h_array = np.clip(h_array, feature_mins, feature_maxs)
            
            # 归一化
            norm_h = (h_array - self.feature_means) / self.feature_stds
            norm_h = np.clip(norm_h, -5.0, 5.0)
            norm_history.append(norm_h.tolist())
        
        input_seq = np.array(norm_history).reshape(1, self.window_size, self.feature_dim)
        
        # 预测
        prediction = self.model.predict(input_seq, verbose=0)[0]
        
        # 反归一化（按特征维度）
        denorm_prediction = prediction * self.feature_stds + self.feature_means
        
        return denorm_prediction, self.feature_means, self.feature_stds
    
    def is_anomaly(self, history: List[List[float]], actual: List[float]) -> Tuple[bool, float]:
        """
        检测参数值是否异常
        
        Args:
            history: 历史参数值序列
            actual: 实际参数值向量
            
        Returns:
            (是否异常, MSE值)
        """
        prediction, feature_means, feature_stds = self.predict(history)
        
        # 确保actual长度匹配
        if len(actual) != self.feature_dim:
            if len(actual) < self.feature_dim:
                actual = list(actual) + [0.0] * (self.feature_dim - len(actual))
            else:
                actual = actual[:self.feature_dim]
        
        actual_array = np.array(actual)
        
        # 裁剪异常值
        feature_mins = feature_means - 3 * feature_stds
        feature_maxs = feature_means + 3 * feature_stds
        actual_array = np.clip(actual_array, feature_mins, feature_maxs)
        
        # 在归一化空间中计算MSE（归一化实际值）
        norm_actual = (actual_array - feature_means) / feature_stds
        norm_prediction = (prediction - feature_means) / feature_stds
        
        # 计算MSE（在归一化空间中）
        mse = np.mean((norm_prediction - norm_actual) ** 2)
        
        is_anomaly = mse > self.mse_threshold if self.mse_threshold else False
        
        return is_anomaly, float(mse)
    
    def save(self, filepath: str):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        model_dir = os.path.dirname(filepath)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        
        self.model.save_weights(filepath + '.weights.h5')
        
        config = {
            'feature_dim': self.feature_dim,
            'window_size': self.window_size,
            'lstm_layers': self.lstm_layers,
            'lstm_units': self.lstm_units,
            'mean': self.mean,
            'std': self.std,
            'mse_threshold': self.mse_threshold
        }
        with open(filepath + '.config.pkl', 'wb') as f:
            pickle.dump(config, f)
    
    def load(self, filepath: str):
        """加载模型"""
        with open(filepath + '.config.pkl', 'rb') as f:
            config = pickle.load(f)
        
        self.feature_dim = config['feature_dim']
        self.window_size = config['window_size']
        self.lstm_layers = config['lstm_layers']
        self.lstm_units = config['lstm_units']
        self.mean = config['mean']
        self.std = config['std']
        self.mse_threshold = config['mse_threshold']
        
        self.build_model()
        self.model.load_weights(filepath + '.weights.h5')

