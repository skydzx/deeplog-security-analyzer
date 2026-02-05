#!/usr/bin/env python3
"""
生成高级安全事件测试数据集
包含：DDoS、DNS隧道、内部威胁、勒索软件、横向移动等
"""

import random
import datetime
from datetime import datetime, timedelta

# 攻击源IP
ATTACK_IPS = [
    "185.220.101.46",   # Tor出口
    "45.154.255.147",   # 恶意
    "91.121.87.18",     # 法国
    "103.35.74.12",     # 亚洲
    "23.129.64.213",    # Tor
    "198.51.100.50",    # 模拟内部
]

# 内部IP
INTERNAL_IPS = [
    "192.168.1.100",    # 办公PC
    "192.168.1.101",    # 办公PC
    "10.0.0.50",        # 服务器
    "172.16.0.10",      # 数据库
]

def generate_ddos_attacks():
    """生成DDoS攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)

    attack_types = [
        ("SYN Flood", "TCP", "SYN"),
        ("UDP Flood", "UDP", "UDP"),
        ("ICMP Flood", "ICMP", "Echo"),
        ("HTTP Flood", "HTTP", "GET"),
        ("DNS Amplification", "DNS", "QUERY"),
        ("ACK Flood", "TCP", "ACK"),
        ("RST Flood", "TCP", "RST"),
        ("Connection Flood", "TCP", "SYN"),
    ]

    for i in range(300):
        timestamp = base_time + timedelta(seconds=i)
        attack_type, protocol, flag = random.choice(attack_types)
        src_ip = random.choice(ATTACK_IPS)
        # 模拟DDoS攻击日志
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} kernel: [ Firewall] {protocol}: {flag} flood from {src_ip}:{random.randint(1000, 65535)} to 192.168.1.10:{random.choice([80, 443, 53])} rate={random.randint(1000, 10000)}pps'
        logs.append(log)

    return logs

def generate_dns_tunneling():
    """生成DNS隧道攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 11, 0, 0)

    dns_tunnel_patterns = [
        "TgtXfer.evil.com",
        "data.exfil.org",
        "cmd.control.secure",
        "stage1.malware.xyz",
        "dns-tunnel.evil.net",
        "c2.stealthy.io",
        "exfil.data.hopto.org",
        "tunnel.encoded.io",
    ]

    for i in range(100):
        timestamp = base_time + timedelta(seconds=i*5)
        src_ip = random.choice(INTERNAL_IPS)
        domain = random.choice(dns_tunnel_patterns)
        query_type = random.choice(["TXT", "NULL", "MX", "CNAME"])
        data_len = random.randint(100, 5000)

        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} named[{random.randint(100,999)}]: query: {query_type} {domain} IN from {src_ip}:{random.randint(1000, 65535)} size={data_len} bytes'
        logs.append(log)

        # DNS隧道数据外泄
        if i % 10 == 0:
            log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} named[{random.randint(100,999)}]: response: TXT {domain} -> {src_ip} answer="{random.choice(["base64data==", "encrypted==", "data123"])}"'
            logs.append(log2)

    return logs

def generate_ransomware_activity():
    """生成勒索软件行为日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 12, 0, 0)

    ransomware_indicators = [
        ("加密文件", "/var/www/html/uploads/document.pdf", "randomname.encrypted"),
        ("加密文件", "/home/user/Documents/important.docx", "important.docx.locked"),
        ("加密文件", "/shared/finance/report.xlsx", "report.xlsx.crypt"),
        ("修改桌面", "/home/user/Desktop/README.txt", "README_FIX_YOUR_FILES.txt"),
        ("创建勒索信", "/var/www/html/RANSOM_NOTE.html", "SeeHowToRecover.html"),
        ("删除备份", "/var/backups/daily.bak", "DELETED"),
        ("停止服务", "mysql.service", "STOPPED"),
        ("停止服务", "nginx.service", "STOPPED"),
        ("加密文件", "/var/lib/postgresql/data/*.db", "ENCRYPTED"),
        ("加密文件", "/network/share/*.xls", "ENCRYPTED"),
    ]

    event_idx = 0
    for i in range(50):
        timestamp = base_time + timedelta(minutes=i)
        action = random.choice(ransomware_indicators)
        log = None
        log2 = None

        if "加密文件" in action[0]:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 kernel: [SUDO] root: COMMAND=/bin/chmod 000 {action[1]}'
            log2 = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 kernel: [ENCRYPTOR] {action[1]} -> {action[2]} (AES-256)'
        elif "修改桌面" in action[0]:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 gnome-shell: WARNING: Desktop wallpaper modified by process {random.randint(1000,9999)}'
            log2 = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 kernel: [ENCRYPTOR] Created {action[1]}'
        elif "创建勒索信" in action[0]:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 apache[${random.randint(1000,9999)}]: POST /uploads/{action[2]} HTTP/1.1 200'
        elif "停止服务" in action[0]:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 systemd[1]: {action[1]}: Main process exited, code=killed, status=15/TERM'
        else:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} server1 kernel: [ENCRYPTOR] {action[1]} {action[2]}'

        logs.append(log)
        if i % 8 == 0:
            logs.append(log2)

    return logs

def generate_lateral_movement():
    """生成横向移动攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 13, 0, 0)

    movement_steps = [
        # 初始访问
        ("192.168.1.100", "web-server", "SSH登录成功", "root"),
        # 凭证获取
        ("192.168.1.100", "web-server", "读取shadow文件", "/etc/shadow"),
        # 凭证利用
        ("192.168.1.100", "web-server", "横向到db-server", "10.0.0.50"),
        # 数据库访问
        ("10.0.0.50", "db-server", "MySQL登录", "admin"),
        # 数据收集
        ("10.0.0.50", "db-server", "导出数据库", "customers_dump.sql"),
        # 继续横向
        ("10.0.0.50", "db-server", "横向到file-server", "172.16.0.20"),
        # 持续控制
        ("172.16.0.20", "file-server", "创建后门用户", "backup_svc"),
        # 数据外泄
        ("172.16.0.20", "file-server", "上传数据到C2", "185.220.101.46"),
    ]

    for i, (src, tgt, action, detail) in enumerate(movement_steps):
        timestamp = base_time + timedelta(minutes=i*5)
        if "SSH" in action:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} sshd[{random.randint(1000,9999)}]: Accepted publickey for {detail} from {src} port {random.randint(10000, 60000)} ssh2'
        elif "读取" in action:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} sudo: {detail}: TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=cat {detail}'
        elif "横向" in action:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} sshd[{random.randint(1000,9999)}]: Failed password for root from {src} port {random.randint(10000, 60000)} ssh2'
            log2 = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} sshd[{random.randint(1000,9999)}]: Accepted password for {detail} from {src} port {random.randint(10000, 60000)} ssh2'
            logs.append(log)
            logs.append(log2)
            continue
        elif "MySQL" in action:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {tgt} mysql[{random.randint(1000,9999)}]: Connect root@{src} on using TCP/IP'
        elif "导出" in action:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {tgt} mysqldump: Selected tables: {detail}'
        elif "创建后门" in action:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} useradd[{random.randint(1000,9999)}]: new user with name \'{detail}\', UID {random.randint(1000,2000)}'
        elif "上传数据" in action:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} rsync[{random.randint(1000,9999)}]: sending incremental file list'
            log2 = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} rsync[{random.randint(1000,9999)}]: sent {random.randint(10000, 100000)} bytes total speed is {random.randint(1000, 10000)} KB/s'
            logs.append(log)
            logs.append(log2)
            continue
        else:
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {tgt} kernel: [LATERAL] {action}: {detail}'

        logs.append(log)

    return logs

def generate_phishing_attacks():
    """生成钓鱼攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 14, 0, 0)

    phishing_urls = [
        "/login.php?user=admin&redirect=https://fake-bank.com/verify",
        "/account/verify?token=PHISHING_TOKEN_123",
        "/secure/login?return=https://evil.com/callback",
        "/wp-admin/authorize?url=http://malicious.site",
        "/api/auth?callback=https://phishing.org/steal",
        "/microsoft/login?redirect=https://account-update-secure.com",
        "/apple/id/login?token=STOLEN",
    ]

    for i in range(80):
        timestamp = base_time + timedelta(seconds=i*10)
        src_ip = random.choice(ATTACK_IPS)
        url = random.choice(phishing_urls)
        user_agent = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ])

        # 钓鱼邮件点击
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET {url} HTTP/1.1" 200 {random.randint(100, 5000)} "{user_agent}"'
        logs.append(log)

        # 凭证提交
        if i % 5 == 0:
            log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "POST /login.php HTTP/1.1" 302 - "username=admin&password=pass123"'
            logs.append(log2)

    # 伪造登录页面访问
    for i in range(20):
        timestamp = base_time + timedelta(minutes=i*2)
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {random.choice(INTERNAL_IPS)} - - "GET /login.php?referrer=microsoft.com HTTP/1.1" 200 {random.randint(500, 2000)}'
        logs.append(log)

    return logs

def generate_database_attacks():
    """生成数据库攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 15, 0, 0)

    db_attacks = [
        # SQL注入
        ("SELECT * FROM users WHERE id=1 OR 1=1", "UNION injection"),
        ("SELECT username,password FROM users--", "UNION injection"),
        ("'; DROP TABLE users--", "DROP TABLE"),
        ("EXEC xp_cmdshell('whoami')", "xp_cmdshell"),
        ("GRANT ALL ON *.* TO 'hacker'@'%'", "Privilege escalation"),
        ("LOAD_FILE('/etc/passwd')", "File read"),
        ("INTO OUTFILE '/var/www/shell.php'", "File write"),
        ("BENCHMARK(10000000,SHA1('test'))", "DoS"),
        ("SELECT SLEEP(10)--", "Time-based blind"),
    ]

    for i in range(60):
        timestamp = base_time + timedelta(seconds=i*15)
        src_ip = random.choice(ATTACK_IPS)
        query, attack_type = random.choice(db_attacks)

        if "INTO OUTFILE" in query:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} MySQL[{random.randint(1000,9999)}]: QueryError: Access denied for user to database'
        else:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} mysql[{random.randint(1000,9999)}]: {query}'
        logs.append(log)

        # 错误日志
        if "OR 1=1" in query or "DROP" in query:
            log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} mysql[{random.randint(1000,9999)}]: Warning: {attack_type} detected in query'
            logs.append(log2)

    return logs

def generate_normal_traffic():
    """生成正常业务流量"""
    logs = []
    base_time = datetime(2024, 12, 20, 8, 0, 0)

    normal_users = ["192.168.1.100", "192.168.1.101", "10.0.0.50"]
    normal_pages = ["/", "/about", "/contact", "/products", "/api/users", "/api/orders"]

    for i in range(200):
        timestamp = base_time + timedelta(minutes=i*3)
        src_ip = random.choice(normal_users)
        page = random.choice(normal_pages)

        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET {page} HTTP/1.1" 200 {random.randint(100, 5000)}'
        logs.append(log)

    return logs

def main():
    print("生成高级安全事件测试数据集...")

    all_logs = []

    print("  - DDoS攻击日志...")
    all_logs.extend(generate_ddos_attacks())

    print("  - DNS隧道日志...")
    all_logs.extend(generate_dns_tunneling())

    print("  - 勒索软件行为日志...")
    all_logs.extend(generate_ransomware_activity())

    print("  - 横向移动日志...")
    all_logs.extend(generate_lateral_movement())

    print("  - 钓鱼攻击日志...")
    all_logs.extend(generate_phishing_attacks())

    print("  - 数据库攻击日志...")
    all_logs.extend(generate_database_attacks())

    print("  - 正常流量日志...")
    all_logs.extend(generate_normal_traffic())

    # 随机打乱
    random.shuffle(all_logs)

    # 添加文件头
    header = """# ============================================================
# 高级安全事件测试数据集
# 生成时间: 2024-12-20
# 包含: DDoS、DNS隧道、勒索软件、横向移动、钓鱼、数据库攻击
# ============================================================
"""

    output_file = "logs/advanced_security_dataset.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(filter(None, all_logs)))
        f.write('\n')

    print(f"\n完成！共生成 {len(all_logs)} 条日志")
    print(f"保存至: {output_file}")

if __name__ == "__main__":
    main()
