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
- **LSTM** - 长短期记忆网络 (DeepLog CCS'17)
- **MITRE ATT&CK** - 企业安全框架

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
