# Test Driven Development - 测试驱动开发技能

## 技能概述

专门针对 DeepLog 项目采用测试驱动开发（TDD）方法的技能。强调先写测试、再实现功能，确保代码质量和可维护性。

## 适用场景

- **新功能开发**: 先写测试用例，再实现功能
- **重构优化**: 通过测试确保重构不破坏现有功能
- **Bug修复**: 先写复现Bug的测试，再修复
- **API设计**: 通过测试验证API设计的合理性
- **性能优化**: 通过基准测试确保优化不降低性能

## TDD开发流程

### 1. Red-Green-Refactor 循环

```python
"""
TDD 开发循环：
1. Red: 写一个失败的测试
2. Green: 让测试通过（实现最简单的代码）
3. Refactor: 重构代码，优化设计
"""

# 示例：为新的异常检测算法开发TDD

# 1. Red: 先写测试
def test_anomaly_detector_initialization():
    """测试异常检测器初始化 - 应该失败（还未实现）"""
    detector = AnomalyDetector(threshold=0.5)
    assert detector.threshold == 0.5
    assert detector.model is None  # 初始状态

def test_anomaly_detection_basic():
    """测试基础异常检测 - 应该失败"""
    detector = AnomalyDetector(threshold=0.5)

    # 正常日志
    normal_log = LogEntry(
        message="INFO: Application started successfully",
        level="INFO",
        parameters={}
    )

    # 异常日志
    anomaly_log = LogEntry(
        message="ERROR: Database connection failed",
        level="ERROR",
        parameters={"error_code": 500}
    )

    # 检测结果
    is_anomaly_normal = detector.detect(normal_log)
    is_anomaly_abnormal = detector.detect(anomaly_log)

    assert not is_anomaly_normal  # 正常日志不应该被检测为异常
    assert is_anomaly_abnormal    # 异常日志应该被检测为异常

# 2. Green: 实现最简单的代码让测试通过
class AnomalyDetector:
    """异常检测器 - 初始实现"""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None

    def detect(self, log_entry: LogEntry) -> bool:
        """简单的基于级别的异常检测"""
        # 最简单的实现：ERROR级别认为是异常
        return log_entry.level == "ERROR"

# 3. Refactor: 重构和优化
class AnomalyDetector:
    """异常检测器 - 重构后的实现"""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None
        self._error_keywords = {
            'error', 'fail', 'exception', 'critical',
            'fatal', 'timeout', 'denied', 'refused'
        }

    def detect(self, log_entry: LogEntry) -> bool:
        """基于关键词的异常检测"""
        message_lower = log_entry.message.lower()

        # 检查错误关键词
        has_error_keywords = any(keyword in message_lower
                               for keyword in self._error_keywords)

        # 检查日志级别
        is_error_level = log_entry.level in ['ERROR', 'CRITICAL', 'FATAL']

        # 综合判断
        anomaly_score = (has_error_keywords * 0.7 + is_error_level * 0.3)

        return anomaly_score >= self.threshold
```

### 2. 测试层次结构

```python
"""
DeepLog 测试层次：
1. 单元测试：测试单个函数/类
2. 集成测试：测试模块间的交互
3. 系统测试：测试整个系统
4. 性能测试：测试性能指标
"""

# 单元测试示例
class TestLogParserUnit:
    """日志解析器单元测试"""

    def test_parse_timestamp(self):
        """测试时间戳解析"""
        parser = LogParser()

        # 正常情况
        timestamp_str = "2024-01-15 10:30:45"
        result = parser._parse_timestamp(timestamp_str)
        expected = datetime(2024, 1, 15, 10, 30, 45)
        assert result == expected

    def test_parse_timestamp_edge_cases(self):
        """测试时间戳解析边界情况"""
        parser = LogParser()

        # 空字符串
        assert parser._parse_timestamp("") is None

        # 无效格式
        assert parser._parse_timestamp("invalid") is None

        # 只有日期
        result = parser._parse_timestamp("2024-01-15")
        expected = datetime(2024, 1, 15, 0, 0, 0)
        assert result == expected

# 集成测试示例
class TestDeepLogIntegration:
    """DeepLog集成测试"""

    def test_train_and_detect_integration(self):
        """训练和检测的集成测试"""
        # 创建测试数据
        normal_logs = [
            "INFO: Application started",
            "INFO: Connected to database",
            "INFO: User login successful",
        ] * 10  # 重复以获得足够的训练数据

        anomaly_logs = [
            "ERROR: Database connection failed",
            "ERROR: Authentication failed",
            "CRITICAL: System out of memory",
        ]

        # 初始化DeepLog
        deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=16)

        # 训练
        deeplog.train(normal_logs, epochs=2, batch_size=8)

        # 测试正常日志检测
        for log in normal_logs[:3]:  # 测试前3条
            is_anomaly, _, _ = deeplog.detect(log)
            assert not is_anomaly, f"正常日志被误判为异常: {log}"

        # 测试异常日志检测（这里可能不会全部检测为异常，因为模型很简单）
        anomaly_detected = 0
        for log in anomaly_logs:
            is_anomaly, _, _ = deeplog.detect(log)
            if is_anomaly:
                anomaly_detected += 1

        # 至少应该检测到一些异常
        assert anomaly_detected > 0, "应该至少检测到一个异常"

# 系统测试示例
class TestDeepLogSystem:
    """DeepLog系统测试"""

    @pytest.mark.slow
    def test_full_pipeline(self):
        """完整pipeline测试"""
        # 1. 准备数据
        data_generator = TestDataGenerator()
        train_data, test_data = data_generator.generate_dataset(
            normal_count=1000,
            anomaly_count=100,
            sequence_length=10
        )

        # 2. 训练模型
        deeplog = DeepLog(window_size=5, top_g=3, lstm_layers=2, lstm_units=32)
        deeplog.train(train_data['logs'], epochs=5, batch_size=16)

        # 3. 评估性能
        predictions = []
        for log in test_data['logs']:
            is_anomaly, _, _ = deeplog.detect(log)
            predictions.append(is_anomaly)

        # 4. 计算指标
        accuracy = accuracy_score(test_data['labels'], predictions)
        precision = precision_score(test_data['labels'], predictions)
        recall = recall_score(test_data['labels'], predictions)
        f1 = f1_score(test_data['labels'], predictions)

        # 5. 验证指标
        assert accuracy > 0.8, f"准确率太低: {accuracy}"
        assert f1 > 0.7, f"F1分数太低: {f1}"

        print(f"系统测试结果 - 准确率: {accuracy:.3f}, F1: {f1:.3f}")
```

## 测试策略和最佳实践

### 1. 测试数据管理

```python
class TestDataManager:
    """测试数据管理器"""

    @staticmethod
    def generate_normal_logs(count: int = 100) -> List[str]:
        """生成正常日志"""
        templates = [
            "INFO: User {user_id} logged in from {ip}",
            "INFO: Database query executed in {time}ms",
            "INFO: File {filename} uploaded successfully",
            "INFO: Service {service} started on port {port}",
            "INFO: Cache hit ratio: {ratio}%",
        ]

        logs = []
        for i in range(count):
            template = np.random.choice(templates)
            log = template.format(
                user_id=np.random.randint(1000, 9999),
                ip=f"192.168.1.{np.random.randint(1, 255)}",
                time=np.random.randint(10, 1000),
                filename=f"file_{np.random.randint(1, 100)}.txt",
                service=np.random.choice(['web', 'api', 'db', 'cache']),
                port=np.random.randint(8000, 9000),
                ratio=np.random.randint(80, 100)
            )
            logs.append(log)

        return logs

    @staticmethod
    def generate_anomaly_logs(count: int = 20) -> List[str]:
        """生成异常日志"""
        templates = [
            "ERROR: Connection refused to {host}:{port}",
            "ERROR: Authentication failed for user {user}",
            "CRITICAL: Out of memory, {used}MB used, {free}MB free",
            "ERROR: Database query timeout after {timeout}s",
            "FATAL: Service {service} crashed with code {code}",
        ]

        logs = []
        for i in range(count):
            template = np.random.choice(templates)
            log = template.format(
                host=f"db{np.random.randint(1, 5)}.company.com",
                port=np.random.randint(3000, 6000),
                user=f"user_{np.random.randint(1, 100)}",
                used=np.random.randint(8000, 12000),
                free=np.random.randint(100, 500),
                timeout=np.random.randint(30, 300),
                service=np.random.choice(['web', 'api', 'worker']),
                code=np.random.randint(1, 255)
            )
            logs.append(log)

        return logs

    @staticmethod
    def create_mixed_dataset(normal_count: int = 1000,
                           anomaly_count: int = 100) -> Tuple[List[str], List[int]]:
        """创建混合数据集"""
        normal_logs = TestDataManager.generate_normal_logs(normal_count)
        anomaly_logs = TestDataManager.generate_anomaly_logs(anomaly_count)

        all_logs = normal_logs + anomaly_logs
        labels = [0] * normal_count + [1] * anomaly_count

        # 打乱顺序
        combined = list(zip(all_logs, labels))
        np.random.shuffle(combined)
        logs, labels = zip(*combined)

        return list(logs), list(labels)
```

### 2. Mock和Fixture

```python
@pytest.fixture
def sample_log_entries():
    """日志条目fixture"""
    return [
        LogEntry(
            message="INFO: Application started",
            level="INFO",
            timestamp=datetime.now(),
            parameters={}
        ),
        LogEntry(
            message="ERROR: Database connection failed",
            level="ERROR",
            timestamp=datetime.now(),
            parameters={"error_code": 500}
        ),
        LogEntry(
            message="WARNING: High memory usage",
            level="WARNING",
            timestamp=datetime.now(),
            parameters={"memory_usage": 85.5}
        )
    ]

@pytest.fixture
def mock_model():
    """模拟模型fixture"""
    model = MagicMock()
    model.predict.return_value = np.array([[0.1, 0.9]])  # 正常预测
    return model

@pytest.fixture
def trained_deeplog():
    """训练好的DeepLog fixture"""
    deeplog = DeepLog(window_size=3, top_g=2, lstm_layers=1, lstm_units=16)

    # 生成训练数据
    normal_logs = TestDataManager.generate_normal_logs(50)

    # 训练模型
    deeplog.train(normal_logs, epochs=1, batch_size=8)

    return deeplog

class TestAnomalyDetector:
    """异常检测器测试"""

    def test_detect_normal_log(self, sample_log_entries, trained_deeplog):
        """测试正常日志检测"""
        normal_entry = sample_log_entries[0]  # INFO级别

        # 转换为日志字符串进行测试
        log_line = f"{normal_entry.timestamp} {normal_entry.level} {normal_entry.message}"

        is_anomaly, _, _ = trained_deeplog.detect(log_line)

        # INFO日志应该被认为是正常的
        assert not is_anomaly

    def test_detect_error_log(self, sample_log_entries, trained_deeplog):
        """测试错误日志检测"""
        error_entry = sample_log_entries[1]  # ERROR级别

        log_line = f"{error_entry.timestamp} {error_entry.level} {error_entry.message}"

        is_anomaly, anomaly_type, _ = trained_deeplog.detect(log_line)

        # ERROR日志应该被检测为异常
        assert is_anomaly
        assert anomaly_type in ['execution_path', 'performance', 'unknown']
```

### 3. 参数化测试

```python
class TestParameterized:
    """参数化测试"""

    @pytest.mark.parametrize("log_level,expected_anomaly", [
        ("INFO", False),
        ("WARNING", False),
        ("ERROR", True),
        ("CRITICAL", True),
        ("FATAL", True),
    ])
    def test_log_level_detection(self, trained_deeplog, log_level, expected_anomaly):
        """测试不同日志级别的检测"""
        log_line = f"Jan 15 10:30:45 localhost service: {log_level}: Test message"

        is_anomaly, _, _ = trained_deeplog.detect(log_line)

        assert is_anomaly == expected_anomaly

    @pytest.mark.parametrize("window_size,top_g,lstm_layers,lstm_units", [
        (5, 3, 1, 16),
        (10, 5, 2, 32),
        (3, 2, 1, 8),
    ])
    def test_different_configurations(self, window_size, top_g, lstm_layers, lstm_units):
        """测试不同配置的DeepLog"""
        deeplog = DeepLog(
            window_size=window_size,
            top_g=top_g,
            lstm_layers=lstm_layers,
            lstm_units=lstm_units
        )

        # 验证配置正确设置
        assert deeplog.window_size == window_size
        assert deeplog.top_g == top_g
        assert deeplog.lstm_layers == lstm_layers
        assert deeplog.lstm_units == lstm_units

        # 测试基本功能
        test_logs = ["INFO: Test message"] * 10
        deeplog.train(test_logs, epochs=1, batch_size=4)

        is_anomaly, _, _ = deeplog.detect("INFO: Another test message")
        assert isinstance(is_anomaly, bool)

    @pytest.mark.parametrize("batch_size,expected_success", [
        (1, True),
        (8, True),
        (32, True),
        (0, False),  # 无效批次大小
        (-1, False), # 无效批次大小
    ])
    def test_batch_size_validation(self, batch_size, expected_success):
        """测试批次大小验证"""
        deeplog = DeepLog()

        if expected_success:
            # 应该成功
            deeplog.train(
                ["INFO: Test"] * 20,
                epochs=1,
                batch_size=batch_size
            )
        else:
            # 应该失败
            with pytest.raises(ValidationError):
                deeplog.train(
                    ["INFO: Test"] * 20,
                    epochs=1,
                    batch_size=batch_size
                )
```

### 4. 性能和负载测试

```python
class TestPerformance:
    """性能测试"""

    @pytest.mark.slow
    @pytest.mark.parametrize("log_count", [100, 1000, 10000])
    def test_detection_performance(self, trained_deeplog, log_count):
        """测试检测性能"""
        # 生成测试日志
        test_logs = [f"INFO: Test message {i}" for i in range(log_count)]

        # 测量检测时间
        start_time = time.time()

        results = trained_deeplog.detect_batch(test_logs)

        end_time = time.time()
        duration = end_time - start_time

        # 计算性能指标
        throughput = log_count / duration  # 条/秒
        latency = duration / log_count * 1000  # 毫秒/条

        print(f"性能测试 ({log_count}条日志):")
        print(f"  总时间: {duration:.2f}秒")
        print(f"  吞吐量: {throughput:.1f}条/秒")
        print(f"  延迟: {latency:.2f}毫秒/条")

        # 性能断言
        assert throughput > 100, f"吞吐量太低: {throughput}"
        assert latency < 50, f"延迟太高: {latency}"

    def test_memory_usage(self, trained_deeplog):
        """测试内存使用"""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行大量检测
        test_logs = [f"INFO: Memory test {i}" for i in range(1000)]
        results = trained_deeplog.detect_batch(test_logs)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"内存使用测试:")
        print(f"  初始内存: {initial_memory:.1f}MB")
        print(f"  最终内存: {final_memory:.1f}MB")
        print(f"  内存增加: {memory_increase:.1f}MB")

        # 内存断言
        assert memory_increase < 100, f"内存泄漏: {memory_increase}MB"

    def test_concurrent_access(self, trained_deeplog):
        """测试并发访问"""
        import threading

        results = []
        errors = []

        def detect_worker(log_line):
            """检测工作线程"""
            try:
                result = trained_deeplog.detect(log_line)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = []
        test_logs = [f"INFO: Concurrent test {i}" for i in range(100)]

        for log_line in test_logs:
            thread = threading.Thread(target=detect_worker, args=(log_line,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(results) == len(test_logs), f"并发检测失败: {len(results)}/{len(test_logs)}"
        assert len(errors) == 0, f"并发检测出现错误: {errors}"
```

## 测试驱动的开发模式

### 1. 功能开发流程

```python
def develop_feature_tdd(feature_name: str, requirements: List[str]):
    """
    TDD方式开发功能

    Args:
        feature_name: 功能名称
        requirements: 需求列表
    """

    print(f"开始TDD开发: {feature_name}")

    for requirement in requirements:
        print(f"\n开发需求: {requirement}")

        # 1. 写测试 (Red)
        print("  1. 编写失败的测试...")
        test_code = generate_failing_test(requirement)
        write_test_file(test_code)

        # 运行测试，确保失败
        run_tests()
        assert tests_fail(), "测试应该失败"

        # 2. 实现功能 (Green)
        print("  2. 实现最简单的功能...")
        implementation = generate_simple_implementation(requirement)
        write_implementation_file(implementation)

        # 运行测试，确保通过
        run_tests()
        assert tests_pass(), "测试应该通过"

        # 3. 重构优化 (Refactor)
        print("  3. 重构和优化...")
        refactored_code = refactor_implementation(implementation)
        write_implementation_file(refactored_code)

        # 确保重构后测试仍通过
        run_tests()
        assert tests_pass(), "重构后测试应该仍通过"

    print(f"\n✅ {feature_name} 开发完成")

def generate_failing_test(requirement: str) -> str:
    """生成失败的测试代码"""
    # 根据需求生成测试代码
    if "异常检测" in requirement:
        return '''
def test_anomaly_detection_feature():
    """测试异常检测功能 - 目前应该失败"""
    detector = AnomalyDetector()
    # 这个功能还不存在，所以会失败
    result = detector.detect_advanced_anomaly("test log")
    assert result is not None
'''
    # 其他需求的测试生成逻辑...

def generate_simple_implementation(requirement: str) -> str:
    """生成最简单的实现"""
    if "异常检测" in requirement:
        return '''
def detect_advanced_anomaly(self, log_line: str) -> bool:
    """高级异常检测 - 最简单实现"""
    # 总是返回False（最简单的实现）
    return False
'''
    # 其他需求的实现生成逻辑...
```

### 2. 重构策略

```python
def refactor_implementation(code: str) -> str:
    """重构实现代码"""

    # 应用SOLID原则
    refactored = apply_solid_principles(code)

    # 应用设计模式
    refactored = apply_design_patterns(refactored)

    # 优化性能
    refactored = optimize_performance(refactored)

    # 改进可读性
    refactored = improve_readability(refactored)

    return refactored

def apply_solid_principles(code: str) -> str:
    """应用SOLID原则"""
    # 单一职责原则
    # 开闭原则
    # 里氏替换原则
    # 接口隔离原则
    # 依赖倒置原则
    pass

def apply_design_patterns(code: str) -> str:
    """应用设计模式"""
    # 策略模式（不同的检测算法）
    # 工厂模式（创建不同的解析器）
    # 观察者模式（监控和告警）
    # 装饰器模式（添加功能）
    pass
```

### 3. 持续集成

```python
def setup_ci_pipeline():
    """设置持续集成流水线"""

    pipeline = {
        'stages': [
            {
                'name': 'lint',
                'script': 'flake8 deeplog/ tests/',
                'artifacts': []
            },
            {
                'name': 'test',
                'script': 'pytest tests/ -v --cov=deeplog --cov-report=xml',
                'artifacts': ['coverage.xml']
            },
            {
                'name': 'performance_test',
                'script': 'pytest tests/ -k performance -v',
                'artifacts': ['performance_results.json']
            },
            {
                'name': 'integration_test',
                'script': 'pytest tests/ -k integration -v',
                'artifacts': ['integration_results.json']
            }
        ],
        'coverage_threshold': 90,
        'performance_thresholds': {
            'latency': '< 10ms',
            'throughput': '> 1000 req/s',
            'memory': '< 512MB'
        }
    }

    return pipeline

def run_quality_checks():
    """运行质量检查"""

    checks = [
        ('代码风格', 'flake8 deeplog/ tests/'),
        ('类型检查', 'mypy deeplog/'),
        ('安全检查', 'bandit -r deeplog/'),
        ('复杂度检查', 'radon cc deeplog/'),
        ('测试覆盖率', 'coverage run --source=deeplog -m pytest tests/'),
    ]

    results = {}
    for check_name, command in checks:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            success = result.returncode == 0
            results[check_name] = {
                'success': success,
                'output': result.stdout,
                'errors': result.stderr
            }
        except Exception as e:
            results[check_name] = {
                'success': False,
                'error': str(e)
            }

    return results
```

## 总结

测试驱动开发为 DeepLog 项目提供了以下优势：

1. **高质量代码**: 先写测试确保功能正确实现
2. **可维护性**: 全面的测试覆盖保证重构安全
3. **文档化**: 测试用例作为功能的使用示例
4. **回归保护**: 防止新功能破坏现有功能
5. **设计改进**: 测试先行帮助设计更好的API

通过遵循 TDD 原则，DeepLog 项目能够保持高质量的代码库和稳定的功能迭代。