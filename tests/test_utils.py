"""
测试工具函数
"""

import pytest
import numpy as np
from deeplog.utils import (
    extract_log_key,
    extract_parameters,
    normalize_parameters,
    create_sequences,
    build_vocabulary,
    one_hot_encode,
    calculate_mse
)


class TestExtractLogKey:
    """测试日志键提取功能"""

    def test_extract_simple_log_key(self):
        """测试简单日志键提取"""
        log_message = "2024-01-01 10:00:00 INFO Starting application"
        log_key = extract_log_key(log_message)

        assert "INFO" in log_key
        assert "Starting application" in log_key
        assert "2024" not in log_key  # 时间戳应该被替换

    def test_extract_log_key_with_numbers(self):
        """测试包含数字的日志键提取"""
        log_message = "INFO User login user_id=12345"
        log_key = extract_log_key(log_message)

        assert "INFO" in log_key
        assert "User login" in log_key
        assert "*" in log_key  # 应该包含通配符

    def test_extract_log_key_with_ip(self):
        """测试包含IP地址的日志键提取"""
        log_message = "INFO Connection from 192.168.1.100"
        log_key = extract_log_key(log_message)

        assert "*" in log_key
        assert "192.168.1.100" not in log_key

    def test_extract_log_key_with_uuid(self):
        """测试包含UUID的日志键提取"""
        log_message = "INFO Processing request 550e8400-e29b-41d4-a716-446655440000"
        log_key = extract_log_key(log_message)

        assert "*" in log_key
        assert "550e8400-e29b-41d4-a716-446655440000" not in log_key

    def test_extract_log_key_with_path(self):
        """测试包含文件路径的日志键提取"""
        log_message = "INFO Reading config from /etc/app/config.json"
        log_key = extract_log_key(log_message)

        assert "/*" in log_key
        assert "/etc/app/config.json" not in log_key

    def test_extract_log_key_case_insensitive(self):
        """测试日志级别大小写不敏感"""
        messages = [
            "info Starting application",
            "INFO Starting application",
            "Error Database connection failed",
            "ERROR Database connection failed"
        ]

        for message in messages:
            log_key = extract_log_key(message)
            assert "INFO" in log_key or "ERROR" in log_key

    def test_extract_log_key_long_message(self):
        """测试长日志消息的截断处理"""
        long_message = "INFO " + "A" * 300  # 超长消息
        log_key = extract_log_key(long_message)

        assert len(log_key) < 250  # 应该被截断


class TestExtractParameters:
    """测试参数提取功能"""

    def test_extract_numeric_parameters(self):
        """测试数值参数提取"""
        log_key = "INFO User login user_id=*"
        log_message = "INFO User login user_id=12345"

        params = extract_parameters(log_message, log_key)
        assert len(params) == 1
        assert params[0] == 12345

    def test_extract_float_parameters(self):
        """测试浮点数参数提取"""
        log_key = "INFO Request completed in * seconds"
        log_message = "INFO Request completed in 0.5 seconds"

        params = extract_parameters(log_message, log_key)
        assert len(params) == 1
        assert abs(params[0] - 0.5) < 0.001

    def test_extract_multiple_parameters(self):
        """测试多个参数提取"""
        log_key = "INFO Processing request *_id=* duration=*"
        log_message = "INFO Processing request request_id=req001 duration=2.5"

        params = extract_parameters(log_message, log_key)
        # 目前只提取数值参数，字符串参数需要不同的处理方式
        assert len(params) == 1
        assert abs(params[0] - 2.5) < 0.001  # 数值参数

    def test_extract_string_parameters(self):
        """测试字符串参数提取"""
        log_key = "INFO Connected to database *"
        log_message = "INFO Connected to database mysql"

        params = extract_parameters(log_message, log_key)
        # 当前实现只提取数值参数，字符串参数需要额外处理
        assert len(params) == 0

    def test_extract_no_parameters(self):
        """测试无参数情况"""
        log_key = "INFO Starting application"
        log_message = "INFO Starting application"

        params = extract_parameters(log_message, log_key)
        assert len(params) == 0


class TestNormalizeParameters:
    """测试参数归一化功能"""

    def test_normalize_numeric_list(self):
        """测试数值列表归一化"""
        params = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized, mean, std = normalize_parameters(params)

        assert len(normalized) == len(params)
        # 检查均值和标准差
        assert abs(mean - 3.0) < 0.001  # 均值应该是3.0
        assert abs(std - np.std([1.0, 2.0, 3.0, 4.0, 5.0])) < 0.001

    def test_normalize_single_value(self):
        """测试单个值归一化"""
        params = [5.0]
        normalized, mean, std = normalize_parameters(params)

        assert len(normalized) == 1
        assert normalized[0] == 0.0  # 单个值归一化后为0
        assert abs(mean - 5.0) < 0.001
        assert std == 1.0  # 标准差为1.0避免除零

    def test_normalize_empty_list(self):
        """测试空列表归一化"""
        params = []
        normalized, mean, std = normalize_parameters(params)

        assert len(normalized) == 0
        assert mean == 0.0
        assert std == 1.0

    def test_normalize_constant_values(self):
        """测试常量值归一化"""
        params = [2.0, 2.0, 2.0]
        normalized, mean, std = normalize_parameters(params)

        assert all(x == 0.0 for x in normalized)  # 常量值都归一化为0
        assert abs(mean - 2.0) < 0.001
        assert std == 1.0  # 标准差为1.0避免除零


class TestCreateSequences:
    """测试序列创建功能"""

    def test_create_sequences_normal(self):
        """测试正常序列创建"""
        data = [1, 2, 3, 4, 5, 6, 7]
        window_size = 3

        sequences, labels = create_sequences(data, window_size)

        assert len(sequences) == 4  # 7-3 = 4个序列
        assert len(labels) == 4
        assert sequences[0] == [1, 2, 3]
        assert labels[0] == 4
        assert sequences[1] == [2, 3, 4]
        assert labels[1] == 5
        assert sequences[-1] == [4, 5, 6]
        assert labels[-1] == 7

    def test_create_sequences_short_data(self):
        """测试数据长度小于窗口大小时"""
        data = [1, 2]
        window_size = 3

        sequences, labels = create_sequences(data, window_size)

        assert len(sequences) == 0  # 无法创建序列
        assert len(labels) == 0

    def test_create_sequences_equal_length(self):
        """测试数据长度等于窗口大小时"""
        data = [1, 2, 3]
        window_size = 3

        sequences, labels = create_sequences(data, window_size)

        assert len(sequences) == 0  # 无法创建带标签的序列
        assert len(labels) == 0


class TestBuildVocabulary:
    """测试词汇表构建功能"""

    def test_build_vocabulary_simple(self):
        """测试简单词汇表构建"""
        log_keys = ["INFO A", "INFO B", "ERROR C", "INFO A"]

        vocab = build_vocabulary(log_keys)

        assert isinstance(vocab, dict)
        assert len(vocab) == 3  # 三个唯一键
        assert "INFO A" in vocab
        assert "INFO B" in vocab
        assert "ERROR C" in vocab
        # 按字母顺序排序：ERROR C(0), INFO A(1), INFO B(2)
        assert vocab["ERROR C"] == 0

    def test_build_vocabulary_empty(self):
        """测试空词汇表构建"""
        log_keys = []

        vocab = build_vocabulary(log_keys)

        assert isinstance(vocab, dict)
        assert len(vocab) == 0


class TestOneHotEncode:
    """测试One-hot编码功能"""

    def test_one_hot_encode_simple(self):
        """测试简单One-hot编码"""
        vocab = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}

        encoded = one_hot_encode("B", vocab)
        assert encoded.shape == (5,)
        assert encoded[1] == 1  # B在位置1
        assert encoded[0] == 0  # 其他位置为0

        encoded = one_hot_encode("D", vocab)
        assert encoded[3] == 1  # D在位置3

    def test_one_hot_encode_unknown(self):
        """测试未知词的One-hot编码"""
        vocab = {"A": 0, "B": 1, "C": 2}

        encoded = one_hot_encode("Z", vocab)  # 未知词
        assert encoded.shape == (3,)
        assert all(x == 0 for x in encoded)  # 全零向量


class TestCalculateMse:
    """测试均方误差计算功能"""

    def test_calculate_mse_identical(self):
        """测试完全相同的预测"""
        predicted = np.array([1.0, 2.0, 3.0])
        actual = np.array([1.0, 2.0, 3.0])

        mse = calculate_mse(predicted, actual)
        assert abs(mse - 0.0) < 0.001

    def test_calculate_mse_different(self):
        """测试完全不同的预测"""
        predicted = np.array([1.0, 2.0, 3.0])
        actual = np.array([4.0, 5.0, 6.0])

        mse = calculate_mse(predicted, actual)
        # MSE = ((4-1)^2 + (5-2)^2 + (6-3)^2) / 3 = (9 + 9 + 9) / 3 = 9
        assert abs(mse - 9.0) < 0.001

    def test_calculate_mse_partial_difference(self):
        """测试部分不同的预测"""
        predicted = np.array([1.0, 2.0, 3.0])
        actual = np.array([1.0, 3.0, 3.0])

        mse = calculate_mse(predicted, actual)
        # MSE = ((1-1)^2 + (3-2)^2 + (3-3)^2) / 3 = (0 + 1 + 0) / 3 = 1/3
        assert abs(mse - (1.0/3.0)) < 0.001