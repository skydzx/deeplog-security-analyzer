"""
工具函数模块 (优化版本)
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Any, Iterator
from collections import defaultdict
import gc
from functools import lru_cache


def extract_log_key(log_message: str) -> str:
    """
    从日志消息中提取日志键（将参数替换为*）

    Args:
        log_message: 原始日志消息

    Returns:
        日志键（参数被替换为*）
    """
    # 简单的参数替换：将数字、IP地址、路径等替换为*
    # 这是一个简化版本，实际应用中可以使用更复杂的解析器如Spell

    # 先提取并保留日志级别（INFO, ERROR, WARN, DEBUG等）
    log_level = ""
    level_match = re.search(r'\b(INFO|ERROR|WARN|WARNING|DEBUG|CRITICAL|FATAL)\b', log_message, re.IGNORECASE)
    if level_match:
        log_level = level_match.group(1).upper()
        # 临时替换日志级别，避免被数字替换影响
        log_message = log_message.replace(level_match.group(1), f"__LEVEL_{log_level}__", 1)

    # 替换时间戳（保留格式但替换数字）
    log_key = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '* *:*:*', log_message)
    # 替换数字
    log_key = re.sub(r'\d+', '*', log_key)
    # 替换IP地址
    log_key = re.sub(r'\*\.\*\.\*\.\*', '*', log_key)  # 处理已经被替换的IP
    log_key = re.sub(r'\d+\.\d+\.\d+\.\d+', '*', log_key)
    # 替换UUID
    log_key = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '*', log_key, flags=re.IGNORECASE)
    # 替换文件路径中的文件名
    log_key = re.sub(r'/[^\s]+', '/*', log_key)
    # 替换参数格式如 user_id=*, request_id=* 等
    log_key = re.sub(r'\w+_id=\*', '*_id=*', log_key)
    log_key = re.sub(r'\w+=\*', '*=*', log_key)

    # 处理Windows事件日志的长消息（截断过长的描述）
    # 如果日志键太长（>200字符），尝试提取关键部分
    if len(log_key) > 200:
        # 尝试提取事件ID和关键信息
        event_id_match = re.search(r'EventID[=:](\S+)', log_key)
        if event_id_match:
            event_id = event_id_match.group(1)
            # 提取消息的前50个字符
            msg_start = log_key.find(log_level) if log_level else 0
            if msg_start > 0:
                msg_part = log_key[msg_start:msg_start+50]
                log_key = f"{log_key[:msg_start]} {log_level} EventID={event_id} {msg_part}..."
        else:
            # 直接截断
            log_key = log_key[:200] + "..."

    # 恢复日志级别
    if log_level:
        log_key = log_key.replace(f"__LEVEL_{log_level}__", log_level)

    return log_key.strip()


def extract_parameters(log_message: str, log_key: str) -> List[float]:
    """
    从日志消息中提取参数值

    Args:
        log_message: 原始日志消息
        log_key: 对应的日志键

    Returns:
        参数值列表（数值参数等，不包括时间差，时间差由LogParser单独处理）
    """
    parameters = []
    seen = set()  # 用于去重

    # 提取时间戳（用于排除）
    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', log_message)
    timestamp_str = timestamp_match.group(0) if timestamp_match else ""

    # 1. 提取参数格式的值，如 user_id=12345
    param_id_matches = re.findall(r'\w+_id=(\d+)', log_message)
    for p in param_id_matches:
        val = float(int(p))
        if val not in seen:
            parameters.append(val)
            seen.add(val)

    # 2. 提取时间相关参数，如 "in 0.5 seconds" 或 "took 10.2 seconds"
    time_matches = re.findall(r'(?:in|took|takes?)\s+(\d+\.?\d*)\s*(?:seconds?|ms|milliseconds?)', log_message, re.IGNORECASE)
    for t in time_matches:
        val = float(t)
        if val not in seen:
            parameters.append(val)
            seen.add(val)

    # 3. 提取其他数值参数（排除时间戳中的数字）
    # 先找到所有数字
    all_numbers = re.findall(r'\b(\d+\.?\d*)\b', log_message)
    for num_str in all_numbers:
        # 跳过时间戳中的数字
        if timestamp_str and num_str in timestamp_str:
            continue

        try:
            val = float(num_str)
            # 跳过已经在前面提取的参数
            if val not in seen:
                # 只保留合理的参数值（排除过大的ID和时间戳）
                # 更严格的限制，避免提取过大的值影响归一化
                if 0 < val < 100000:  # 合理的参数值范围（降低上限）
                    parameters.append(val)
                    seen.add(val)
        except:
            pass

    return parameters


def normalize_parameters(parameters: List[float],
                        mean: float = None,
                        std: float = None) -> Tuple[List[float], float, float]:
    """
    归一化参数值

    Args:
        parameters: 参数值列表
        mean: 均值（如果为None则计算）
        std: 标准差（如果为None则计算）

    Returns:
        (归一化后的参数, 均值, 标准差)
    """
    if not parameters:
        return [], 0.0, 1.0

    params_array = np.array(parameters)

    if mean is None:
        mean = np.mean(params_array)
    if std is None:
        std = np.std(params_array)
        if std == 0:
            std = 1.0

    normalized = (params_array - mean) / std
    return normalized.tolist(), mean, std


def create_sequences(data: List[Any], window_size: int, batch_size: int = None) -> Tuple[List[List[Any]], List[Any]]:
    """
    创建滑动窗口序列用于训练 (优化版本)

    Args:
        data: 输入数据序列
        window_size: 窗口大小
        batch_size: 批处理大小（如果提供，将使用批处理优化）

    Returns:
        (输入序列列表, 对应的标签列表)
    """
    if len(data) < window_size + 1:
        return [], []

    total_sequences = len(data) - window_size

    if batch_size and batch_size < total_sequences:
        # 批处理模式：分批创建序列以节省内存
        sequences = []
        labels = []

        for start_idx in range(0, total_sequences, batch_size):
            end_idx = min(start_idx + batch_size, total_sequences)

            batch_sequences = []
            batch_labels = []

            for i in range(start_idx, end_idx):
                batch_sequences.append(data[i:i + window_size])
                batch_labels.append(data[i + window_size])

            sequences.extend(batch_sequences)
            labels.extend(batch_labels)

            # 强制垃圾回收以释放内存
            if len(sequences) % (batch_size * 10) == 0:
                gc.collect()

        return sequences, labels
    else:
        # 标准模式：使用列表推导式优化
        sequences = [data[i:i + window_size] for i in range(total_sequences)]
        labels = [data[i + window_size] for i in range(total_sequences)]

        return sequences, labels


def create_sequences_numpy(data: List[Any], window_size: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    使用NumPy优化的序列创建 (高性能版本)

    Args:
        data: 输入数据序列
        window_size: 窗口大小

    Returns:
        (输入序列数组, 标签数组)
    """
    if len(data) < window_size + 1:
        return np.array([]), np.array([])

    data_array = np.array(data)
    total_sequences = len(data) - window_size

    # 使用stride tricks创建滑动窗口视图
    shape = (total_sequences, window_size)
    strides = (data_array.itemsize,) * 2
    sequences = np.lib.stride_tricks.as_strided(data_array, shape=shape, strides=strides)

    # 创建标签
    labels = data_array[window_size:]

    return sequences, labels


def build_vocabulary(log_keys: List[str]) -> Dict[str, int]:
    """
    构建日志键词汇表 (优化版本)

    Args:
        log_keys: 日志键列表

    Returns:
        日志键到索引的映射字典
    """
    unique_keys = sorted(set(log_keys))  # 排序确保一致性
    vocab = {key: idx for idx, key in enumerate(unique_keys)}
    return vocab


@lru_cache(maxsize=1024)
def build_vocabulary_cached(log_keys_tuple: Tuple[str, ...]) -> Dict[str, int]:
    """
    缓存版本的词汇表构建 (用于频繁调用)

    Args:
        log_keys_tuple: 日志键元组

    Returns:
        日志键到索引的映射字典
    """
    unique_keys = sorted(set(log_keys_tuple))
    vocab = {key: idx for idx, key in enumerate(unique_keys)}
    return vocab


def one_hot_encode(key: str, vocab: Dict[str, int]) -> np.ndarray:
    """
    将日志键编码为one-hot向量

    Args:
        key: 日志键
        vocab: 词汇表

    Returns:
        one-hot编码向量
    """
    vocab_size = len(vocab)
    if key not in vocab:
        # 未知键，返回全零向量
        return np.zeros(vocab_size)

    one_hot = np.zeros(vocab_size)
    one_hot[vocab[key]] = 1.0
    return one_hot


def one_hot_encode_batch(keys: List[str], vocab: Dict[str, int]) -> np.ndarray:
    """
    批量one-hot编码 (优化版本)

    Args:
        keys: 日志键列表
        vocab: 词汇表

    Returns:
        one-hot编码矩阵
    """
    vocab_size = len(vocab)
    batch_size = len(keys)

    # 预分配矩阵
    one_hot_matrix = np.zeros((batch_size, vocab_size))

    for i, key in enumerate(keys):
        if key in vocab:
            one_hot_matrix[i, vocab[key]] = 1.0
        # 未知键保持全零

    return one_hot_matrix


def calculate_mse(predicted: np.ndarray, actual: np.ndarray) -> float:
    """
    计算均方误差

    Args:
        predicted: 预测值
        actual: 实际值

    Returns:
        均方误差
    """
    return np.mean((predicted - actual) ** 2)


def calculate_mse_batch(predicted: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """
    批量计算均方误差 (优化版本)

    Args:
        predicted: 预测值数组
        actual: 实际值数组

    Returns:
        每个样本的均方误差数组
    """
    return np.mean((predicted - actual) ** 2, axis=1)


def batch_generator(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """
    批数据生成器 (内存优化)

    Args:
        data: 输入数据
        batch_size: 批大小

    Yields:
        数据批
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def memory_efficient_processing(data: List[Any], process_func, batch_size: int = 1000):
    """
    内存高效的批处理函数

    Args:
        data: 输入数据
        process_func: 处理函数
        batch_size: 批大小

    Returns:
        处理结果
    """
    results = []

    for batch in batch_generator(data, batch_size):
        batch_results = process_func(batch)
        results.extend(batch_results)

        # 定期垃圾回收
        if len(results) % (batch_size * 10) == 0:
            gc.collect()

    return results


def optimize_memory_usage():
    """
    内存优化函数
    调用垃圾回收并清理不必要的对象
    """
    gc.collect()
    # 清理LRU缓存中的过期条目
    build_vocabulary_cached.cache_clear()