"""
日志解析器模块
负责将非结构化日志解析为结构化表示
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from .utils import extract_log_key, extract_parameters


class LogEntry:
    """日志条目类"""
    
    def __init__(self, raw_message: str, timestamp: Optional[datetime] = None):
        self.raw_message = raw_message
        self.timestamp = timestamp
        self.log_key = extract_log_key(raw_message)
        self.parameters = extract_parameters(raw_message, self.log_key)
        self.time_delta = 0.0  # 与前一个日志条目的时间差
        
    def __repr__(self):
        return f"LogEntry(key={self.log_key}, params={self.parameters})"


class LogParser:
    """
    日志解析器
    将原始日志解析为结构化的日志条目
    """
    
    def __init__(self):
        self.last_timestamp = None
        
    def parse(self, log_line: str, timestamp: Optional[datetime] = None) -> LogEntry:
        """
        解析单条日志
        
        Args:
            log_line: 原始日志行
            timestamp: 时间戳（可选，如果为None则尝试从日志中解析）
            
        Returns:
            LogEntry对象
        """
        # 如果没有提供时间戳，尝试从日志字符串中解析
        if timestamp is None:
            timestamp = self._parse_timestamp_from_log(log_line)
        
        entry = LogEntry(log_line, timestamp)
        
        # 计算时间差
        if timestamp and self.last_timestamp:
            delta = (timestamp - self.last_timestamp).total_seconds()
            entry.time_delta = delta
            # 将时间差添加到参数向量中
            if entry.parameters:
                entry.parameters.insert(0, delta)
            else:
                entry.parameters = [delta]
        
        if timestamp:
            self.last_timestamp = timestamp
            
        return entry
    
    def _parse_timestamp_from_log(self, log_line: str) -> Optional[datetime]:
        """
        从日志字符串中解析时间戳
        
        Args:
            log_line: 日志行
            
        Returns:
            datetime对象或None
        """
        import re
        from datetime import datetime
        
        # 尝试匹配常见的时间戳格式
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',  # 2024-01-01 10:00:00
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)',  # 2024-01-01 10:00:00.123
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',  # 2024/01/01 10:00:00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    # 尝试解析
                    if '.' in timestamp_str:
                        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        return datetime.strptime(timestamp_str, '%Y/%m/%d %H:%M:%S')
                    except:
                        pass
        
        return None
    
    def parse_batch(self, log_lines: List[str], 
                   timestamps: Optional[List[datetime]] = None) -> List[LogEntry]:
        """
        批量解析日志
        
        Args:
            log_lines: 日志行列表
            timestamps: 时间戳列表（可选）
            
        Returns:
            LogEntry对象列表
        """
        entries = []
        self.last_timestamp = None
        
        for i, line in enumerate(log_lines):
            timestamp = timestamps[i] if timestamps else None
            entry = self.parse(line, timestamp)
            entries.append(entry)
            
        return entries
    
    def parse_with_identifier(self, log_lines: List[str], 
                             identifier_extractor: callable = None) -> Dict[str, List[LogEntry]]:
        """
        根据标识符（如block_id, instance_id）将日志分组
        
        Args:
            log_lines: 日志行列表
            identifier_extractor: 提取标识符的函数
            
        Returns:
            按标识符分组的日志条目字典
        """
        if identifier_extractor is None:
            # 默认标识符提取器（提取常见的ID模式）
            def default_extractor(line: str) -> str:
                # 尝试提取block_id, instance_id等
                patterns = [
                    r'block[_\s]*id[:\s]*([^\s,]+)',
                    r'instance[_\s]*id[:\s]*([^\s,]+)',
                    r'id[:\s]*([a-f0-9-]{36})',  # UUID
                ]
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(1)
                return "default"
            
            identifier_extractor = default_extractor
        
        grouped = {}
        for line in log_lines:
            identifier = identifier_extractor(line)
            if identifier not in grouped:
                grouped[identifier] = []
            entry = self.parse(line)
            grouped[identifier].append(entry)
            
        return grouped

