# 日志导出指南

本指南介绍如何导出Windows系统日志和Apache日志，以便用于DeepLog训练和检测。

## Windows系统日志导出

### 方法1：使用PowerShell（推荐）

```powershell
# 导出所有事件日志
Get-WinEvent -ListLog * | ForEach-Object {
    $logName = $_.LogName
    $events = Get-WinEvent -LogName $logName -MaxEvents 1000 -ErrorAction SilentlyContinue
    if ($events) {
        $events | Format-Table -AutoSize | Out-File -FilePath "windows_log_$logName.txt" -Encoding UTF8
    }
}

# 导出特定日志（如System、Application、Security）
Get-WinEvent -LogName System -MaxEvents 1000 | 
    Format-Table TimeCreated, Id, LevelDisplayName, Message -AutoSize | 
    Out-File -FilePath "windows_system_log.txt" -Encoding UTF8

Get-WinEvent -LogName Application -MaxEvents 1000 | 
    Format-Table TimeCreated, Id, LevelDisplayName, Message -AutoSize | 
    Out-File -FilePath "windows_application_log.txt" -Encoding UTF8
```

### 方法2：使用wevtutil命令

```cmd
# 导出System日志
wevtutil epl System windows_system_log.evtx

# 导出Application日志
wevtutil epl Application windows_application_log.evtx

# 转换为文本格式（需要先安装Windows SDK或使用PowerShell）
wevtutil qe System /f:text /c:1000 > windows_system_log.txt
```

### 方法3：使用Python脚本（推荐用于DeepLog）

使用提供的 `tools/export_windows_logs.py` 脚本。

## Apache日志导出

### 方法1：直接复制日志文件

Apache日志通常位于以下位置：

**Linux:**
```bash
# 访问日志
/var/log/apache2/access.log
/var/log/httpd/access_log

# 错误日志
/var/log/apache2/error.log
/var/log/httpd/error_log
```

**Windows:**
```
C:\Apache24\logs\access.log
C:\Apache24\logs\error.log
```

### 方法2：使用命令行工具

**Linux:**
```bash
# 复制最近的日志
cp /var/log/apache2/access.log ./apache_access.log
cp /var/log/apache2/error.log ./apache_error.log

# 或者只复制最近的N行
tail -n 10000 /var/log/apache2/access.log > apache_access_recent.log
```

**Windows:**
```cmd
copy C:\Apache24\logs\access.log apache_access.log
copy C:\Apache24\logs\error.log apache_error.log
```

### 方法3：使用Python脚本

使用提供的 `tools/export_apache_logs.py` 脚本。

## 日志格式说明

### Windows事件日志格式
```
时间戳 | 级别 | 来源 | 事件ID | 消息
```

### Apache访问日志格式（默认）
```
IP地址 - - [时间戳] "请求方法 路径 HTTP版本" 状态码 响应大小 "Referer" "User-Agent"
```

### Apache错误日志格式
```
[时间戳] [级别] [模块] 消息
```

## 使用导出的日志

导出的日志可以直接用于DeepLog：

```python
from deeplog import DeepLog

# 读取日志文件
with open('windows_system_log.txt', 'r', encoding='utf-8') as f:
    log_lines = f.readlines()

# 训练模型
deeplog = DeepLog()
deeplog.train(log_lines, epochs=10)

# 检测异常
is_anomaly, anomaly_type, details = deeplog.detect(new_log_line)
```

## 注意事项

1. **编码格式**：确保日志文件使用UTF-8编码
2. **日志量**：建议使用至少1000-10000条正常日志进行训练
3. **时间范围**：使用最近一段时间的日志，确保反映当前系统状态
4. **隐私安全**：导出日志时注意保护敏感信息

