# DeepLog 项目结构说明

## 目录结构

```
deeplog/
├── deeplog/                    # 主包目录
│   ├── __init__.py            # 包初始化，导出主要类
│   ├── deeplog.py             # DeepLog主类，统一接口
│   ├── parser.py              # 日志解析器
│   ├── models.py              # LSTM模型定义（日志键模型和参数值模型）
│   ├── trainer.py             # 训练模块
│   ├── detector.py            # 异常检测模块
│   └── utils.py               # 工具函数
│
├── scripts/                    # 实用脚本
│   ├── basic_example.py       # 基础训练和检测脚本
│   └── advanced_example.py     # 高级功能演示脚本
│
├── requirements.txt           # Python依赖包
├── README.md                  # 项目说明文档
├── PROJECT_STRUCTURE.md       # 项目结构说明（本文件）
└── .gitignore                 # Git忽略文件

```

## 核心模块说明

### 1. `deeplog/parser.py` - 日志解析器
- **LogEntry**: 日志条目类，包含原始消息、日志键、参数值等
- **LogParser**: 日志解析器，将非结构化日志解析为结构化表示
  - `parse()`: 解析单条日志
  - `parse_batch()`: 批量解析日志
  - `parse_with_identifier()`: 根据标识符分组日志

### 2. `deeplog/models.py` - LSTM模型
- **LogKeyModel**: 日志键异常检测模型
  - 使用LSTM预测下一个日志键
  - 支持训练、预测、保存和加载
- **ParameterValueModel**: 参数值异常检测模型
  - 使用LSTM检测参数值序列中的异常
  - 支持多变量时间序列建模

### 3. `deeplog/trainer.py` - 训练模块
- **DeepLogTrainer**: DeepLog训练器
  - `train_log_key_model()`: 训练日志键模型
  - `train_parameter_models()`: 训练参数值模型

### 4. `deeplog/detector.py` - 检测模块
- **DeepLogDetector**: 异常检测器
  - `detect()`: 检测单条日志是否异常
  - 维护历史窗口用于预测
  - 支持日志键异常和参数值异常检测

### 5. `deeplog/deeplog.py` - 主类
- **DeepLog**: 统一接口类
  - `train()`: 训练模型
  - `detect()`: 检测单条日志
  - `detect_batch()`: 批量检测
  - `save()` / `load()`: 保存和加载模型
  - `update_model()`: 在线更新模型（增量学习）

### 6. `deeplog/utils.py` - 工具函数
- `extract_log_key()`: 提取日志键
- `extract_parameters()`: 提取参数值
- `normalize_parameters()`: 归一化参数
- `create_sequences()`: 创建滑动窗口序列
- `build_vocabulary()`: 构建词汇表
- `one_hot_encode()`: One-hot编码

## 工作流程

### 训练阶段
1. 使用`LogParser`解析正常日志
2. 提取日志键序列和参数值序列
3. 使用`DeepLogTrainer`训练LSTM模型
4. 保存训练好的模型

### 检测阶段
1. 解析新来的日志条目
2. 使用`DeepLogDetector`检测异常
3. 首先检测日志键是否异常（执行路径异常）
4. 如果日志键正常，检测参数值是否异常（性能异常）
5. 返回检测结果和详细信息

## 关键参数

- **window_size (h)**: 历史窗口大小，默认10
- **top_g (g)**: 预测输出中top-g个候选键被视为正常，默认5
- **lstm_layers (L)**: LSTM层数，默认2
- **lstm_units (α)**: 每个LSTM块的单元数，默认64

## 扩展点

1. **日志解析器**: 可以替换为更高级的解析器（如Spell）
2. **增量学习**: `update_model()`方法需要实现完整的在线学习逻辑
3. **工作流模型**: 可以添加工作流构建和诊断功能
4. **多任务分离**: 可以实现并发任务的日志分离功能

