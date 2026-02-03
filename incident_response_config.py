# 应急响应日志溯源分析工具配置
# Incident Response Tool Configuration

# ========================================
# 日志源配置
# ========================================

# Linux日志文件路径配置
LINUX_LOGS = {
    "auth": "/var/log/auth.log",           # 认证日志
    "secure": "/var/log/secure",            # 安全日志
    "syslog": "/var/log/syslog",            # 系统日志
    "messages": "/var/log/messages",        # 消息日志
    "kern": "/var/log/kern.log",            # 内核日志
    "daemon": "/var/log/daemon.log",        # 守护进程日志
    "btmp": "/var/log/btmp",                # 失败登录
    "wtmp": "/var/log/wtmp",                # 登录记录
    "lastlog": "/var/log/lastlog",          # 最后登录
    "apache_access": "/var/log/apache2/access.log",
    "apache_error": "/var/log/apache2/error.log",
    "nginx_access": "/var/log/nginx/access.log",
    "nginx_error": "/var/log/nginx/error.log",
    "mysql": "/var/log/mysql/mysql.log",
    "postgresql": "/var/log/postgresql/postgresql.log",
}

# Windows日志文件路径配置
WINDOWS_LOGS = {
    "system": "System",
    "application": "Application",
    "security": "Security",
    "setup": "Setup",
    "forwarded": "Forwarded Events",
}

# Tomcat日志文件配置
TOMCAT_LOGS = {
    "catalina": "catalina.out",
    "localhost": "localhost.log",
    "manager": "manager.log",
    "host_manager": "host-manager.log",
    "access": "localhost_access_log.txt",
}

# ========================================
# 攻击检测规则配置
# ========================================

# 暴力破解阈值
BRUTE_FORCE = {
    "failed_login_threshold": 5,        # 失败登录阈值
    "lockout_threshold": 10,            # 锁定账户阈值
    "time_window_minutes": 5,           # 时间窗口（分钟）
}

# IP信誉配置
IP_REPUTATION = {
    "enable_blocklist_check": True,     # 启用黑名单检查
    "private_ip_ranges": [              # 私有IP范围
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
    ],
}

# ========================================
# 输出配置
# ========================================

OUTPUT = {
    "default_format": "txt",            # 默认输出格式
    "save_timeline": True,              # 保存时间线
    "max_events_display": 100,          # 最大显示事件数
    "critical_threshold": "high",       # 关键事件阈值
}

# ========================================
# 告警配置
# ========================================

ALERTS = {
    "critical_attacks": [               # 高危攻击类型
        "webshell",
        "privilege_escalation",
        "sql_injection",
        "command_injection",
    ],
    "notification": {
        "email": False,
        "webhook": False,
    },
}

# ========================================
# DeepLog集成配置
# ========================================

DEEPLOG = {
    "enabled": True,
    "model_path": "models/incident_response",
    "window_size": 10,
    "top_g": 5,
    "lstm_layers": 2,
    "lstm_units": 64,
}

# ========================================
# 常见攻击模式
# ========================================

ATTACK_SIGNATURES = {
    "sql_injection": [
        r"union select",
        r"or 1=1",
        r"' --",
        r"xp_cmdshell",
        r"information_schema",
    ],
    "xss": [
        r"<script>",
        r"javascript:",
        r"onerror=",
        r"onload=",
    ],
    "path_traversal": [
        r"\.\./",
        r"etc/passwd",
        r"boot.ini",
    ],
    "command_injection": [
        r";\s*cat\s",
        r";\s*ls\s",
        r"\|\s*wget",
        r"\|\s*curl",
    ],
}
