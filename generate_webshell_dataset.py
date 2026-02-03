#!/usr/bin/env python3
"""生成高级 WebShell 测试数据集"""
import random
import datetime
from datetime import datetime, timedelta

def generate_webshell_attacks():
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)
    attacker_ips = ["45.154.255.147", "185.220.101.46", "91.121.87.18", "103.35.74.12"]
    normal_ips = ["192.168.1.100", "10.0.0.50"]
    user_agents = ["Mozilla/5.0", "curl/7.68.0"]

    for i in range(200):
        timestamp = base_time + timedelta(seconds=i * 30)
        r = random.random()
        src_ip = random.choice(attacker_ips) if r < 0.7 else random.choice(normal_ips)

        if r < 0.15:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "POST /uploads/shell.php HTTP/1.1" 200 23 "-"'
            logs.append(log)
        elif r < 0.25:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET /images/shell.gif HTTP/1.1" 200 500 "-"'
            logs.append(log)
        elif r < 0.35:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET /temp/x.php?cmd=id HTTP/1.1" 200 100 "-"'
            logs.append(log)
        elif r < 0.42:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "POST /admin/asp.aspx HTTP/1.1" 200 15 "-"'
            logs.append(log)
        elif r < 0.55:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET /uploads/test.php HTTP/1.1" 403 213 "-"'
            logs.append(log)
        else:
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET /api/users HTTP/1.1" 200 500 "{random.choice(user_agents)}"'
            logs.append(log)
    return logs

def generate_webshell_scan_logs():
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)
    scanner_ips = ["45.154.255.147", "185.220.101.46"]
    paths = ["/phpmyadmin/shell.php", "/uploads/shell.php", "/temp/shell.php", "/x.php", "/1.php"]

    for i in range(100):
        timestamp = base_time + timedelta(seconds=i * 10)
        src_ip = random.choice(scanner_ips)
        path = random.choice(paths)
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET {path} HTTP/1.1" {random.choice([404,403,200])} 0 "masscan"'
        logs.append(log)
    return logs

def main():
    print("生成 WebShell 测试数据集...")
    all_logs = generate_webshell_attacks() + generate_webshell_scan_logs()
    random.shuffle(all_logs)
    with open("D:/PycharmProjects/deeplog/logs/webshell_dataset.log", 'w', encoding='utf-8') as f:
        f.write("# WebShell Test Dataset\n")
        f.write('\n'.join(all_logs))
    print(f"完成！共 {len(all_logs)} 条日志")

if __name__ == "__main__":
    main()
