# DeepLog: 基于深度学习的系统日志异常检测框架

DeepLog是一个基于LSTM的深度神经网络模型，用于系统日志的异常检测和诊断。

## 功能特性

- **日志键异常检测**：使用LSTM模型检测执行路径异常
- **参数值异常检测**：检测性能异常和参数值异常
- **在线检测**：支持实时流式异常检测
- **增量学习**：支持在线更新模型以适应新模式
- **工作流模型构建**：从日志序列构建有限状态自动机（FSA）工作流
- **多任务分离**：支持基于LSTM和密度聚类的任务分离方法
- **异常诊断**：使用工作流模型进行异常诊断和根本原因分析
- **评估框架**：提供完整的评估指标和对比工具

## 项目结构

```
deeplog/
├── deeplog/
│   ├── __init__.py
│   ├── parser.py              # 日志解析器
│   ├── models.py              # LSTM模型定义
│   ├── trainer.py             # 训练模块
│   ├── detector.py            # 异常检测模块
│   ├── workflow.py            # 工作流模型构建
│   ├── incremental_learner.py # 增量学习模块
│   ├── evaluator.py          # 评估模块
│   └── utils.py               # 工具函数
├── scripts/               # 实用脚本
├── tests/                 # 测试代码
├── requirements.txt       # 依赖包
└── README.md
```

## 安装

### 方法1：开发模式安装（推荐）

```bash
# 安装依赖
pip install -r requirements.txt

# 以开发模式安装包
pip install -e .
```

### 方法2：直接使用（无需安装）

如果不想安装包，示例脚本已经自动添加项目路径，可以直接运行：

```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行脚本（脚本会自动处理路径）
python scripts/basic_example.py
```

## 快速开始

### 基础使用

```python
from deeplog import DeepLog

# 1. 初始化DeepLog
deeplog = DeepLog(window_size=10, top_g=5, lstm_layers=2, lstm_units=64)

# 2. 准备正常日志数据（用于训练）
normal_logs = [
    "2024-01-01 10:00:00 INFO Starting application",
    "2024-01-01 10:00:01 INFO Connected to database",
    "2024-01-01 10:00:02 INFO User login successful",
    # ... 更多正常日志
]

# 3. 训练模型
deeplog.train(normal_logs, epochs=10, batch_size=32)

# 4. 检测异常
is_anomaly, anomaly_type, details = deeplog.detect("2024-01-01 10:00:10 ERROR Database error")
if is_anomaly:
    print(f"检测到异常: {anomaly_type}")
    print(f"详细信息: {details}")

# 5. 批量检测
results = deeplog.detect_batch(log_lines)

# 6. 保存模型
deeplog.save("models")

# 7. 加载模型
deeplog.load("models")

# 8. 构建工作流模型
workflows = deeplog.build_workflows(log_lines, method="lstm")

# 9. 异常诊断
is_anomaly, anomaly_type, workflow, diagnosis = deeplog.diagnose_anomaly(log_line)

# 10. 评估
from deeplog import evaluate_on_dataset
metrics = evaluate_on_dataset(deeplog, test_logs, ground_truth)
```

### 运行示例

```bash
# 基础训练和检测（使用logs目录下的真实日志）
python scripts/basic_example.py

# 高级功能演示
python scripts/advanced_example.py

# 工作流构建
python scripts/workflow_example.py

# 评估功能
python scripts/evaluation_example.py
```

## 参数说明

- `window_size (h)`: 历史窗口大小，默认10
- `top_g (g)`: 预测输出中top-g个候选键被视为正常，默认5
- `lstm_layers (L)`: LSTM层数，默认2
- `lstm_units (α)`: 每个LSTM块的单元数，默认64

## 日志导出工具

项目提供了日志导出工具，位于 `tools/` 目录：

### Windows系统日志导出

```bash
# 导出System日志
python tools/export_windows_logs.py --log System --output system_log.txt --max-events 1000

# 导出所有主要日志（System, Application, Security）
python tools/export_windows_logs.py --all --output-dir logs
```

**PowerShell方法（无需Python）:**
```powershell
Get-WinEvent -LogName System -MaxEvents 1000 | 
    Format-Table TimeCreated, Id, LevelDisplayName, Message -AutoSize | 
    Out-File -FilePath "windows_system_log.txt" -Encoding UTF8
```

### Linux系统日志导出

```bash
# 导出syslog
python tools/export_linux_logs.py --log-file /var/log/syslog --output syslog.txt

# 导出最近10000行
python tools/export_linux_logs.py --log-file /var/log/syslog --lines 10000

# 导出所有找到的日志
python tools/export_linux_logs.py --all --output-dir logs/linux_logs

# 查找Linux日志文件
python tools/export_linux_logs.py --find
```

**直接复制方法:**
```bash
# 复制日志文件
sudo cp /var/log/syslog ./syslog.txt
sudo cp /var/log/messages ./messages.txt

# 或只复制最近N行
sudo tail -n 10000 /var/log/syslog > syslog_recent.txt
```

### Apache日志导出

```bash
# 导出访问日志
python tools/export_apache_logs.py --log-file /var/log/apache2/access.log --output apache_access.txt

# 导出最近10000行
python tools/export_apache_logs.py --log-file access.log --lines 10000 --output recent_logs.txt

# 按日期范围导出
python tools/export_apache_logs.py --log-file access.log --start-date 2024-01-01 --end-date 2024-01-31

# 查找Apache日志文件
python tools/export_apache_logs.py --find
```

**直接复制方法:**
```bash
# Linux
cp /var/log/apache2/access.log ./apache_access.log
tail -n 10000 /var/log/apache2/access.log > apache_recent.log

# Windows
copy C:\Apache24\logs\access.log apache_access.log
```

### 使用导出的日志

```python
from deeplog import DeepLog

# 读取日志文件
with open('windows_system_log.txt', 'r', encoding='utf-8') as f:
    log_lines = [line.strip() for line in f if line.strip()]

# 训练模型
deeplog = DeepLog()
deeplog.train(log_lines, epochs=10)

# 检测异常
is_anomaly, anomaly_type, details = deeplog.detect(new_log_line)
```

## 参考文献

DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning
ACM Conference on Computer and Communications Security (CCS'17)

