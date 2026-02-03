#!/usr/bin/env python3
"""
应急响应日志溯源分析工具 - Incident Response Log Forensics Tool

功能：
1. 多类型日志解析（Linux/Windows/Tomcat/Nginx）
2. 攻击模式检测（暴力破解、SQL注入、Webshell等）
3. 时间线重建
4. 溯源分析
5. 风险评估报告

使用方法：
python incident_response.py --linux /var/log/auth.log
python incident_response.py --windows windows_log.txt
python incident_response.py --tomcat catalina.log
python incident_response.py --nginx access.log
python incident_response.py --all --input logs/
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from deeplog import DeepLog
    HAS_DEEPLOG = True
except ImportError:
    HAS_DEEPLOG = False
    print("[警告] DeepLog未安装，将使用规则引擎进行检测")


class ThreatLevel(Enum):
    """威胁等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AttackType(Enum):
    """攻击类型"""
    BRUTE_FORCE = "暴力破解"
    SQL_INJECTION = "SQL注入"
    XSS = "XSS攻击"
    WEBSHELL = "Webshell"
    FILE_UPLOAD = "文件上传攻击"
    PATH_TRAVERSAL = "路径遍历"
    COMMAND_INJECTION = "命令注入"
    BUFFER_OVERFLOW = "缓冲区溢出"
    PRIVILEGE_ESCALATION = "权限提升"
    UNAUTHORIZED_ACCESS = "未授权访问"
    DENIAL_OF_SERVICE = "拒绝服务"
    SUSPICIOUS_LOGIN = "可疑登录"
    MALWARE = "恶意软件"
    PORT_SCAN = "端口扫描"
    UNKNOWN = "未知"


@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: datetime
    source_ip: Optional[str] = None
    target: Optional[str] = None
    event_type: str = ""
    raw_log: str = ""
    threat_level: ThreatLevel = ThreatLevel.INFO
    attack_type: AttackType = AttackType.UNKNOWN
    details: Dict = field(default_factory=dict)
    timeline_order: int = 0


class AttackPatternEngine:
    """攻击模式检测引擎"""

    # 攻击模式正则表达式
    PATTERNS = {
        AttackType.BRUTE_FORCE: [
            r'Failed password.*from\s+([\d.]+)',
            r'authentication failure.*ip=([\d.]+)',
            r'Invalid user.*from\s+([\d.]+)',
            r'Connection closed.*auth',
            r'wrong password.*attempt',
            r'Failed.*ssh.*[0-9]{1,3}\.[0-9]{1,3}',
        ],
        AttackType.SQL_INJECTION: [
            r"('|%).*(or|and).*(=|--)",
            r'union.*select',
            r'select.*from.*where',
            r'exec.*xp_cmdshell',
            r'Information_schema',
            r"'\s*OR\s*'1'\s*=\s*'1",
        ],
        AttackType.XSS: [
            r'<script>',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'alert\(',
            r'document\.cookie',
        ],
        AttackType.WEBSHELL: [
            r'cmd\.php',
            r'shell\.php',
            r'eval\(',
            r'system\(',
            r'passthru\(',
            r'assert\(',
            r'\$_(GET|POST|REQUEST)\[',
            r'base64_decode\(',
        ],
        AttackType.FILE_UPLOAD: [
            r'\.php.*upload',
            r'\.asp.*upload',
            r'\.jsp.*upload',
            r'\.exe.*upload',
            r'uploader.*php',
        ],
        AttackType.PATH_TRAVERSAL: [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e',
            r'\.\.%2f',
            r'etc/passwd',
            r'boot\.ini',
        ],
        AttackType.COMMAND_INJECTION: [
            r';\s*(cat|ls|wget|curl|nc)',
            r'\|(cat|ls|wget|curl|nc)',
            r'`.*(cat|ls|wget|curl|nc)',
            r'\$(cat|ls|wget|curl|nc)',
        ],
        AttackType.PRIVILEGE_ESCALATION: [
            r'sudo.*(root|admin)',
            r'su\s+(root|admin)',
            r'chmod\s+[47][0-7][0-7][0-7]',
            r'chown.*root.*root',
        ],
        AttackType.PORT_SCAN: [
            r'Connect.*port\s+[0-9]+',
            r'Port.*scan',
            r'nmap',
            r'masscan',
            r'connect from.*port',
        ],
        AttackType.SUSPICIOUS_LOGIN: [
            r'login.*success.*from\s+([\d.]+)',
            r'session opened',
            r'authenticated.*root',
            r'ssh.*[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',
        ],
    }

    # Windows事件ID映射
    WINDOWS_EVENT_PATTERNS = {
        4624: (ThreatLevel.INFO, AttackType.SUSPICIOUS_LOGIN, "成功登录"),
        4625: (ThreatLevel.MEDIUM, AttackType.BRUTE_FORCE, "登录失败"),
        4648: (ThreatLevel.LOW, AttackType.SUSPICIOUS_LOGIN, "显式凭据登录"),
        4672: (ThreatLevel.HIGH, AttackType.PRIVILEGE_ESCALATION, "管理员登录"),
        4688: (ThreatLevel.INFO, AttackType.UNKNOWN, "新进程创建"),
        4689: (ThreatLevel.INFO, AttackType.UNKNOWN, "进程退出"),
        4720: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "用户账户创建"),
        4722: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "用户账户启用"),
        4724: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "密码重置"),
        4725: (ThreatLevel.MEDIUM, AttackType.UNAUTHORIZED_ACCESS, "用户账户禁用"),
        4726: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "用户账户删除"),
        4733: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "成员从安全组删除"),
        4735: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "安全组修改"),
        4740: (ThreatLevel.HIGH, AttackType.BRUTE_FORCE, "账户锁定"),
        4756: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "成员添加到通用安全组"),
        4964: (ThreatLevel.HIGH, AttackType.PRIVILEGE_ESCALATION, "特殊组登录"),
    }

    def __init__(self):
        self.compiled_patterns = {}
        for attack_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[attack_type] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def detect(self, log_line: str) -> Tuple[Optional[AttackType], Optional[ThreatLevel], Optional[Dict]]:
        """检测日志中的攻击模式"""
        for attack_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(log_line)
                if match:
                    details = {"matched_pattern": pattern.pattern}
                    if match.groups():
                        details["captured"] = match.groups()

                    # 根据攻击类型设置威胁等级
                    threat_level = ThreatLevel.MEDIUM
                    if attack_type in [AttackType.WEBSHELL, AttackType.PRIVILEGE_ESCALATION]:
                        threat_level = ThreatLevel.HIGH
                    elif attack_type in [AttackType.BRUTE_FORCE, AttackType.COMMAND_INJECTION]:
                        threat_level = ThreatLevel.MEDIUM
                    elif attack_type in [AttackType.SQL_INJECTION, AttackType.XSS]:
                        threat_level = ThreatLevel.HIGH

                    return attack_type, threat_level, details

        return None, None, None

    def detect_windows_event(self, event_id: int, level: str) -> Tuple[Optional[AttackType], Optional[ThreatLevel], str]:
        """检测Windows事件"""
        if event_id in self.WINDOWS_EVENT_PATTERNS:
            base_level, attack_type, desc = self.WINDOWS_EVENT_PATTERNS[event_id]
            # 提升失败登录的威胁等级
            if event_id == 4625:
                if level == "Error":
                    base_level = ThreatLevel.HIGH
            return attack_type, base_level, desc
        return None, None, "未知事件"


class LogParser:
    """多类型日志解析器"""

    # Linux syslog格式
    SYSLOG_PATTERN = re.compile(
        r'([A-Z][a-z]{2}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(.*)'
    )

    # 标准日志格式
    STANDARD_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*(\[?.*?\]?)\s*(\w+)\s*(.*)'
    )

    # Nginx/Apache访问日志
    ACCESS_LOG_PATTERN = re.compile(
        r'([\d.]+)\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)\s+"([^"]*)"\s+"([^"]*)"'
    )

    # Tomcat日志
    TOMCAT_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\.\d+\s+\[([^\]]+)\]\s+(\w+)\s+(.*)'
    )

    def parse_linux_log(self, log_line: str) -> Optional[Dict]:
        """解析Linux日志"""
        # 尝试标准syslog格式
        match = self.SYSLOG_PATTERN.match(log_line[:30] + log_line[30:])
        if match:
            date_str, hostname, message = match.groups()
            try:
                timestamp = datetime.strptime(date_str, '%b %d %H:%M:%S')
                timestamp = timestamp.replace(year=datetime.now().year)
            except:
                try:
                    timestamp = datetime.strptime(date_str.split()[1], '%Y-%m-%d')
                except:
                    timestamp = datetime.now()

            return {
                'timestamp': timestamp,
                'hostname': hostname,
                'message': message,
                'raw': log_line
            }

        # 尝试ISO格式
        if log_line.startswith('202') or log_line.startswith('20'):
            parts = log_line.split(None, 3)
            if len(parts) >= 4:
                try:
                    timestamp = datetime.fromisoformat(parts[0] + ' ' + parts[1][:8])
                    return {
                        'timestamp': timestamp,
                        'hostname': parts[2].rstrip(':'),
                        'message': parts[3] if len(parts) > 3 else '',
                        'raw': log_line
                    }
                except:
                    pass

        return None

    def parse_windows_log(self, log_line: str) -> Optional[Dict]:
        """解析Windows日志"""
        # Windows事件日志格式
        match = re.match(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\w+)\s+EventID=(\d+)\s+(.*)',
            log_line
        )
        if match:
            timestamp_str, level, event_id, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = datetime.now()

            return {
                'timestamp': timestamp,
                'level': level,
                'event_id': int(event_id),
                'message': message,
                'raw': log_line
            }
        return None

    def parse_tomcat_log(self, log_line: str) -> Optional[Dict]:
        """解析Tomcat日志"""
        match = self.TOMCAT_PATTERN.match(log_line)
        if match:
            timestamp_str, thread, level, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = datetime.now()

            return {
                'timestamp': timestamp,
                'thread': thread,
                'level': level,
                'message': message,
                'raw': log_line
            }
        return None

    def parse_nginx_log(self, log_line: str) -> Optional[Dict]:
        """解析Nginx访问日志"""
        match = self.ACCESS_LOG_PATTERN.match(log_line)
        if match:
            ip, datetime_str, request, status, size, referer, user_agent = match.groups()
            try:
                dt = datetime_str.split()[0] + ' ' + datetime_str.split()[1]
                timestamp = datetime.strptime(dt, '%d/%b/%Y:%H:%M:%S %z')
                # 移除时区信息
                timestamp = timestamp.replace(tzinfo=None)
            except:
                timestamp = datetime.now()

            # 解析请求
            method, path, protocol = request.split()

            return {
                'timestamp': timestamp,
                'source_ip': ip,
                'method': method,
                'path': path,
                'status': int(status),
                'user_agent': user_agent,
                'raw': log_line
            }
        return None


class TimelineBuilder:
    """时间线构建器"""

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.order_counter = 0

    def add_event(self, event: SecurityEvent):
        """添加事件到时间线"""
        self.order_counter += 1
        event.timeline_order = self.order_counter
        self.events.append(event)

    def sort_events(self):
        """按时间排序事件"""
        self.events.sort(key=lambda x: (x.timestamp, x.timeline_order))

    def build_from_logs(self, logs: List[str], log_type: str, parser: LogParser):
        """从日志构建时间线"""
        attack_engine = AttackPatternEngine()

        for line_num, log_line in enumerate(logs):
            if not log_line.strip():
                continue

            # 解析日志
            parsed = None
            if log_type == 'linux':
                parsed = parser.parse_linux_log(log_line)
            elif log_type == 'windows':
                parsed = parser.parse_windows_log(log_line)
            elif log_type == 'tomcat':
                parsed = parser.parse_tomcat_log(log_line)
            elif log_type == 'nginx':
                parsed = parser.parse_nginx_log(log_line)

            if not parsed:
                continue

            # 检测攻击模式
            attack_type, threat_level, details = attack_engine.detect(log_line)

            # Windows事件特殊处理
            if log_type == 'windows' and 'event_id' in parsed:
                event_id = parsed['event_id']
                level = parsed.get('level', 'INFO')
                win_attack, win_level, desc = attack_engine.detect_windows_event(event_id, level)
                if win_attack:
                    attack_type = win_attack
                    threat_level = win_level
                    details['description'] = desc

            # 提取源IP
            source_ip = None
            ip_pattern = re.search(r'from\s+([\d.]+)', log_line)
            if ip_pattern:
                source_ip = ip_pattern.group(1)
            elif 'source_ip' in parsed:
                source_ip = parsed['source_ip']

            # 创建安全事件
            event = SecurityEvent(
                timestamp=parsed['timestamp'],
                source_ip=source_ip,
                target=parsed.get('hostname') or parsed.get('path', ''),
                event_type=log_type,
                raw_log=log_line,
                threat_level=threat_level or ThreatLevel.INFO,
                attack_type=attack_type or AttackType.UNKNOWN,
                details={
                    **(parsed or {}),
                    **(details or {})
                }
            )

            self.add_event(event)

        self.sort_events()


class IncidentAnalyzer:
    """事件分析器"""

    def __init__(self):
        self.timeline_builder = TimelineBuilder()
        self.log_parser = LogParser()

    def analyze_linux_logs(self, log_file: str) -> Dict:
        """分析Linux日志"""
        print(f"[*] 分析Linux日志: {log_file}")

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f if line.strip()]

        self.timeline_builder = TimelineBuilder()
        self.timeline_builder.build_from_logs(logs, 'linux', self.log_parser)

        return self._generate_report('Linux', log_file)

    def analyze_windows_logs(self, log_file: str) -> Dict:
        """分析Windows日志"""
        print(f"[*] 分析Windows日志: {log_file}")

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f if line.strip()]

        self.timeline_builder = TimelineBuilder()
        self.timeline_builder.build_from_logs(logs, 'windows', self.log_parser)

        return self._generate_report('Windows', log_file)

    def analyze_tomcat_logs(self, log_file: str) -> Dict:
        """分析Tomcat日志"""
        print(f"[*] 分析Tomcat日志: {log_file}")

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f if line.strip()]

        self.timeline_builder = TimelineBuilder()
        self.timeline_builder.build_from_logs(logs, 'tomcat', self.log_parser)

        return self._generate_report('Tomcat', log_file)

    def analyze_nginx_logs(self, log_file: str) -> Dict:
        """分析Nginx日志"""
        print(f"[*] 分析Nginx日志: {log_file}")

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f if line.strip()]

        self.timeline_builder = TimelineBuilder()
        self.timeline_builder.build_from_logs(logs, 'nginx', self.log_parser)

        return self._generate_report('Nginx', log_file)

    def _generate_report(self, log_type: str, source: str) -> Dict:
        """生成分析报告"""
        events = self.timeline_builder.events

        # 统计
        stats = {
            'total_events': len(events),
            'by_threat_level': defaultdict(int),
            'by_attack_type': defaultdict(int),
            'source_ips': defaultdict(int),
            'critical_events': [],
        }

        for event in events:
            stats['by_threat_level'][event.threat_level.value] += 1
            stats['by_attack_type'][event.attack_type.value] += 1
            if event.source_ip:
                stats['source_ips'][event.source_ip] += 1

            if event.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                stats['critical_events'].append(event)

        # 按威胁等级排序
        stats['critical_events'].sort(key=lambda x: (x.threat_level.value, x.timestamp))

        return {
            'source': source,
            'log_type': log_type,
            'analysis_time': datetime.now().isoformat(),
            'stats': dict(stats),
            'timeline': [
                {
                    'order': e.timeline_order,
                    'timestamp': e.timestamp.isoformat(),
                    'threat': e.threat_level.value,
                    'attack_type': e.attack_type.value,
                    'source_ip': e.source_ip,
                    'raw_log': e.raw_log[:200],
                }
                for e in events
            ],
            'recommendations': self._generate_recommendations(stats),
        }

    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """生成安全建议"""
        recommendations = []

        if stats['by_attack_type'].get('暴力破解', 0) > 10:
            recommendations.append("[高危] 检测到大量暴力破解尝试，建议：1)检查并封锁攻击IP；2)启用双因素认证；3)加强密码策略")

        if stats['by_attack_type'].get('SQL注入', 0) > 0:
            recommendations.append("[高危] 检测到SQL注入攻击，建议：1)检查Web应用防火墙配置；2)审查输入验证；3)更新WAF规则")

        if stats['by_attack_type'].get('Webshell', 0) > 0:
            recommendations.append("[严重] 检测到Webshell特征，建议：1)立即隔离受影响服务器；2)扫描webshell文件；3)检查后门")

        if stats['by_attack_type'].get('权限提升', 0) > 0:
            recommendations.append("[严重] 检测到权限提升行为，建议：1)审查用户权限变更；2)检查sudo使用记录；3)审计账户")

        if stats['by_attack_type'].get('可疑登录', 0) > 5:
            recommendations.append("[中危] 检测到多次可疑登录，建议：1)检查登录地理位置；2)审查异常登录时间；3)强制退出可疑会话")

        if not recommendations:
            recommendations.append("[信息] 未发现严重威胁，建议定期审计日志")

        return recommendations

    def print_summary(self, report: Dict):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("应急响应日志分析报告")
        print("=" * 60)
        print(f"日志类型: {report['log_type']}")
        print(f"分析时间: {report['analysis_time']}")
        print(f"总事件数: {report['stats']['total_events']}")
        print("\n威胁等级分布:")
        for level, count in sorted(report['stats']['by_threat_level'].items(), key=lambda x: x[0], reverse=True):
            print(f"  {level}: {count}")

        print("\n攻击类型分布:")
        for attack, count in sorted(report['stats']['by_attack_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {attack}: {count}")

        print("\n可疑IP Top10:")
        for ip, count in sorted(report['stats']['source_ips'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ip}: {count}次")

        print("\n关键事件:")
        for event in report['stats']['critical_events'][:20]:
            print(f"  [{event.threat_level.value.upper()}] {event.timestamp} - {event.attack_type.value}")
            print(f"    {event.raw_log[:100]}")

        print("\n安全建议:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

    def save_report(self, report: Dict, output_file: str):
        """保存报告到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("应急响应日志溯源分析报告\n")
            f.write("Incident Response Log Forensics Report\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"生成时间: {report['analysis_time']}\n")
            f.write(f"日志类型: {report['log_type']}\n")
            f.write(f"数据来源: {report['source']}\n")
            f.write(f"总事件数: {report['stats']['total_events']}\n\n")

            f.write("-" * 70 + "\n")
            f.write("威胁等级分布\n")
            f.write("-" * 70 + "\n")
            for level, count in sorted(report['stats']['by_threat_level'].items()):
                f.write(f"  {level}: {count}\n")

            f.write("\n-" * 35 + "\n")
            f.write("\n-" * 70 + "\n")
            f.write("攻击类型分布\n")
            f.write("-" * 70 + "\n")
            for attack, count in sorted(report['stats']['by_attack_type'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {attack}: {count}\n")

            f.write("\n-" * 70 + "\n")
            f.write("可疑IP统计\n")
            f.write("-" * 70 + "\n")
            for ip, count in sorted(report['stats']['source_ips'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {ip}: {count}次\n")

            f.write("\n-" * 70 + "\n")
            f.write("安全建议\n")
            f.write("-" * 70 + "\n")
            for rec in report['recommendations']:
                f.write(f"  - {rec}\n")

            f.write("\n-" * 70 + "\n")
            f.write("完整时间线\n")
            f.write("-" * 70 + "\n")
            for item in report['timeline']:
                f.write(f"[{item['timestamp']}] [{item['threat'].upper()}] {item['attack_type']}\n")
                f.write(f"  {item['raw_log']}\n\n")

        print(f"\n[*] 报告已保存到: {output_file}")


def detect_log_type(filepath: str) -> str:
    """自动检测日志类型"""
    filename = Path(filepath).name.lower()

    if 'auth' in filename or 'syslog' in filename or 'secure' in filename or 'messages' in filename:
        return 'linux'
    elif 'windows' in filename or 'system' in filename or 'application' in filename:
        return 'windows'
    elif 'catalina' in filename or 'tomcat' in filename:
        return 'tomcat'
    elif 'access' in filename or 'nginx' in filename or 'apache' in filename:
        return 'nginx'

    # 通过内容检测
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        first_lines = [f.readline() for _ in range(5)]

    for line in first_lines:
        if 'EventID=' in line:
            return 'windows'
        if 'INFO' in line and 'dfs.' in line:
            return 'linux'
        if 'GET /' in line or 'POST /' in line:
            return 'nginx'

    return 'unknown'


def main():
    parser = argparse.ArgumentParser(
        description='应急响应日志溯源分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析Linux认证日志
  python incident_response.py --linux /var/log/auth.log

  # 分析Windows事件日志
  python incident_response.py --windows windows_system_log.txt

  # 分析Tomcat日志
  python incident_response.py --tomcat catalina.log

  # 分析Nginx访问日志
  python incident_response.py --nginx access.log

  # 自动检测并分析
  python incident_response.py --auto logs/

  # 导出JSON格式结果
  python incident_response.py --linux auth.log --output result.json --format json
        """
    )

    parser.add_argument('--linux', type=str, help='Linux日志文件路径')
    parser.add_argument('--windows', type=str, help='Windows日志文件路径')
    parser.add_argument('--tomcat', type=str, help='Tomcat日志文件路径')
    parser.add_argument('--nginx', type=str, help='Nginx/Apache日志文件路径')
    parser.add_argument('--auto', type=str, help='自动检测并分析目录中的所有日志')
    parser.add_argument('--output', type=str, default='incident_report.txt', help='输出报告路径')
    parser.add_argument('--format', type=str, default='txt', choices=['txt', 'json'], help='输出格式')
    parser.add_argument('--deeplog', action='store_true', help='使用DeepLog进行异常检测')
    parser.add_argument('--timeline-only', action='store_true', help='仅输出时间线')

    args = parser.parse_args()

    analyzer = IncidentAnalyzer()
    reports = []

    start_time = time.time()

    if args.linux:
        report = analyzer.analyze_linux_logs(args.linux)
        reports.append(report)

    if args.windows:
        report = analyzer.analyze_windows_logs(args.windows)
        reports.append(report)

    if args.tomcat:
        report = analyzer.analyze_tomcat_logs(args.tomcat)
        reports.append(report)

    if args.nginx:
        report = analyzer.analyze_nginx_logs(args.nginx)
        reports.append(report)

    if args.auto:
        input_dir = Path(args.auto)
        if input_dir.is_file():
            input_dir = input_dir.parent

        log_files = []
        for f in input_dir.rglob('*'):
            if f.is_file() and f.suffix in ['.log', '.txt']:
                log_files.append(f)

        print(f"[*] 发现 {len(log_files)} 个日志文件")

        for log_file in log_files[:20]:  # 限制分析数量
            log_type = detect_log_type(str(log_file))
            if log_type == 'unknown':
                continue

            try:
                if log_type == 'linux':
                    report = analyzer.analyze_linux_logs(str(log_file))
                elif log_type == 'windows':
                    report = analyzer.analyze_windows_logs(str(log_file))
                elif log_type == 'tomcat':
                    report = analyzer.analyze_tomcat_logs(str(log_file))
                elif log_type == 'nginx':
                    report = analyzer.analyze_nginx_logs(str(log_file))
                else:
                    continue

                reports.append(report)
            except Exception as e:
                print(f"[!] 分析 {log_file} 失败: {e}")

    if not reports:
        parser.print_help()
        return 1

    # 输出报告
    if args.format == 'json':
        output_file = args.output if args.output.endswith('.json') else args.output + '.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        print(f"[*] JSON报告已保存到: {output_file}")
    else:
        for report in reports:
            analyzer.print_summary(report)

        output_file = args.output
        for report in reports:
            analyzer.save_report(report, output_file)

    elapsed_time = time.time() - start_time
    print(f"\n[*] 分析完成，耗时: {elapsed_time:.2f}秒")

    return 0


if __name__ == "__main__":
    sys.exit(main())
