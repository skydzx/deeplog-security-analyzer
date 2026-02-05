#!/usr/bin/env python3
"""
生产环境真实日志数据集生成器
基于实际安全事件和攻击模式创建真实日志格式
"""

import random
import hashlib
from datetime import datetime, timedelta

def generate_production_logs():
    """生成生产环境真实日志"""
    logs = []
    base_time = datetime(2024, 1, 15, 0, 0, 0)

    # 生产环境服务器配置
    servers = [
        "web-prod-01.company.com",
        "api-prod-02.company.com",
        "db-prod-01.company.com",
        "auth-prod.company.com",
        "cdn-edge-01.company.com"
    ]

    # 真实攻击源IP (模拟恶意IP)
    malicious_ips = [
        "185.220.101.46",    # Tor exit
        "45.154.255.147",    # Proxy
        "91.121.87.18",      # France
        "103.35.74.12",      # China
        "23.129.64.213",     # Netherlands
        "198.51.100.50",     # Test range
        "203.0.113.100",     # Test range
        "192.168.100.50",    # Internal attacker
    ]

    # 正常用户IP池
    normal_ips = [f"203.0.113.{i}" for i in range(10, 100)]

    # 用户代理
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "curl/7.68.0",
        "python-requests/2.28.0",
    ]

    # SQL注入 payloads
    sql_payloads = ["' OR '1'='1", "UNION SELECT", "admin'--"]

    # ============== Apache/Nginx 访问日志 ==============
    print("生成 Web 访问日志...")
    for i in range(5000):
        timestamp = base_time + timedelta(seconds=i * 10)
        is_attack = random.random() < 0.05
        src_ip = random.choice(malicious_ips) if is_attack else random.choice(normal_ips)

        if is_attack:
            attack_type = random.choice([
                "sql_injection", "xss", "path_traversal", "webshell", "scan"
            ])

            if attack_type == "sql_injection":
                path = f"/products.php?id={random.choice(sql_payloads)}"
                status = random.choice(["200", "500", "403"])
            elif attack_type == "xss":
                path = f"/search?q=<script>alert({random.randint(1,100)})</script>"
                status = "200"
            elif attack_type == "path_traversal":
                path = f"/files?path=../../../etc/passwd"
                status = random.choice(["403", "404", "200"])
            elif attack_type == "webshell":
                path = f"/uploads/shell.php"
                status = random.choice(["200", "403", "404"])
            else:  # scan
                path = random.choice(["/admin", "/phpmyadmin", "/.env", "/wp-admin", "/backup.sql"])
                status = "404"

            log = f'{timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")} {src_ip} - - "GET {path} HTTP/1.1" {status} {random.randint(100,5000)} "{random.choice(user_agents)}"'
        else:
            path = random.choice([
                "/api/users", "/api/products", "/static/main.js",
                "/css/style.css", "/images/logo.png", "/health"
            ])
            log = f'{timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")} {random.choice(normal_ips)} - - "GET {path} HTTP/1.1" 200 {random.randint(50,5000)} "{random.choice(user_agents)}"'

        logs.append(log)

    # ============== SSH 认证日志 ==============
    print("生成 SSH 认证日志...")
    ssh_start = base_time + timedelta(hours=1)
    for i in range(2000):
        timestamp = ssh_start + timedelta(seconds=i * 5)
        is_bruteforce = random.random() < 0.03
        src_ip = random.choice(malicious_ips) if is_bruteforce else random.choice(normal_ips)

        if is_bruteforce:
            users = ["root", "admin", "ubuntu", "centos", "www-data", "mysql", "postgres"]
            user = random.choice(users)
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} sshd[{random.randint(1000,9999)}]: Failed password for {"invalid user " if random.random()<0.5 else ""}{user} from {src_ip} port {random.randint(10000,60000)} ssh2'
        else:
            user = random.choice(["ubuntu", "deploy", "admin", "developer"])
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} sshd[{random.randint(1000,9999)}]: Accepted publickey for {user} from {random.choice(normal_ips)} port {random.randint(40000,60000)} ssh2'

        logs.append(log)

    # ============== 系统日志 ==============
    print("生成系统日志...")
    sys_start = base_time + timedelta(hours=2)
    for i in range(1500):
        timestamp = sys_start + timedelta(minutes=i * 2)
        server = random.choice(servers)
        event_type = random.random()

        if event_type < 0.02:  # 安全事件
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {server} sudo: pam_unix(sudo:auth): authentication failure; logname=uid={random.randint(100,999)} tty= ruser= rhost= user=root'
        elif event_type < 0.04:  # 错误
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {server} kernel: [UFW BLOCK] IN=eth0 OUT= MAC=00:00:00:00:00:00 SRC={random.choice(malicious_ips)} DST={random.choice(["10.0.0.1", "10.0.0.5"])} LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT={random.randint(10000,65000)} DPT=22 WINDOW=5840 RES=0x00 ACK SYN URGP=0 '
        elif event_type < 0.06:  # 服务
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {server} systemd[{random.randint(1,100)}]: Started AWS SSM Agent ({random.choice(["Running", "Failed"])}).'
        else:  # 正常
            log = f'{timestamp.strftime("%b %d %H:%M:%S")} {server} CRON[{random.randint(1000,9999)}]: (root) CMD (/usr/local/bin/cleanup.sh)'

        logs.append(log)

    # ============== Docker/Kubernetes 日志 ==============
    print("生成容器日志...")
    k8s_start = base_time + timedelta(hours=3)
    for i in range(800):
        timestamp = k8s_start + timedelta(minutes=i * 3)
        pod_name = f"web-{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
        namespace = random.choice(["default", "production", "kube-system"])

        event = random.random()
        if event < 0.01:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")} {pod_name} {namespace}/ Warning FailedScheduling Pod could not be scheduled due to insufficient cpu'
        elif event < 0.02:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")} {pod_name} {namespace}/ Warning BackOff Back-off restarting failed container'
        elif event < 0.03:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")} {pod_name} {namespace}/ Normal Created Container created'
        else:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")} {pod_name} {namespace}/ Normal Started Pod started'

        logs.append(log)

    # ============== 数据库日志 ==============
    print("生成数据库日志...")
    db_start = base_time + timedelta(hours=4)
    for i in range(600):
        timestamp = db_start + timedelta(minutes=i * 5)
        server = "db-prod-01.company.com"
        is_attack = random.random() < 0.02

        if is_attack:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")} [{server}] [ERROR] [MY-000000] [Server] Got error: Access denied for user \'root\'@\'{random.choice(malicious_ips)}\' (using password: YES)'
        else:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")} [{server}] [Note] [MY-000000] [Server] Normal shutdown'

        logs.append(log)

    # ============== 防火墙/IDS 日志 ==============
    print("生成防火墙日志...")
    fw_start = base_time + timedelta(hours=5)
    for i in range(1000):
        timestamp = fw_start + timedelta(seconds=i * 3)

        attack = random.random()
        if attack < 0.1:
            src_ip = random.choice(malicious_ips)
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")} firewall=ALERT src={src_ip} dst=10.0.0.1 proto=tcp dport=443 action=DROP reason=Suspicious traffic pattern detected'
        elif attack < 0.15:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")} ids=SURICATA sig=1:1000001:0 src={random.choice(malicious_ips)} dst=10.0.0.5 msg="ET SCAN Potential SSH Scan OUTBOUND"'
        else:
            log = f'{timestamp.strftime("%Y-%m-%dT%H:%M:%S")} firewall=INFO src=10.0.0.{random.randint(10,200)} dst=10.0.0.1 proto=tcp dport=443 action=ACCEPT'

        logs.append(log)

    return logs

def main():
    print("=" * 60)
    print("生成生产环境真实日志数据集")
    print("=" * 60)

    all_logs = generate_production_logs()

    # 随机打乱
    random.shuffle(all_logs)

    # 写入文件
    output_file = "D:/PycharmProjects/deeplog/logs/production_dataset.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Production Environment Real Security Logs\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write("# Contains: Web, SSH, System, K8s, Database, Firewall logs\n")
        f.write("# Simulated with real attack patterns\n")
        f.write("=" * 60 + "\n")
        f.write('\n'.join(all_logs))
        f.write('\n')

    print(f"\n完成！共生成 {len(all_logs)} 条日志")
    print(f"保存至: {output_file}")

if __name__ == "__main__":
    main()
