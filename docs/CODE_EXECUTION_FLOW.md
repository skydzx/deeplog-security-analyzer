# basic_example.py 代码执行流程详解

> **重要说明**：本文档中提到的"AI"或"模型"指的是**自己训练的深度学习模型（LSTM神经网络）**，不是调用OpenAI、Claude等大模型API。这个模型是在本地训练的，不需要联网，完全运行在你的电脑上。

## 一、程序入口

```python
if __name__ == "__main__":
    main()
```

**说明：** 程序从这里开始，调用 `main()` 函数。

---

## 二、main() 函数执行流程

### 步骤1：初始化DeepLog（第131-133行）

```python
print("\n1. 初始化DeepLog...")
deeplog = DeepLog(window_size=3, top_g=3, lstm_layers=1, lstm_units=32)
```

**在做什么：**
- 创建一个DeepLog对象，这是整个系统的"大脑"
- 设置参数：
  - `window_size=3`：看前3条日志，预测第4条
  - `top_g=3`：预测前3个最可能的，只要在实际值里就算正常
  - `lstm_layers=1`：LSTM只有1层（简单模型）
  - `lstm_units=32`：每层32个神经元

**内部发生了什么：**
- 创建了日志解析器（`LogParser`）
- 创建了训练器（`DeepLogTrainer`）
- 但模型还没训练，所以还不能检测异常

---

### 步骤2：准备训练数据（第136-138行）

```python
print("\n2. 准备训练数据...")
normal_logs = load_logs_from_directory('logs', max_logs=5000)
print(f"训练日志数量: {len(normal_logs)}")
```

**在做什么：**
- 调用 `load_logs_from_directory()` 函数，从 `logs/` 目录加载日志文件

**`load_logs_from_directory()` 函数详解（第17-110行）：**

#### 2.1 查找日志文件（第35-58行）

```python
# 查找所有日志文件并按类型分类
for pattern in ['*.txt', '*.log']:
    # Windows日志（支持多种命名方式）
    for windows_pattern in ['windows_logs', 'local_windows_logs', '*windows*']:
        windows_files = glob.glob(os.path.join(log_dir, windows_pattern, pattern))
    # Linux日志（支持多种命名方式）
    for linux_pattern in ['linux_logs', 'local_linux_logs', '*linux*']:
        linux_files = glob.glob(os.path.join(log_dir, linux_pattern, pattern))
    # Apache日志（支持多种命名方式）
    apache_files = glob.glob(os.path.join(log_dir, '*apache*', pattern))
    # GitHub LogHub数据集
    github_files = glob.glob(os.path.join(log_dir, 'github_loghub', '*.log'))
```

**在做什么：**
- 在 `logs/` 目录下找所有 `.txt` 和 `.log` 文件
- 按类型分类：Windows、Linux、Apache
- 支持多种目录命名方式：
  - Windows: `windows_logs`、`local_windows_logs`、任何包含`windows`的目录
  - Linux: `linux_logs`、`local_linux_logs`、任何包含`linux`的目录
  - Apache: 任何包含`apache`的目录（如`local_phpstudy_apache_logs`）
  - GitHub LogHub: `github_loghub`目录

**实际例子（当前项目结构）：**
```
logs/
  ├── local_windows_logs/
  │   ├── windows_application_log.txt  ← 找到这个
  │   ├── windows_security_log.txt     ← 找到这个
  │   └── windows_system_log.txt       ← 找到这个
  ├── local_linux_logs/
  │   ├── linux_auth_log.txt           ← 找到这个
  │   ├── linux_kern_log.txt           ← 找到这个
  │   └── linux_syslog_log.txt         ← 找到这个
  ├── local_phpstudy_apache_logs/
  │   ├── access.log.*                 ← 找到这些
  │   └── error.log                    ← 找到这个
  └── github_loghub/
      ├── Windows_2k.log               ← 找到这个
      ├── Linux_2k.log                ← 找到这个
      └── Apache_2k.log               ← 找到这个
```

#### 2.2 读取日志内容（第81-97行）

```python
for log_type, files in log_files_by_type.items():
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line:
                    logs_by_type[log_type].append(line)
```

**在做什么：**
- 打开每个日志文件，逐行读取
- 去掉空行，把有效日志存起来
- 每类日志最多读 `max_logs // 3` 条（比如5000条，每类约1666条）

**实际例子：**
```
文件内容：
"2024-01-01 10:00:00 INFO Starting application"
"2024-01-01 10:00:01 INFO Connected to database"
"2024-01-01 10:00:02 INFO User login successful"

↓ 读取后

normal_logs = [
    "2024-01-01 10:00:00 INFO Starting application",
    "2024-01-01 10:00:01 INFO Connected to database",
    "2024-01-01 10:00:02 INFO User login successful",
    ...
]
```

#### 2.3 合并和打乱（第99-108行）

```python
# 合并所有日志
for logs in logs_by_type.values():
    log_lines.extend(logs)

# 随机打乱
random.shuffle(log_lines)
```

**在做什么：**
- 把Windows、Linux、Apache的日志合并在一起
- 随机打乱顺序（这样训练时不会偏向某类日志）

**如果没有找到日志文件（第70-73行）：**
```python
if not all_files:
    return generate_sample_logs()  # 使用示例数据
```

**`generate_sample_logs()` 函数（第113-122行）：**
- 如果没找到真实日志，就生成一些示例日志
- 这些是假的日志，只是为了演示

---

### 步骤3：训练模型（第141-153行）

```python
print("\n3. 训练模型...")
deeplog.train(
    normal_logs,
    train_key_model=True,      # 训练日志键模型
    train_param_models=True,   # 训练参数值模型
    epochs=5,                  # 训练5轮
    batch_size=8               # 每批8条日志
)
```

**在做什么：**
- 把正常日志传给**自己训练的LSTM模型**，让它学习"正常的样子"（注意：这是本地训练的模型，不是调用大模型API）

**`deeplog.train()` 内部发生了什么：**

#### 3.1 解析日志（第66行）

```python
log_entries = self.parser.parse_batch(log_lines, timestamps)
```

**在做什么：**
- 把每条原始日志解析成结构化数据
- 提取日志模板和参数值

**例子：**
```
原始日志: "2024-01-01 10:00:00 INFO User login user_id=12345"
↓ 解析后
LogEntry:
  - log_key: "INFO User login user_id=*"
  - parameters: [12345]
  - timestamp: 2024-01-01 10:00:00
```

#### 3.2 训练日志键模型（第72-77行）

```python
if train_key_model:
    self.log_key_model = self.trainer.train_log_key_model(
        log_entries, epochs=epochs, batch_size=batch_size
    )
```

**在做什么：**
- 用LSTM学习日志出现的顺序规律
- 看前3条日志，预测第4条应该是什么

**训练过程：**
```
输入序列：
1. "INFO Starting application"
2. "INFO Connected to database"
3. "INFO User login"

↓ LSTM处理

预测输出：
1. "INFO Processing request" (概率0.4)
2. "INFO Request completed" (概率0.3)
3. "INFO User logout" (概率0.2)
...
```

#### 3.3 训练参数值模型（第80-90行）

```python
if train_param_models:
    self.parameter_models = self.trainer.train_parameter_models(
        log_entries, epochs=epochs, batch_size=batch_size
    )
```

**在做什么：**
- 对于每种日志模板，单独训练一个模型
- 学习参数值的正常范围

**训练过程：**
```
对于 "INFO Request completed in * seconds" 这个模板：
收集所有参数值: [0.1, 0.2, 0.15, 0.3, 0.25, ...]
↓ 训练模型

模型学会：正常范围是 0.1-0.5 秒
如果新日志是 100 秒 → 异常！
```

#### 3.4 创建检测器（第93-96行）

```python
if self.log_key_model:
    self.detector = DeepLogDetector(
        self.log_key_model, self.parameter_models, self.top_g
    )
```

**在做什么：**
- 把训练好的模型传给检测器
- 检测器会用这些模型来检测异常

---

### 步骤4：检测正常日志（第156-217行）

```python
print("\n4. 检测正常日志（从训练数据中选取，包含不同类型）...")
```

**在做什么：**
- 从训练数据中选几条日志，测试**训练好的模型**能否正确识别为"正常"

#### 4.1 选择测试日志（第157-166行）

```python
if len(normal_logs) > deeplog.window_size + 10:
    test_indices = [
        deeplog.window_size + 10,  # 第13条
        len(normal_logs) // 2,     # 中间那条
        len(normal_logs) - 10       # 倒数第10条
    ]
    test_normal_logs = [normal_logs[i] for i in test_indices]
```

**在做什么：**
- 从训练数据的不同位置选3条日志
- 确保有足够的历史上下文（因为需要前3条才能预测）

#### 4.2 识别日志类型（第169-200行）

```python
def identify_log_type(log_line):
    # Windows事件日志特征
    if 'EventID' in log_line or ...:
        return "Windows"
    # Apache日志特征
    elif re.match(r'^\[(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', log_line):
        return "Apache"
    # Linux系统日志特征
    elif re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', log_line):
        return "Linux"
    return "未知"
```

**在做什么：**
- 通过格式特征判断日志类型
- 只是为了显示时更清楚，不影响检测

#### 4.3 执行检测（第202-216行）

```python
for log in test_normal_logs:
    is_anomaly, anomaly_type, details = deeplog.detect(log)
    status = "异常" if is_anomaly else "正常"
    print(f"\n日志 [{log_type}]: {log_display}")
    print(f"  状态: {status}")
```

**`deeplog.detect()` 内部发生了什么：**

1. **解析日志**（第113行）
   ```python
   log_entry = self.parser.parse(log_line, timestamp)
   ```

2. **检测异常**（第116行）
   ```python
   return self.detector.detect(log_entry)
   ```

3. **检测器的工作流程**（`detector.py`）：
   - 检查日志键是否在预测列表中
   - 如果不在 → 异常（执行路径异常）
   - 如果在，检查参数值是否正常
   - 如果参数值异常 → 异常（参数值异常）

**实际例子：**
```
历史日志（前3条）：
1. "INFO Starting application"
2. "INFO Connected to database"
3. "INFO User login"

新日志："INFO Processing request"

↓ 检测过程

1. LSTM预测：下一条最可能的3个是
   - "INFO Processing request" (概率0.4) ✓
   - "INFO Request completed" (概率0.3)
   - "INFO User logout" (概率0.2)

2. 新日志在预测列表中 → 正常！

结果：is_anomaly = False, status = "正常"
```

---

### 步骤5：检测异常日志（第219-238行）

```python
print("\n5. 检测异常日志...")
anomaly_logs = [
    "ERROR Critical system failure detected",
    "CRITICAL Database corruption occurred", 
    "FATAL Application crashed with exception",
]

for log in anomaly_logs:
    is_anomaly, anomaly_type, details = deeplog.detect(log)
```

**在做什么：**
- 用明显的异常日志测试**训练好的模型**能否正确识别

**检测过程：**
```
历史日志（前3条）：
1. "INFO Starting application"
2. "INFO Connected to database"
3. "INFO User login"

新日志："ERROR Critical system failure detected"

↓ 检测过程

1. LSTM预测：下一条最可能的3个是
   - "INFO Processing request" (概率0.4)
   - "INFO Request completed" (概率0.3)
   - "INFO User logout" (概率0.2)

2. 新日志 "ERROR Critical system failure detected" 不在预测列表中 → 异常！

结果：is_anomaly = True, anomaly_type = "执行路径异常"
```

**显示预测结果（第233-238行）：**
```python
if details.get('predictions'):
    print(f"  预测的top-3日志键:")
    for i, (key, prob) in enumerate(details['predictions'][:3], 1):
        print(f"    {i}. [{prob:.4f}] {key_display}")
```

**在做什么：**
- 显示**模型预测**的"应该是什么"
- 这样可以看到模型的"想法"（模型是基于你提供的训练数据学习的）

---

### 步骤6：保存模型（第241-246行）

```python
print("\n6. 保存模型...")
deeplog.save("models")
print("模型已保存到 models/ 目录")
```

**在做什么：**
- 把训练好的模型保存到 `models/` 目录
- 下次可以直接加载，不用重新训练

**保存的内容：**
```
models/
  ├── log_key_model.config.pkl      # 日志键模型的配置
  ├── log_key_model.weights.h5       # 日志键模型的权重
  ├── param_model_*.config.pkl      # 各个参数值模型的配置
  └── param_model_*.weights.h5      # 各个参数值模型的权重
```

---

## 三、完整执行流程图

```
开始
  ↓
1. 初始化DeepLog
  ├─ 创建解析器
  ├─ 创建训练器
  └─ 模型 = None（还没训练）
  ↓
2. 加载日志文件
  ├─ 查找 logs/ 目录下的文件（支持local_windows_logs、local_linux_logs、local_phpstudy_apache_logs、github_loghub等目录）
  ├─ 读取日志内容
  └─ 合并并打乱
  ↓
3. 训练模型
  ├─ 解析日志（提取模板和参数）
  ├─ 训练日志键模型（学习顺序规律）
  ├─ 训练参数值模型（学习数值范围）
  └─ 创建检测器
  ↓
4. 测试正常日志
  ├─ 从训练数据选几条
  ├─ 调用 detect() 检测
  └─ 应该识别为"正常"
  ↓
5. 测试异常日志
  ├─ 用明显的异常日志
  ├─ 调用 detect() 检测
  └─ 应该识别为"异常"
  ↓
6. 保存模型
  └─ 保存到 models/ 目录
  ↓
结束
```

---

## 四、关键函数调用链

### 检测一条日志的完整流程：

```
deeplog.detect(log_line)
  ↓
1. parser.parse(log_line)
   └─ 返回 LogEntry（包含 log_key 和 parameters）
  ↓
2. detector.detect(log_entry)
   ├─ 2.1 _detect_key_anomaly()
   │    ├─ log_key_model.predict()  # 预测下一条
   │    └─ 检查是否在 top_g 列表中
   │
   └─ 2.2 _detect_parameter_anomaly()（如果日志键正常）
        ├─ parameter_models[log_key].predict()  # 预测参数值
        └─ 计算MSE，检查是否超过阈值
  ↓
3. 返回 (is_anomaly, anomaly_type, details)
```

---

## 五、实际运行示例

假设有以下日志：

```
训练数据：
1. "2024-01-01 10:00:00 INFO Starting application"
2. "2024-01-01 10:00:01 INFO Connected to database"
3. "2024-01-01 10:00:02 INFO User login user_id=12345"
4. "2024-01-01 10:00:03 INFO Processing request request_id=req001"
5. "2024-01-01 10:00:04 INFO Request completed in 0.5 seconds"
```

### 训练阶段：

1. **解析日志**：
   - 日志1 → 模板："INFO Starting application"，参数：[]
   - 日志2 → 模板："INFO Connected to database"，参数：[]
   - 日志3 → 模板："INFO User login user_id=*"，参数：[12345]
   - ...

2. **训练日志键模型**：
   - 学习到：看到"Starting application"后，通常接下来是"Connected to database"
   - 学习到：看到"User login"后，通常接下来是"Processing request"

3. **训练参数值模型**：
   - 对于"INFO Request completed in * seconds"：
     - 收集参数值：[0.5, 0.3, 0.4, ...]
     - 学习到：正常范围是 0.1-0.8 秒

### 检测阶段：

**测试1：正常日志**
```
新日志："INFO Processing request request_id=req002"

检测过程：
1. 历史窗口：[日志1, 日志2, 日志3]
2. LSTM预测：下一条最可能的3个
   - "INFO Processing request" ✓（在列表中）
   - "INFO Request completed"
   - "INFO User logout"
3. 新日志在预测列表中 → 正常！
4. 检查参数值：request_id=req002（正常范围）→ 正常！

结果：is_anomaly = False
```

**测试2：异常日志**
```
新日志："ERROR Database crashed"

检测过程：
1. 历史窗口：[日志1, 日志2, 日志3]
2. LSTM预测：下一条最可能的3个
   - "INFO Processing request"
   - "INFO Request completed"
   - "INFO User logout"
3. 新日志 "ERROR Database crashed" 不在预测列表中 → 异常！

结果：is_anomaly = True, anomaly_type = "执行路径异常"
```

---

## 六、总结

**整个程序的执行流程：**

1. **准备阶段**：初始化系统，加载日志数据
2. **学习阶段**：**本地训练的LSTM模型**学习正常日志的规律（在你的电脑上训练，不需要联网）
3. **测试阶段**：用正常和异常日志测试训练好的模型
4. **保存阶段**：保存训练好的模型到本地文件

**核心思想：**
- 给**本地训练的LSTM模型**看大量正常日志，让它学会"正常的样子"（模型是在你的电脑上训练的，不是调用大模型API）
- 新日志来了，看它是否符合"正常的样子"
- 不符合就是异常

**关键点：**
- `window_size=3`：看前3条，预测第4条
- `top_g=3`：预测前3个最可能的，只要在实际值里就算正常
- 双重检测：先检查日志模板，再检查参数值

