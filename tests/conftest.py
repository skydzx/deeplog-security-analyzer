"""
pytest配置文件
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock


@pytest.fixture
def sample_logs():
    """生成示例日志数据"""
    return [
        "2024-01-01 10:00:00 INFO Starting application",
        "2024-01-01 10:00:01 INFO Connected to database",
        "2024-01-01 10:00:02 INFO User login user_id=12345",
        "2024-01-01 10:00:03 INFO Processing request request_id=req001",
        "2024-01-01 10:00:04 INFO Request completed in 0.5 seconds",
    ]


@pytest.fixture
def anomaly_logs():
    """生成异常日志数据"""
    return [
        "2024-01-01 10:00:05 ERROR Database connection failed",
        "2024-01-01 10:00:06 CRITICAL System crash detected",
        "2024-01-01 10:00:07 FATAL Application crashed",
    ]


@pytest.fixture
def mock_tensorflow():
    """模拟TensorFlow模型"""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.1, 0.3, 0.6]])
    mock_model.fit.return_value = MagicMock()
    mock_model.save.return_value = None
    mock_model.load.return_value = None
    return mock_model


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录fixture"""
    return tmp_path


@pytest.fixture(scope="session")
def deeplog_config():
    """DeepLog配置"""
    return {
        "window_size": 3,
        "top_g": 2,
        "lstm_layers": 1,
        "lstm_units": 16,
        "epochs": 2,
        "batch_size": 4
    }