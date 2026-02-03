"""
测试日志解析器
"""

import pytest
from datetime import datetime
from deeplog.parser import LogParser, LogEntry


class TestLogEntry:
    """测试LogEntry类"""

    def test_log_entry_creation(self):
        """测试LogEntry基本创建"""
        raw_message = "2024-01-01 10:00:00 INFO User login user_id=12345"
        timestamp = datetime(2024, 1, 1, 10, 0, 0)
        entry = LogEntry(raw_message, timestamp)

        assert entry.raw_message == raw_message
        assert entry.timestamp == timestamp
        assert isinstance(entry.log_key, str)
        assert isinstance(entry.parameters, list)
        assert entry.time_delta == 0.0

    def test_log_entry_without_timestamp(self):
        """测试不带时间戳的LogEntry"""
        raw_message = "INFO User login user_id=12345"
        entry = LogEntry(raw_message)

        assert entry.raw_message == raw_message
        assert entry.timestamp is None
        assert isinstance(entry.log_key, str)

    def test_log_entry_repr(self):
        """测试LogEntry的字符串表示"""
        raw_message = "INFO User login user_id=12345"
        entry = LogEntry(raw_message)
        repr_str = repr(entry)

        assert "LogEntry" in repr_str
        assert "key=" in repr_str
        assert "params=" in repr_str


class TestLogParser:
    """测试LogParser类"""

    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = LogParser()
        assert parser.last_timestamp is None

    def test_parse_single_log(self):
        """测试单条日志解析"""
        parser = LogParser()
        log_line = "2024-01-01 10:00:00 INFO Starting application"
        entry = parser.parse(log_line)

        assert isinstance(entry, LogEntry)
        assert entry.raw_message == log_line
        assert entry.timestamp is not None
        assert isinstance(entry.log_key, str)

    def test_parse_log_with_timestamp(self):
        """测试带时间戳的日志解析"""
        parser = LogParser()
        log_line = "INFO Starting application"
        timestamp = datetime(2024, 1, 1, 10, 0, 0)
        entry = parser.parse(log_line, timestamp)

        assert entry.timestamp == timestamp
        assert entry.raw_message == log_line

    def test_parse_batch_logs(self):
        """测试批量日志解析"""
        parser = LogParser()
        log_lines = [
            "2024-01-01 10:00:00 INFO Starting application",
            "2024-01-01 10:00:01 INFO Connected to database",
            "2024-01-01 10:00:02 INFO User login user_id=12345"
        ]
        timestamps = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 1, 10, 0, 1),
            datetime(2024, 1, 1, 10, 0, 2)
        ]

        entries = parser.parse_batch(log_lines, timestamps)

        assert len(entries) == 3
        assert all(isinstance(entry, LogEntry) for entry in entries)
        assert entries[0].timestamp == timestamps[0]
        assert entries[1].timestamp == timestamps[1]
        assert entries[2].timestamp == timestamps[2]

    def test_parse_batch_without_timestamps(self):
        """测试不带时间戳的批量解析"""
        parser = LogParser()
        log_lines = [
            "2024-01-01 10:00:00 INFO Starting application",
            "2024-01-01 10:00:01 INFO Connected to database"
        ]

        entries = parser.parse_batch(log_lines)

        assert len(entries) == 2
        assert all(entry.timestamp is not None for entry in entries)

    def test_parse_with_identifier(self):
        """测试带标识符的解析"""
        parser = LogParser()

        # 测试默认标识符提取器（没有标准标识符时都归为default）
        log_lines = [
            "INFO User login",
            "INFO Processing request"
        ]

        result = parser.parse_with_identifier(log_lines)

        assert isinstance(result, dict)
        assert len(result) == 1  # 只有一个default组
        assert "default" in result
        assert len(result["default"]) == 2

    def test_parse_with_identifier_custom_extractor(self):
        """测试自定义标识符提取器"""
        parser = LogParser()

        def session_extractor(line: str) -> str:
            if "session1:" in line:
                return "session1"
            elif "session2:" in line:
                return "session2"
            else:
                return "default"

        log_lines = [
            "session1: INFO User login",
            "session1: INFO Processing request",
            "session2: INFO User login",
            "session2: INFO Processing request"
        ]

        result = parser.parse_with_identifier(log_lines, session_extractor)

        assert isinstance(result, dict)
        assert len(result) == 2  # 两个session
        assert "session1" in result
        assert "session2" in result
        assert len(result["session1"]) == 2
        assert len(result["session2"]) == 2

    def test_time_delta_calculation(self):
        """测试时间差计算"""
        parser = LogParser()
        log_lines = [
            "2024-01-01 10:00:00 INFO Starting application",
            "2024-01-01 10:00:02 INFO Connected to database",  # 2秒后
            "2024-01-01 10:00:05 INFO User login"  # 再过3秒
        ]

        entries = parser.parse_batch(log_lines)

        assert entries[0].time_delta == 0.0  # 第一个日志时间差为0
        assert abs(entries[1].time_delta - 2.0) < 0.1  # 第二个日志时间差约2秒
        assert abs(entries[2].time_delta - 3.0) < 0.1  # 第三个日志时间差约3秒

    def test_malformed_log_handling(self):
        """测试异常日志处理"""
        parser = LogParser()

        # 空字符串
        entry = parser.parse("")
        assert entry.raw_message == ""
        assert entry.log_key == ""

        # None输入
        entry = parser.parse("INFO Normal message")
        assert entry.raw_message == "INFO Normal message"