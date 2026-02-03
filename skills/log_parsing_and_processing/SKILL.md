# Log Parsing and Processing - 日志解析和处理技能

## 技能概述

专门针对 DeepLog 项目中日志解析、预处理和特征提取的技能。专注于高效处理各种格式的系统日志，提取有意义的特征用于异常检测。

## 适用场景

- **日志格式解析**: 支持多种日志格式（Linux, Windows, Apache等）
- **特征提取**: 日志键提取、参数提取、时间序列处理
- **数据预处理**: 归一化、编码、序列构建
- **性能优化**: 大规模日志处理、内存优化
- **新格式支持**: 扩展支持新的日志类型

## 核心解析架构

### 1. 日志解析器设计

```python
"""
DeepLog 日志解析器架构
支持多种日志格式和高效的特征提取
"""

from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime
import re
import json
from dataclasses import dataclass

@dataclass
class LogEntry:
    """日志条目数据类"""
    original_line: str
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    message: str = ""
    log_key: str = ""
    parameters: Dict[str, Union[str, int, float]] = None
    source: str = ""  # "linux", "windows", "apache", etc.

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class BaseLogParser:
    """基础日志解析器"""

    def __init__(self):
        self.patterns = self._load_patterns()
        self.compiled_patterns = self._compile_patterns()

    def parse(self, log_line: str, timestamp: Optional[datetime] = None) -> LogEntry:
        """解析单条日志"""
        raise NotImplementedError

    def parse_batch(self, log_lines: List[str],
                   timestamps: Optional[List[datetime]] = None) -> List[LogEntry]:
        """批量解析日志"""
        if timestamps and len(timestamps) != len(log_lines):
            raise ValueError("timestamps长度必须与log_lines相同")

        entries = []
        for i, line in enumerate(log_lines):
            ts = timestamps[i] if timestamps else None
            try:
                entry = self.parse(line, ts)
                entries.append(entry)
            except Exception as e:
                # 创建带有错误信息的条目
                error_entry = LogEntry(
                    original_line=line,
                    message=f"解析失败: {e}",
                    source=self.__class__.__name__.replace('Parser', '').lower()
                )
                entries.append(error_entry)

        return entries

    def _load_patterns(self) -> Dict[str, str]:
        """加载解析模式"""
        raise NotImplementedError

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译正则表达式模式"""
        return {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.patterns.items()
        }

class LinuxLogParser(BaseLogParser):
    """Linux系统日志解析器"""

    def _load_patterns(self) -> Dict[str, str]:
        """Linux日志解析模式"""
        return {
            # 时间戳模式
            'timestamp': r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',

            # 完整日志行模式
            'full_line': r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\w+)\s+(?P<process>\w+(?:\[\d+\])?):\s+(?P<message>.*)',

            # 日志级别模式
            'level': r'\b(INFO|WARNING|ERROR|CRITICAL|DEBUG)\b',

            # IP地址模式
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',

            # 文件路径模式
            'file_path': r'/[^\s]+',

            # 数值参数模式
            'number': r'\b\d+\b',

            # 时间值模式（如 "10 seconds", "5.2 ms"）
            'time_value': r'(\d+(?:\.\d+)?)\s*(seconds?|minutes?|hours?|ms|milliseconds?)',
        }

    def parse(self, log_line: str, timestamp: Optional[datetime] = None) -> LogEntry:
        """解析Linux日志"""
        # 匹配完整日志行
        match = self.compiled_patterns['full_line'].match(log_line.strip())

        if match:
            groups = match.groupdict()

            # 解析时间戳
            if not timestamp and groups.get('timestamp'):
                try:
                    # 简化的时间戳解析，实际应该更复杂
                    ts_str = groups['timestamp']
                    # 转换为datetime对象（这里简化了）
                    parsed_ts = self._parse_linux_timestamp(ts_str)
                except:
                    parsed_ts = None
            else:
                parsed_ts = timestamp

            # 提取消息
            message = groups.get('message', '')

            # 提取日志级别
            level_match = self.compiled_patterns['level'].search(message)
            level = level_match.group(1) if level_match else None

            # 提取日志键
            log_key = self._extract_log_key(message)

            # 提取参数
            parameters = self._extract_parameters(message)

            return LogEntry(
                original_line=log_line,
                timestamp=parsed_ts,
                level=level,
                message=message,
                log_key=log_key,
                parameters=parameters,
                source='linux'
            )
        else:
            # 无法解析的日志
            return LogEntry(
                original_line=log_line,
                message=log_line,
                source='linux'
            )

    def _parse_linux_timestamp(self, ts_str: str) -> datetime:
        """解析Linux时间戳"""
        # 简化的实现，实际应该处理时区等
        current_year = datetime.now().year
        try:
            # Jan 15 10:30:45 -> 2024-01-15 10:30:45
            dt = datetime.strptime(f"{current_year} {ts_str}", "%Y %b %d %H:%M:%S")
            return dt
        except:
            return None

    def _extract_log_key(self, message: str) -> str:
        """提取日志键"""
        # 移除参数值，保留模板
        key = message

        # 替换IP地址
        key = self.compiled_patterns['ip_address'].sub('<IP>', key)

        # 替换文件路径
        key = self.compiled_patterns['file_path'].sub('<PATH>', key)

        # 替换数值
        key = self.compiled_patterns['number'].sub('<NUM>', key)

        # 替换时间值
        key = self.compiled_patterns['time_value'].sub('<TIME>', key)

        return key.strip()

    def _extract_parameters(self, message: str) -> Dict[str, Union[str, int, float]]:
        """提取参数"""
        params = {}

        # 提取时间值
        time_matches = self.compiled_patterns['time_value'].findall(message)
        if time_matches:
            for value, unit in time_matches:
                params[f'time_{unit}'] = float(value)

        # 提取IP地址
        ip_matches = self.compiled_patterns['ip_address'].findall(message)
        if ip_matches:
            params['ip_addresses'] = ip_matches

        # 提取文件路径
        path_matches = self.compiled_patterns['file_path'].findall(message)
        if path_matches:
            params['file_paths'] = path_matches

        return params

class WindowsLogParser(BaseLogParser):
    """Windows系统日志解析器"""

    def _load_patterns(self) -> Dict[str, str]:
        """Windows日志解析模式"""
        return {
            # Windows事件日志时间戳
            'timestamp': r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',

            # 完整日志行模式（简化版）
            'full_line': r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(?P<level>\w+)\s+(?P<source>[^\s]+)\s+(?P<message>.*)',

            # 事件ID模式
            'event_id': r'EventID[:=]\s*(\d+)',

            # 用户模式
            'user': r'Account Name[:=]\s*([^\s]+)',

            # 进程ID模式
            'pid': r'ProcessID[:=]\s*(\d+)',
        }

    def parse(self, log_line: str, timestamp: Optional[datetime] = None) -> LogEntry:
        """解析Windows日志"""
        match = self.compiled_patterns['full_line'].match(log_line.strip())

        if match:
            groups = match.groupdict()

            # 解析时间戳
            if not timestamp and groups.get('timestamp'):
                try:
                    parsed_ts = datetime.fromisoformat(groups['timestamp'].replace('T', ' '))
                except:
                    parsed_ts = None
            else:
                parsed_ts = timestamp

            message = groups.get('message', '')
            level = groups.get('level')

            # 提取日志键
            log_key = self._extract_log_key(message)

            # 提取参数
            parameters = self._extract_parameters(message)

            return LogEntry(
                original_line=log_line,
                timestamp=parsed_ts,
                level=level,
                message=message,
                log_key=log_key,
                parameters=parameters,
                source='windows'
            )
        else:
            return LogEntry(
                original_line=log_line,
                message=log_line,
                source='windows'
            )

class ApacheLogParser(BaseLogParser):
    """Apache访问日志解析器"""

    def _load_patterns(self) -> Dict[str, str]:
        return {
            # Apache通用日志格式
            'common': r'(?P<ip>\S+)\s+(?P<identity>\S+)\s+(?P<user>\S+)\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<size>\S+)',

            # 请求行解析
            'request': r'(?P<method>\w+)\s+(?P<path>[^\s?]+)(?:\?(?P<query>[^"]*))?\s+HTTP/(?P<http_version>[\d.]+)',

            # 用户代理
            'user_agent': r'"(?P<user_agent>[^"]*)"',

            # 引用者
            'referer': r'"(?P<referer>[^"]*)"',
        }

    def parse(self, log_line: str, timestamp: Optional[datetime] = None) -> LogEntry:
        """解析Apache日志"""
        match = self.compiled_patterns['common'].match(log_line.strip())

        if match:
            groups = match.groupdict()

            # 解析时间戳
            if not timestamp and groups.get('timestamp'):
                try:
                    # Apache格式: 01/Jan/2024:10:30:45 +0800
                    ts_str = groups['timestamp']
                    parsed_ts = datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S %z")
                except:
                    parsed_ts = None
            else:
                parsed_ts = timestamp

            # 解析请求
            request = groups.get('request', '')
            request_parts = self._parse_request(request)

            # 提取参数
            parameters = {
                'ip': groups.get('ip'),
                'status_code': int(groups.get('status', 0)),
                'response_size': groups.get('size'),
                **request_parts
            }

            return LogEntry(
                original_line=log_line,
                timestamp=parsed_ts,
                level='INFO',  # Apache日志通常是INFO级别
                message=request,
                log_key=f"{request_parts.get('method', 'UNKNOWN')} {request_parts.get('path', 'UNKNOWN')}",
                parameters=parameters,
                source='apache'
            )
        else:
            return LogEntry(
                original_line=log_line,
                message=log_line,
                source='apache'
            )

    def _parse_request(self, request: str) -> Dict[str, str]:
        """解析HTTP请求"""
        match = self.compiled_patterns['request'].match(request)
        if match:
            return match.groupdict()
        return {}
```

### 2. 特征提取器

```python
class FeatureExtractor:
    """特征提取器"""

    def __init__(self):
        self.extractors = {
            'log_key': self._extract_log_key,
            'temporal': self._extract_temporal_features,
            'structural': self._extract_structural_features,
            'semantic': self._extract_semantic_features,
        }

    def extract(self, log_entry: LogEntry) -> Dict[str, Union[str, int, float, List]]:
        """提取所有特征"""
        features = {}

        for feature_type, extractor in self.extractors.items():
            try:
                features.update(extractor(log_entry))
            except Exception as e:
                # 记录错误但不中断处理
                features[f'{feature_type}_error'] = str(e)

        return features

    def _extract_log_key(self, entry: LogEntry) -> Dict[str, str]:
        """提取日志键特征"""
        return {
            'log_key': entry.log_key,
            'log_key_length': len(entry.log_key),
            'log_key_words': len(entry.log_key.split()),
            'has_numbers': bool(re.search(r'\d', entry.log_key)),
            'has_paths': '<PATH>' in entry.log_key,
            'has_ips': '<IP>' in entry.log_key,
        }

    def _extract_temporal_features(self, entry: LogEntry) -> Dict[str, Union[int, float]]:
        """提取时间特征"""
        features = {}

        if entry.timestamp:
            features.update({
                'hour': entry.timestamp.hour,
                'day_of_week': entry.timestamp.weekday(),
                'month': entry.timestamp.month,
                'is_weekend': entry.timestamp.weekday() >= 5,
                'is_business_hours': 9 <= entry.timestamp.hour <= 17,
            })

        return features

    def _extract_structural_features(self, entry: LogEntry) -> Dict[str, Union[int, List]]:
        """提取结构特征"""
        message = entry.message

        return {
            'message_length': len(message),
            'word_count': len(message.split()),
            'sentence_count': len(re.split(r'[.!?]+', message)),
            'has_quotes': '"' in message,
            'has_brackets': ('[' in message and ']' in message),
            'capital_ratio': sum(1 for c in message if c.isupper()) / len(message) if message else 0,
            'punctuation_ratio': sum(1 for c in message if c in '.,!?;:') / len(message) if message else 0,
        }

    def _extract_semantic_features(self, entry: LogEntry) -> Dict[str, Union[int, float]]:
        """提取语义特征"""
        message = entry.message.lower()

        # 错误关键词
        error_keywords = ['error', 'fail', 'exception', 'critical', 'warning']
        error_score = sum(1 for keyword in error_keywords if keyword in message)

        # 成功关键词
        success_keywords = ['success', 'complete', 'done', 'ok', 'finish']
        success_score = sum(1 for keyword in success_keywords if keyword in message)

        # 数值密度
        number_count = len(re.findall(r'\d+', message))
        number_density = number_count / len(message.split()) if message.split() else 0

        return {
            'error_score': error_score,
            'success_score': success_score,
            'number_density': number_density,
            'has_error_keywords': error_score > 0,
            'has_success_keywords': success_score > 0,
        }
```

### 3. 数据预处理器

```python
class DataPreprocessor:
    """数据预处理器"""

    def __init__(self):
        self.encoders = {}
        self.scalers = {}
        self.vocabularies = {}

    def fit(self, log_entries: List[LogEntry]):
        """拟合预处理器"""
        # 构建词汇表
        self._build_vocabularies(log_entries)

        # 拟合编码器
        self._fit_encoders(log_entries)

        # 拟合缩放器
        self._fit_scalers(log_entries)

    def transform(self, log_entries: List[LogEntry]) -> np.ndarray:
        """转换数据"""
        features_list = []

        for entry in log_entries:
            # 提取基础特征
            features = self._extract_base_features(entry)

            # 编码分类特征
            encoded_features = self._encode_categorical_features(features)

            # 缩放数值特征
            scaled_features = self._scale_numerical_features(encoded_features)

            features_list.append(scaled_features)

        return np.array(features_list)

    def fit_transform(self, log_entries: List[LogEntry]) -> np.ndarray:
        """拟合并转换"""
        self.fit(log_entries)
        return self.transform(log_entries)

    def _build_vocabularies(self, entries: List[LogEntry]):
        """构建词汇表"""
        from collections import Counter

        # 日志键词汇表
        log_keys = [entry.log_key for entry in entries]
        self.vocabularies['log_key'] = {
            key: idx for idx, (key, _) in enumerate(
                Counter(log_keys).most_common()
            )
        }

        # 级别词汇表
        levels = [entry.level for entry in entries if entry.level]
        self.vocabularies['level'] = {
            level: idx for idx, (level, _) in enumerate(
                Counter(levels).most_common()
            )
        }

    def _fit_encoders(self, entries: List[LogEntry]):
        """拟合编码器"""
        # 这里可以添加更复杂的编码器，如目标编码等
        pass

    def _fit_scalers(self, entries: List[LogEntry]):
        """拟合缩放器"""
        from sklearn.preprocessing import StandardScaler, MinMaxScaler

        # 数值特征缩放器
        numerical_features = []
        for entry in entries:
            if entry.timestamp:
                # 时间特征
                numerical_features.append([
                    entry.timestamp.hour,
                    entry.timestamp.weekday(),
                    len(entry.message),
                    len(entry.parameters)
                ])

        if numerical_features:
            self.scalers['numerical'] = StandardScaler()
            self.scalers['numerical'].fit(numerical_features)

    def _extract_base_features(self, entry: LogEntry) -> Dict:
        """提取基础特征"""
        features = {
            'log_key': entry.log_key,
            'level': entry.level or 'UNKNOWN',
            'message_length': len(entry.message),
            'param_count': len(entry.parameters),
        }

        if entry.timestamp:
            features.update({
                'hour': entry.timestamp.hour,
                'day_of_week': entry.timestamp.weekday(),
                'month': entry.timestamp.month,
            })

        return features

    def _encode_categorical_features(self, features: Dict) -> Dict:
        """编码分类特征"""
        encoded = features.copy()

        # 编码日志键
        if 'log_key' in features:
            log_key = features['log_key']
            encoded['log_key_encoded'] = self.vocabularies['log_key'].get(log_key, -1)

        # 编码级别
        if 'level' in features:
            level = features['level']
            encoded['level_encoded'] = self.vocabularies['level'].get(level, -1)

        return encoded

    def _scale_numerical_features(self, features: Dict) -> np.ndarray:
        """缩放数值特征"""
        numerical_keys = ['hour', 'day_of_week', 'month', 'message_length', 'param_count']

        numerical_values = []
        for key in numerical_keys:
            if key in features:
                numerical_values.append(features[key])
            else:
                numerical_values.append(0)  # 默认值

        # 应用缩放
        if 'numerical' in self.scalers:
            scaled = self.scalers['numerical'].transform([numerical_values])
            return scaled[0]
        else:
            return np.array(numerical_values)
```

## 性能优化策略

### 1. 批量处理优化

```python
class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.parsers = {
            'linux': LinuxLogParser(),
            'windows': WindowsLogParser(),
            'apache': ApacheLogParser(),
        }

    def process_large_file(self, file_path: str, parser_type: str = 'auto') -> List[LogEntry]:
        """处理大文件"""
        entries = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            batch_lines = []

            for line in f:
                batch_lines.append(line.strip())

                # 达到批次大小时处理
                if len(batch_lines) >= self.batch_size:
                    batch_entries = self._process_batch(batch_lines, parser_type)
                    entries.extend(batch_entries)
                    batch_lines = []

            # 处理剩余行
            if batch_lines:
                batch_entries = self._process_batch(batch_lines, parser_type)
                entries.extend(batch_entries)

        return entries

    def _process_batch(self, lines: List[str], parser_type: str) -> List[LogEntry]:
        """处理一批日志"""
        # 自动检测解析器类型
        if parser_type == 'auto':
            parser_type = self._detect_parser_type(lines[:10])  # 检测前10行

        parser = self.parsers.get(parser_type)
        if not parser:
            raise ValueError(f"不支持的解析器类型: {parser_type}")

        return parser.parse_batch(lines)

    def _detect_parser_type(self, sample_lines: List[str]) -> str:
        """自动检测日志类型"""
        scores = {}

        for parser_name, parser in self.parsers.items():
            score = 0
            for line in sample_lines:
                try:
                    entry = parser.parse(line)
                    if entry.log_key:  # 成功解析
                        score += 1
                except:
                    pass
            scores[parser_name] = score

        # 返回得分最高的解析器
        return max(scores, key=scores.get)
```

### 2. 内存优化

```python
class MemoryOptimizedProcessor:
    """内存优化处理器"""

    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self._monitor_memory()

    def process_with_memory_limit(self, file_path: str) -> List[LogEntry]:
        """内存受限处理"""
        import psutil
        import gc

        entries = []
        batch_size = self._calculate_optimal_batch_size()

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                batch_lines = []
                for _ in range(batch_size):
                    line = f.readline()
                    if not line:
                        break
                    batch_lines.append(line.strip())

                if not batch_lines:
                    break

                # 处理批次
                batch_entries = self._process_batch_memory_efficient(batch_lines)
                entries.extend(batch_entries)

                # 检查内存使用
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                if memory_usage > self.max_memory_mb * 0.8:  # 80%阈值
                    gc.collect()  # 强制垃圾回收

                    # 如果仍然超限，减小批次大小
                    if memory_usage > self.max_memory_mb * 0.9:
                        batch_size = max(1, batch_size // 2)

        return entries

    def _calculate_optimal_batch_size(self) -> int:
        """计算最优批次大小"""
        available_memory = psutil.virtual_memory().available / 1024 / 1024
        avg_entry_size_kb = 2  # 估算每个条目的内存使用

        # 留出50%的内存用于其他操作
        usable_memory = available_memory * 0.5
        optimal_batch = int(usable_memory * 1024 / avg_entry_size_kb)  # KB to entries

        return min(optimal_batch, 10000)  # 最大限制

    def _process_batch_memory_efficient(self, lines: List[str]) -> List[LogEntry]:
        """内存高效的批次处理"""
        # 使用生成器而不是列表
        return list(self._parse_generator(lines))

    def _parse_generator(self, lines: List[str]):
        """解析生成器"""
        parser = LinuxLogParser()  # 或自动检测

        for line in lines:
            try:
                entry = parser.parse(line)
                yield entry
            except Exception as e:
                # 生成错误条目
                yield LogEntry(
                    original_line=line,
                    message=f"解析错误: {e}"
                )

    def _monitor_memory(self):
        """监控内存使用"""
        import threading
        import time

        def monitor():
            while True:
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                if memory_usage > self.max_memory_mb:
                    print(f"警告: 内存使用超过限制 ({memory_usage:.1f}MB / {self.max_memory_mb}MB)")
                time.sleep(10)  # 每10秒检查一次

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
```

## 测试和验证

### 1. 解析器测试

```python
class TestLogParsers:
    """日志解析器测试"""

    def test_linux_parser(self):
        """测试Linux解析器"""
        parser = LinuxLogParser()

        # 测试正常日志
        log_line = "Jan 15 10:30:45 localhost kernel: [12345.678] INFO: Process started"
        entry = parser.parse(log_line)

        assert entry.source == 'linux'
        assert entry.level == 'INFO'
        assert 'Process started' in entry.message
        assert entry.timestamp is not None

    def test_windows_parser(self):
        """测试Windows解析器"""
        parser = WindowsLogParser()

        log_line = "2024-01-15T10:30:45 ERROR Application Error: Access denied"
        entry = parser.parse(log_line)

        assert entry.source == 'windows'
        assert entry.level == 'ERROR'
        assert 'Access denied' in entry.message

    def test_apache_parser(self):
        """测试Apache解析器"""
        parser = ApacheLogParser()

        log_line = '192.168.1.100 - - [15/Jan/2024:10:30:45 +0800] "GET /index.html HTTP/1.1" 200 1024'
        entry = parser.parse(log_line)

        assert entry.source == 'apache'
        assert entry.parameters['status_code'] == 200
        assert entry.parameters['method'] == 'GET'
        assert entry.parameters['path'] == '/index.html'

    def test_batch_processing(self):
        """测试批量处理"""
        parser = LinuxLogParser()
        log_lines = [
            "Jan 15 10:30:45 host1 kernel: INFO message 1",
            "Jan 15 10:30:46 host1 kernel: ERROR message 2",
            "Jan 15 10:30:47 host1 kernel: DEBUG message 3",
        ]

        entries = parser.parse_batch(log_lines)

        assert len(entries) == 3
        assert all(entry.source == 'linux' for entry in entries)
        assert entries[1].level == 'ERROR'

    def test_error_handling(self):
        """测试错误处理"""
        parser = LinuxLogParser()

        # 无效日志行
        invalid_line = ""
        entry = parser.parse(invalid_line)

        assert entry.original_line == invalid_line
        assert entry.message == invalid_line  # 或包含错误信息
```

### 2. 性能测试

```python
class TestPerformance:
    """性能测试"""

    def test_parsing_speed(self):
        """测试解析速度"""
        import time

        parser = LinuxLogParser()
        # 生成测试数据
        test_lines = [
            f"Jan 15 10:30:{i:02d} localhost kernel: INFO Test message {i}"
            for i in range(1000)
        ]

        start_time = time.time()
        entries = parser.parse_batch(test_lines)
        end_time = time.time()

        parsing_time = end_time - start_time
        speed = len(entries) / parsing_time  # 条/秒

        print(f"解析速度: {speed:.1f} 条/秒")
        assert speed > 1000  # 至少1000条/秒

    def test_memory_usage(self):
        """测试内存使用"""
        import psutil

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        parser = LinuxLogParser()
        large_dataset = [f"Jan 15 10:30:{i:02d} localhost kernel: INFO Message {i}" * 10
                        for i in range(10000)]  # 10万条日志

        entries = parser.parse_batch(large_dataset)

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"内存增加: {memory_increase:.1f}MB")
        assert memory_increase < 500  # 内存增加不超过500MB

    def test_scalability(self):
        """测试可扩展性"""
        parser = LinuxLogParser()

        # 测试不同规模的数据集
        sizes = [100, 1000, 10000]
        for size in sizes:
            test_lines = [f"Jan 15 10:30:{i%60:02d} localhost kernel: INFO Message {i}"
                         for i in range(size)]

            start_time = time.time()
            entries = parser.parse_batch(test_lines)
            end_time = time.time()

            avg_time = (end_time - start_time) / size * 1000  # 毫秒/条
            print(f"规模 {size}: {avg_time:.2f}ms/条")

            assert avg_time < 10  # 每条日志解析时间不超过10ms
```

## 最佳实践

### 1. 日志格式扩展

```python
# 添加新的日志格式支持
class CustomLogParser(BaseLogParser):
    """自定义日志解析器"""

    def _load_patterns(self) -> Dict[str, str]:
        return {
            'custom_format': r'your_custom_regex_pattern_here',
            # 添加更多模式...
        }

    def parse(self, log_line: str, timestamp=None) -> LogEntry:
        # 实现自定义解析逻辑
        pass

# 注册新的解析器
parser_registry = {
    'linux': LinuxLogParser,
    'windows': WindowsLogParser,
    'apache': ApacheLogParser,
    'custom': CustomLogParser,
}
```

### 2. 性能监控

```python
class ParserPerformanceMonitor:
    """解析器性能监控"""

    def __init__(self):
        self.stats = defaultdict(list)

    def monitor_parsing(self, parser_name: str, lines_count: int, duration: float):
        """监控解析性能"""
        speed = lines_count / duration  # 条/秒
        self.stats[parser_name].append(speed)

        # 计算统计信息
        speeds = self.stats[parser_name]
        avg_speed = sum(speeds) / len(speeds)
        max_speed = max(speeds)
        min_speed = min(speeds)

        print(f"{parser_name} 解析性能:")
        print(f"  当前速度: {speed:.1f} 条/秒")
        print(f"  平均速度: {avg_speed:.1f} 条/秒")
        print(f"  最快速度: {max_speed:.1f} 条/秒")
        print(f"  最慢速度: {min_speed:.1f} 条/秒")

    def generate_report(self) -> Dict:
        """生成性能报告"""
        report = {}
        for parser_name, speeds in self.stats.items():
            report[parser_name] = {
                'average_speed': sum(speeds) / len(speeds),
                'max_speed': max(speeds),
                'min_speed': min(speeds),
                'total_measurements': len(speeds),
            }
        return report
```

这个技能规范为 DeepLog 项目的日志解析和处理提供了全面的指导，帮助开发人员高效处理各种格式的系统日志。