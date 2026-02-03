# DeepLog AI 编程技能规范

## 概述

本目录包含为 DeepLog 项目定制的 AI 编程技能规范。这些规范旨在指导 AI 助手更好地理解项目需求，编写符合项目标准的代码，并遵循项目的开发最佳实践。

## 技能分类

### 🔬 核心算法技能

#### [deep_learning_log_anomaly_detection](deep_learning_log_anomaly_detection/SKILL.md)
- **适用场景**: 核心异常检测算法开发、模型架构设计、新功能模块实现
- **核心能力**:
  - LSTM/GRU 模型设计和优化
  - 多变量时间序列异常检测
  - 工作流构建和诊断
  - 增量学习和在线更新

#### [lstm_model_optimization](lstm_model_optimization/SKILL.md)
- **适用场景**: LSTM模型性能优化、训练策略改进、推理加速
- **核心能力**:
  - 模型架构搜索和优化
  - 训练过程优化（早停、学习率调度）
  - 推理优化（量化、缓存、批处理）
  - 性能监控和基准测试

### 🛠️ 工程技能

#### [exception_handling_and_error_management](exception_handling_and_error_management/SKILL.md)
- **适用场景**: 异常处理体系设计、错误恢复策略、用户体验优化
- **核心能力**:
  - 异常类层次结构设计
  - 错误处理策略和恢复机制
  - 用户友好的错误信息
  - 错误日志记录和诊断

#### [log_parsing_and_processing](log_parsing_and_processing/SKILL.md)
- **适用场景**: 日志解析器开发、数据预处理、特征提取
- **核心能力**:
  - 多格式日志解析（Linux/Windows/Apache）
  - 特征提取和编码
  - 性能优化和内存管理
  - 数据预处理流水线

### 🧪 测试和质量

#### [test_driven_development](test_driven_development/SKILL.md)
- **适用场景**: 新功能开发、重构、Bug修复、性能优化
- **核心能力**:
  - TDD开发流程（Red-Green-Refactor）
  - 测试层次结构（单元/集成/系统测试）
  - 参数化测试和Mock技术
  - 性能测试和质量保证

## 使用指南

### 1. 任务识别

根据开发任务类型选择合适的技能规范：

| 任务类型 | 推荐技能 | 优先级 |
|---------|---------|--------|
| 新异常检测算法 | deep_learning_log_anomaly_detection | 高 |
| 模型性能优化 | lstm_model_optimization | 高 |
| 错误处理改进 | exception_handling_and_error_management | 中 |
| 日志格式扩展 | log_parsing_and_processing | 中 |
| 功能重构 | test_driven_development | 高 |
| Bug修复 | test_driven_development | 高 |

### 2. 技能应用

```python
# 开发新异常检测算法的推荐流程：

# 1. 参考 deep_learning_log_anomaly_detection 技能
#    - 了解LSTM模型设计模式
#    - 学习多变量时间序列处理
#    - 掌握异常检测算法框架

# 2. 应用 test_driven_development 技能
#    - 先写测试用例（Red）
#    - 实现最简功能（Green）
#    - 重构优化代码（Refactor）

# 3. 使用 exception_handling_and_error_management 技能
#    - 设计适当的异常处理
#    - 提供用户友好的错误信息
#    - 实现错误恢复机制

# 4. 运用 log_parsing_and_processing 技能
#    - 确保数据预处理正确
#    - 优化特征提取效率
#    - 处理边界情况
```

### 3. 代码质量标准

所有代码必须符合以下标准：

#### 📝 代码风格
```python
# ✅ 推荐
from typing import List, Dict, Tuple, Optional
import numpy as np

def process_logs(logs: List[str], config: Dict[str, Any]) -> Tuple[bool, str, Dict]:
    """
    处理日志数据

    Args:
        logs: 日志行列表
        config: 配置参数

    Returns:
        (是否成功, 状态消息, 详细信息)

    Raises:
        ValidationError: 输入验证失败
        ProcessingError: 处理过程出错
    """
    pass

# ❌ 避免
def process(logs, config):  # 无类型注解
    # 缺少文档字符串
    pass
```

#### 🧪 测试覆盖
- **单元测试**: 每个公共函数都有测试
- **集成测试**: 模块间交互的测试
- **异常测试**: 错误情况的测试
- **边界测试**: 极端输入的测试

#### 🚨 错误处理
```python
# ✅ 推荐
from deeplog.exceptions import ValidationError, safe_execute

def robust_function(data):
    """健壮的函数实现"""
    # 输入验证
    if not isinstance(data, list):
        raise ValidationError("data必须是列表", field="data")

    # 安全执行
    result = safe_execute(
        self._process_data,
        data,
        error_context="数据处理"
    )

    return result

# ❌ 避免
def fragile_function(data):
    """脆弱的函数实现"""
    return self._process_data(data)  # 无错误处理
```

#### 📊 性能要求
- **推理延迟**: < 10ms/条日志
- **内存使用**: < 512MB 在正常负载下
- **准确率**: > 90% 在测试数据集上
- **测试覆盖率**: > 85%

## 技能更新

### 版本历史

- **v1.0.0** (2026-01-22): 初始版本
  - 包含4个核心技能规范
  - 覆盖主要开发场景
  - 提供详细的代码示例

### 更新计划

- [ ] 添加性能优化技能
- [ ] 增加部署和运维技能
- [ ] 添加API设计技能
- [ ] 完善文档生成技能

## 贡献指南

### 添加新技能

1. **确定需求**: 分析当前技能覆盖的空白
2. **设计规范**: 定义适用场景和核心能力
3. **编写示例**: 提供详细的代码示例
4. **测试验证**: 确保规范有效性
5. **文档更新**: 更新README和目录

### 技能文件结构

```
skill_name/
├── SKILL.md          # 技能规范文档
├── examples/         # 示例代码
│   ├── basic.py
│   ├── advanced.py
│   └── performance.py
└── templates/        # 代码模板
    ├── class_template.py
    ├── function_template.py
    └── test_template.py
```

## 联系和支持

- **项目主页**: [DeepLog GitHub](https://github.com/your-repo/deeplog)
- **问题反馈**: 通过GitHub Issues提交
- **贡献方式**: Fork + Pull Request

---

*DeepLog AI 编程技能规范 v1.0.0*