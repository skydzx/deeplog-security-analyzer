# DeepLog Security Analyzer

基于深度学习的智能安全日志分析平台

[![GitHub stars](https://img.shields.io/github/stars/skydzx/deeplog-security-analyzer)](https://github.com/skydzx/deeplog-security-analyzer/stargazers)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-61dafb)](https://reactjs.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK-FF6B6B)](https://attack.mitre.org/)

---

## 项目简介

DeepLog Security Analyzer 是一个基于 **DeepLog (CCS'17)** 论文架构的智能安全日志分析平台，结合深度学习与规则引擎，实现对系统日志的实时威胁检测与分析。

### 核心特性

- **🤖 深度学习检测**: 基于 LSTM 神经网络的日志异常检测
- **⚡ 实时分析**: 支持日志文件上传与在线粘贴分析
- **🎨 现代化界面**: React + Tailwind + Framer Motion 构建的酷炫 UI
- **📊 可视化报告**: 生成 HTML/JSON 格式的详细分析报告
- **🔗 MITRE ATT&CK**: 自动关联企业安全框架战术与技术
- **📁 多格式支持**: Apache、Nginx、SSH、Windows、K8s、数据库等

---

## 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  🛡️ DeepLog                    Dashboard  Analyze  Reports │
│                                                             │
│           Next-Gen Security Analytics                       │
│                                                             │
│     ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│     │ Critical │  │ High    │  │ Medium  │  │ Total   │  │
│     │   253   │  │  6306   │  │  4381   │  │  10940  │  │
│     └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                                                             │
│     Threat Level: ████████████░░░░░  8.5/10              │
│                                                             │
│     Upload File  or  Paste Logs                           │
│     ┌─────────────────────────────────────────────┐         │
│     │  Drag & drop your log file here            │         │
│     └─────────────────────────────────────────────┘         │
│                                                             │
│     Deep Learning  |  MITRE ATT&CK  |  Multi-Format      │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/skydzx/deeplog-security-analyzer.git
cd deeplog-security-analyzer

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
npm run build
cd ..
```

### 2. 启动服务

```bash
# 启动后端服务 (端口 5090)
python backend/app.py
```

### 3. 访问界面

打开浏览器访问: **http://localhost:5090**

---

## 功能演示

### 上传日志文件分析

1. 点击 `Upload File` 或拖拽日志文件
2. 支持 `.log`、`.txt`、`.json` 格式
3. 点击 `Start Analysis` 开始分析

### 粘贴日志快速分析

1. 点击 `Paste Logs` 切换到粘贴模式
2. 直接粘贴日志内容
3. 点击 `Start Analysis` 快速分析

### 检测的攻击类型

| 攻击类型 | 描述 | MITRE ATT&CK |
|---------|------|--------------|
| SQL 注入 | UNION SELECT、OR '1'='1 等 | T1190 |
| XSS 攻击 | 跨站脚本注入 | T1059 |
| WebShell | 可疑脚本文件名 | T1505 |
| 暴力破解 | SSH/FTP 密码尝试 | T1110 |
| 路径遍历 | ../ 敏感文件读取 | T1068 |
| 命令注入 | 系统命令执行 | T1059 |

---

## 项目结构

```
deeplog-security-analyzer/
├── backend/                    # Flask 后端
│   └── app.py                  # API 服务
├── frontend/                   # React 前端
│   ├── src/                    # 源代码
│   │   ├── App.jsx             # 主应用组件
│   │   └── index.css           # Tailwind 样式
│   └── dist/                   # 构建产物
├── tools/                      # 工具脚本
│   ├── analyze.py              # 日志分析工具
│   ├── security_incident_analyzer.py
│   ├── incident_response.py
│   └── ...
├── tests/                      # 测试文件
│   ├── test_anomaly_detection.py
│   ├── test_basic.py
│   └── run_tests.py
├── data_generators/            # 测试数据生成器
│   ├── generate_production_dataset.py
│   └── ...
├── config/                     # 配置文件
│   └── rules/                  # YAML 检测规则
│       ├── sql_injection.yaml
│       ├── webshell.yaml
│       └── ...
├── deeplog/                    # DeepLog 核心库
├── logs/                       # 日志文件目录
├── datasets/                   # 数据集目录
├── docs/                       # 文档
├── scripts/                    # 收集日志脚本
├── enhanced_security_analyzer.py  # 核心分析器
└── README.md
```

---

## 技术栈

### 后端
- **Python 3.8+** - 主语言
- **Flask** - Web 框架
- **Flask-CORS** - 跨域支持

### 前端
- **React 18** - UI 框架
- **Tailwind CSS** - 原子化 CSS
- **Framer Motion** - 动画库
- **Recharts** - 图表库
- **Lucide React** - 图标库

### 核心算法

#### DeepLog 深度学习模型

DeepLog 基于 **LSTM (Long Short-Term Memory)** 长短期记忆神经网络，这是论文 **"DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning" (CCS'17)** 的开源实现。

##### 核心思想

系统日志是按时间顺序生成的日志序列，具有固定的模式。LSTM 能够学习"正常日志应该长什么样"，从而检测出异常日志。

```
正常日志: INFO → INFO → INFO → INFO → INFO
攻击日志: INFO → INFO → ERROR → ERROR → FATAL
                         ↑
                      异常偏离
```

##### 模型架构

```
输入日志序列 ──→ One-Hot编码 ──→ LSTM×2层 ──→ Dense层 ──→ 预测下一个日志键
                                                    ↓
                                          概率分布 [P(A), P(B), P(C)...]
```

##### 两类异常检测模型

| 模型 | 输入 | 输出 | 检测目标 |
|-----|------|------|---------|
| **LogKeyModel** | 日志键序列 (如 `GET`, `POST`, `ERROR`) | 预测下一个键的概率分布 | 日志模式异常 |
| **ParameterValueModel** | 参数值向量 | 预测下一个参数值 | 参数值异常 |

##### 训练流程

```
正常日志 → LogParser解析 → 构建词汇表 → 滑动窗口 → LSTM训练 → 保存模型
    ↓              ↓            ↓            ↓           ↓
  数据源      提取日志键    唯一键映射    序列切分    TensorFlow
```

**滑动窗口示意 (window_size=3):**
```
日志序列: [A, B, C, D, E, F, G, H]
训练样本: [A,B,C]→D, [B,C,D]→E, [C,D,E]→F, [D,E,F]→G, [E,F,G]→H
```

##### 检测原理

1. **日志键异常**: 预测的下一个日志键概率 < 阈值，则触发告警
2. **参数值异常**: 预测参数与实际参数的 MSE > 阈值，则触发告警

##### 与传统机器学习对比

| 特性 | 传统机器学习 (RF/SVM) | DeepLog (LSTM) |
|-----|---------------------|----------------|
| 特征工程 | 需手工提取统计特征 | 自动学习特征 |
| 输入格式 | 固定维度向量 | 变长序列 |
| 时序依赖 | 无法利用 | 充分利用 |
| 典型算法 | Random Forest, Isolation Forest | LSTM, Transformer |
| 可解释性 | 较高 | 较低 |

##### 模型配置 (可调整)

```python
window_size = 10    # 历史窗口大小
lstm_layers = 2     # LSTM层层数
lstm_units = 64    # 每层单元数
batch_size = 32    # 批次大小
epochs = 10        # 训练轮数
```

##### 输出文件

训练完成后会生成两个文件：
- `.weights.h5` - LSTM模型权重
- `.config.pkl` - 词汇表和配置参数

#### MITRE ATT&CK

自动将检测到的威胁映射到 MITRE ATT&CK 企业框架，帮助安全分析师理解攻击者的战术和技术。

---

## API 接口

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/analyze` | POST | 上传文件分析 |
| `/api/quick-analyze` | POST | 粘贴日志分析 |
| `/api/rules` | GET | 获取检测规则 |
| `/api/reports` | GET | 获取报告列表 |
| `/api/health` | GET | 健康检查 |

---

## 演示数据

项目内置了多种测试数据集：

```bash
# 生成生产环境模拟数据 (10,900 条)
python data_generators/generate_production_dataset.py

# 生成 APT 攻击数据
python data_generators/generate_apt_dataset.py

# 生成 Log4j 漏洞利用数据
python data_generators/generate_log4j_dataset.py
```

---

## 许可证

MIT License

---

## 参考资料

- **DeepLog Paper**: "DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning" (CCS'17)
- **MITRE ATT&CK**: https://attack.mitre.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **React**: https://reactjs.org/

---

## 作者

**DeepLog Security Analyzer**

基于 DeepLog (CCS'17) 架构，结合现代 Web 技术构建的智能安全分析平台。

---

**Star us on GitHub!** ⭐
