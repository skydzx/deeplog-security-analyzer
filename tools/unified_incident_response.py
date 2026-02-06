#!/usr/bin/env python3
"""
统一应急响应日志溯源分析工具 - Unified Incident Response Forensics Tool
整合 DeepLog 日志异常检测 + WebShell 文件检测

功能：
1. 多类型日志解析（Linux/Windows/Tomcat/Nginx/Apache）
2. 基于规则的异常检测（暴力破解、SQL注入、Webshell特征等）
3. DeepLog 深度学习异常检测
4. WebShell 文件深度分析
5. 时间线重建
6. 溯源分析
7. 风险评估报告

使用方法：
python unified_incident_response.py --linux /var/log/auth.log
python unified_incident_response.py --auto /path/to/logs --webshell-dir /path/to/webroot
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from deeplog import DeepLog
    HAS_DEEPLOG = True
except ImportError:
    HAS_DEEPLOG = False

# WebShell检测路径
WEBSHELL_ROOT = Path(r"D:\webshell_detect")
WEBSHELL_MODELS = WEBSHELL_ROOT / "models" / "unified_gbdt_v5"


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
    DISK_FULL = "磁盘空间不足"
    SERVICE_CRASH = "服务崩溃"
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


@dataclass
class WebshellResult:
    """WebShell检测结果"""
    file_path: str
    is_webshell: bool
    confidence: float
    threat_level: ThreatLevel
    details: Dict = field(default_factory=dict)


class AttackPatternEngine:
    """攻击模式检测引擎"""

    PATTERNS = {
        AttackType.BRUTE_FORCE: [
            r'Failed password.*from\s+([\d.]+)',
            r'authentication failure.*ip=([\d.]+)',
            r'Invalid user.*from\s+([\d.]+)',
            r'Connection closed.*auth',
            r'wrong password.*attempt',
            r'EventID=4625',
        ],
        AttackType.SQL_INJECTION: [
            r"('|%).*(or|and).*(=|--)",
            r'union.*select',
            r'select.*from.*where',
            r'exec.*xp_cmdshell',
            r"'\s*OR\s*'1'\s*=\s*'1",
            r'Information_schema',
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
            r'uploader.*php',
            r'eval\(',
            r'system\(',
            r'passthru\(',
            r'assert\(',
            r'\$_(GET|POST|REQUEST)',
            r'base64_decode\(',
            r'gzinflate\(.*base64',
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
        ],
        AttackType.PRIVILEGE_ESCALATION: [
            r'sudo.*(root|admin)',
            r'su\s+(root|admin)',
            r'chmod\s+[47][0-7][0-7][0-7]',
            r'EventID=4672',
        ],
        AttackType.SUSPICIOUS_LOGIN: [
            r'login.*success.*from\s+([\d.]+)',
            r'session opened',
            r'authenticated.*root',
            r'EventID=4624',
        ],
        AttackType.DISK_FULL: [
            r'No space left on device',
            r'cannot remove.*No space left',
            r'ENOSPC',
        ],
        AttackType.SERVICE_CRASH: [
            r'Main process exited',
            r'server reached MaxClients',
            r'Invalid argument.*mutex',
            r'service.*Failed with result',
        ],
    }

    WINDOWS_EVENT_PATTERNS = {
        4624: (ThreatLevel.INFO, AttackType.SUSPICIOUS_LOGIN, "成功登录"),
        4625: (ThreatLevel.MEDIUM, AttackType.BRUTE_FORCE, "登录失败"),
        4648: (ThreatLevel.LOW, AttackType.SUSPICIOUS_LOGIN, "显式凭据登录"),
        4672: (ThreatLevel.HIGH, AttackType.PRIVILEGE_ESCALATION, "管理员登录"),
        4688: (ThreatLevel.INFO, AttackType.UNKNOWN, "新进程创建"),
        4720: (ThreatLevel.HIGH, AttackType.UNAUTHORIZED_ACCESS, "用户账户创建"),
        4740: (ThreatLevel.HIGH, AttackType.BRUTE_FORCE, "账户锁定"),
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

                    threat_level = ThreatLevel.MEDIUM
                    if attack_type in [AttackType.WEBSHELL, AttackType.PRIVILEGE_ESCALATION]:
                        threat_level = ThreatLevel.HIGH
                    elif attack_type in [AttackType.SQL_INJECTION]:
                        threat_level = ThreatLevel.HIGH
                    elif attack_type in [AttackType.BRUTE_FORCE]:
                        threat_level = ThreatLevel.MEDIUM

                    return attack_type, threat_level, details

        return None, None, None

    def detect_windows_event(self, event_id: int, level: str) -> Tuple[Optional[AttackType], Optional[ThreatLevel], str]:
        """检测Windows事件"""
        if event_id in self.WINDOWS_EVENT_PATTERNS:
            base_level, attack_type, desc = self.WINDOWS_EVENT_PATTERNS[event_id]
            if event_id == 4625 and level == "Error":
                base_level = ThreatLevel.HIGH
            return attack_type, base_level, desc
        return None, None, "未知事件"


class WebshellScanner:
    """WebShell扫描器（轻量级集成）"""

    # WebShell特征模式
    WEBSHELL_PATTERNS = {
        'php': [
            (r'eval\s*\(', 0.9, 'eval函数执行'),
            (r'system\s*\(', 0.9, 'system函数执行'),
            (r'shell_exec\s*\(', 0.9, 'shell_exec函数执行'),
            (r'passthru\s*\(', 0.9, 'passthru函数执行'),
            (r'exec\s*\(', 0.85, 'exec函数执行'),
            (r'assert\s*\(', 0.9, 'assert函数执行'),
            (r'preg_replace\s*\([^)]*\/e', 0.95, 'preg_replace /e修饰符'),
            (r'call_user_func\s*\(', 0.85, 'call_user_func函数'),
            (r'\$_(?:GET|POST|REQUEST)\[.*\]\s*\(', 0.8, '请求参数执行'),
            (r'eval\s*\(\s*\$_', 0.9, 'eval执行请求参数'),
            (r'base64_decode\s*\([^)]+\)', 0.7, 'base64解码'),
            (r'gzinflate\s*\(\s*base64_decode', 0.85, 'gzinflate+base64混淆'),
            (r'gzuncompress\s*\(\s*base64_decode', 0.85, 'gzuncompress+base64混淆'),
            (r'\$\$\w+\s*\([^)]*\$_(?:GET|POST|REQUEST)', 0.85, '变量变量执行'),
            (r'create_function\s*\(', 0.85, 'create_function函数'),
            (r'phpinfo\s*\(', 0.7, 'phpinfo信息泄露'),
            (r'\$_FILES\[', 0.75, '文件上传'),
            (r'move_uploaded_file\s*\(', 0.8, '移动上传文件'),
        ],
        'jsp': [
            (r'<%@\s*import', 0.5, 'JSP导入'),
            (r'<%!\s*.*class', 0.7, 'JSP代码块'),
            (r'Runtime\.getRuntime\(\)\.exec', 0.95, 'Runtime命令执行'),
            (r'ProcessBuilder', 0.9, 'ProcessBuilder命令执行'),
            (r'\.getParameter\s*\(', 0.6, '获取请求参数'),
        ],
        'asp': [
            (r'<%@.*language.*vbscript', 0.6, 'VBScript脚本'),
            (r'Execute\s*\(', 0.9, 'Execute执行'),
            (r'Eval\s*\(', 0.85, 'Eval执行'),
            (r'Session\.Add\s*\(', 0.6, 'Session操作'),
            (r'Request\.Form\[', 0.6, '表单请求'),
        ],
    }

    # WebShell工具特征
    WEBSHELL_TOOLS = [
        (r'behinder', 0.9, '冰蝎WebShell'),
        (r'rebeyond', 0.9, '冰蝎WebShell'),
        (r'godzilla', 0.9, '哥斯拉WebShell'),
        (r'antsword', 0.9, '蚁剑WebShell'),
        (r'chopper', 0.85, '菜刀WebShell'),
        (r'caidao', 0.85, '菜刀WebShell'),
    ]

    def __init__(self):
        self.compiled_patterns = {}
        for lang, patterns in self.WEBSHELL_PATTERNS.items():
            self.compiled_patterns[lang] = [(re.compile(p, re.IGNORECASE), w, d) for p, w, d in patterns]

    def scan_file(self, file_path: str) -> WebshellResult:
        """扫描文件是否包含WebShell特征"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return WebshellResult(
                file_path=file_path,
                is_webshell=False,
                confidence=0.0,
                threat_level=ThreatLevel.INFO,
                details={'error': str(e)}
            )

        # 检测语言
        ext = Path(file_path).suffix.lower()
        lang_map = {'.php': 'php', '.jsp': 'jsp', '.asp': 'asp', '.aspx': 'asp'}
        lang = lang_map.get(ext, 'php')

        # 计算威胁分数
        threat_score = 0.0
        matched_patterns = []

        # 检测语言特定模式
        if lang in self.compiled_patterns:
            for pattern, weight, desc in self.compiled_patterns[lang]:
                if pattern.search(content):
                    threat_score = max(threat_score, weight)
                    matched_patterns.append(desc)

        # 检测WebShell工具特征
        for pattern, weight, desc in self.WEBSHELL_TOOLS:
            if re.search(pattern, content, re.IGNORECASE):
                threat_score = max(threat_score, weight)
                matched_patterns.append(desc)

        # 检测混淆代码
        if re.search(r'\$\w+\s*=\s*["\'][A-Za-z0-9+/=]{50,}["\']', content):
            threat_score = max(threat_score, 0.75)
            matched_patterns.append('可疑编码字符串')

        # 确定威胁等级
        if threat_score >= 0.9:
            threat_level = ThreatLevel.CRITICAL
        elif threat_score >= 0.8:
            threat_level = ThreatLevel.HIGH
        elif threat_score >= 0.6:
            threat_level = ThreatLevel.MEDIUM
        elif threat_score >= 0.4:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.INFO

        is_webshell = threat_score >= 0.6

        return WebshellResult(
            file_path=file_path,
            is_webshell=is_webshell,
            confidence=threat_score,
            threat_level=threat_level,
            details={
                'language': lang,
                'matched_patterns': matched_patterns,
                'file_size': len(content),
                'file_hash': hashlib.md5(content.encode()).hexdigest()
            }
        )

    def scan_directory(self, directory: str, extensions: List[str] = None) -> List[WebshellResult]:
        """扫描目录中的所有文件"""
        if extensions is None:
            extensions = ['.php', '.jsp', '.asp', '.aspx', '.txt']

        results = []
        dir_path = Path(directory)

        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                try:
                    result = self.scan_file(str(file_path))
                    results.append(result)
                except Exception as e:
                    print(f"[!] 扫描失败: {file_path} - {e}")

        return results


class LogParser:
    """多类型日志解析器"""

    SYSLOG_PATTERN = re.compile(r'([A-Z][a-z]{2}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(.*)')
    WINDOWS_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\w+)\s+EventID=(\d+)\s+(.*)')
    TOMCAT_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\.\d+\s+\[([^\]]+)\]\s+(\w+)\s+(.*)')
    NGINX_PATTERN = re.compile(r'([\d.]+)\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)')

    def parse_linux_log(self, log_line: str) -> Optional[Dict]:
        """解析Linux日志"""
        match = self.SYSLOG_PATTERN.match(log_line[:30] + log_line[30:])
        if match:
            date_str, hostname, message = match.groups()
            try:
                timestamp = datetime.strptime(date_str, '%b %d %H:%M:%S')
                timestamp = timestamp.replace(year=datetime.now().year)
            except:
                timestamp = datetime.now()
            return {'timestamp': timestamp, 'hostname': hostname, 'message': message, 'raw': log_line}
        return None

    def parse_windows_log(self, log_line: str) -> Optional[Dict]:
        """解析Windows日志"""
        match = self.WINDOWS_PATTERN.match(log_line)
        if match:
            timestamp_str, level, event_id, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = datetime.now()
            return {'timestamp': timestamp, 'level': level, 'event_id': int(event_id), 'message': message, 'raw': log_line}
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
            return {'timestamp': timestamp, 'thread': thread, 'level': level, 'message': message, 'raw': log_line}
        return None

    def parse_nginx_log(self, log_line: str) -> Optional[Dict]:
        """解析Nginx访问日志"""
        match = self.NGINX_PATTERN.match(log_line)
        if match:
            ip, datetime_str, request, status, size = match.groups()
            method, path, protocol = request.split()
            try:
                dt = datetime_str.split()[0] + ' ' + datetime_str.split()[1]
                timestamp = datetime.strptime(dt, '%d/%b/%Y:%H:%M:%S')
                timestamp = timestamp.replace(tzinfo=None)
            except:
                timestamp = datetime.now()
            return {'timestamp': timestamp, 'source_ip': ip, 'method': method, 'path': path, 'status': int(status), 'raw': log_line}
        return None


class TimelineBuilder:
    """时间线构建器"""

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.order_counter = 0

    def add_event(self, event: SecurityEvent):
        self.order_counter += 1
        event.timeline_order = self.order_counter
        self.events.append(event)

    def sort_events(self):
        self.events.sort(key=lambda x: (x.timestamp, x.timeline_order))

    def build_from_logs(self, logs: List[str], log_type: str, parser: LogParser):
        attack_engine = AttackPatternEngine()

        for line_num, log_line in enumerate(logs):
            if not log_line.strip():
                continue

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
                    details = details or {}
                    details['description'] = desc

            # 提取源IP
            source_ip = None
            ip_pattern = re.search(r'from\s+([\d.]+)', log_line)
            if ip_pattern:
                source_ip = ip_pattern.group(1)
            elif 'source_ip' in parsed:
                source_ip = parsed['source_ip']

            event = SecurityEvent(
                timestamp=parsed['timestamp'],
                source_ip=source_ip,
                target=parsed.get('hostname') or parsed.get('path', ''),
                event_type=log_type,
                raw_log=log_line,
                threat_level=threat_level or ThreatLevel.INFO,
                attack_type=attack_type or AttackType.UNKNOWN,
                details={**(parsed or {}), **(details or {})}
            )
            self.add_event(event)

        self.sort_events()


class UnifiedIncidentAnalyzer:
    """统一事件分析器"""

    def __init__(self):
        self.timeline_builder = TimelineBuilder()
        self.log_parser = LogParser()
        self.webshell_scanner = WebshellScanner()
        self.deeplog_model = None

        # 尝试初始化DeepLog
        if HAS_DEEPLOG:
            try:
                self.deeplog_model = DeepLog(
                    window_size=10,
                    top_g=5,
                    lstm_layers=2,
                    lstm_units=64
                )
                print("[+] DeepLog模型初始化成功")
            except Exception as e:
                print(f"[!] DeepLog初始化失败: {e}")

    def analyze(self, log_file: str = None, webshell_dir: str = None,
                train_data: str = None) -> Dict:
        """执行统一分析"""
        report = {
            'analysis_time': datetime.now().isoformat(),
            'sources': [],
            'log_analysis': None,
            'webshell_analysis': None,
            'timeline': [],
            'recommendations': [],
            'executive_summary': {}
        }

        # 1. 日志分析
        if log_file:
            log_type = self._detect_log_type(log_file)
            report['sources'].append({'type': 'log', 'path': log_file, 'log_type': log_type})

            if train_data:
                print(f"[*] 使用DeepLog训练模型: {train_data}")
                try:
                    with open(train_data, 'r', encoding='utf-8', errors='ignore') as f:
                        train_logs = [line.strip() for line in f if line.strip()]
                    self.deeplog_model.train(train_logs, epochs=5, batch_size=32)
                except Exception as e:
                    print(f"[!] 训练失败: {e}")

            log_report = self._analyze_logs(log_file, log_type)
            report['log_analysis'] = log_report
            report['timeline'].extend(log_report.get('timeline', []))

        # 2. WebShell扫描
        if webshell_dir:
            print(f"[*] 扫描WebShell: {webshell_dir}")
            webshell_report = self._scan_webshell(webshell_dir)
            report['webshell_analysis'] = webshell_report
            report['sources'].append({'type': 'webshell_dir', 'path': webshell_dir})

        # 3. 生成执行摘要
        report['executive_summary'] = self._generate_summary(report)

        # 4. 生成建议
        report['recommendations'] = self._generate_recommendations(report)

        return report

    def _detect_log_type(self, filepath: str) -> str:
        """检测日志类型"""
        filename = Path(filepath).name.lower()
        content_hints = []

        # 读取前几行检测内容
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    line_lower = line.lower()
                    if 'sshd' in line_lower or 'sudo' in line_lower or 'dhclient' in line_lower:
                        content_hints.append('linux')
                    if 'mysql' in line_lower or 'httpd' in line_lower:
                        content_hints.append('linux')
                    if 'EventID=' in line_lower:
                        content_hints.append('windows')
                    if 'catalina' in line_lower or 'localhost:' in line_lower:
                        content_hints.append('tomcat')
                    if 'get /' in line_lower or 'post /' in line_lower:
                        content_hints.append('nginx')
        except:
            pass

        # 基于文件名检测
        if 'auth' in filename or 'syslog' in filename or 'secure' in filename or 'messages' in filename:
            return 'linux'
        elif 'windows' in filename or 'system' in filename:
            return 'windows'
        elif 'catalina' in filename or 'tomcat' in filename:
            return 'tomcat'
        elif 'access' in filename or 'nginx' in filename or 'apache' in filename:
            return 'nginx'

        # 基于内容检测
        if 'linux' in content_hints:
            return 'linux'
        if 'tomcat' in content_hints:
            return 'tomcat'
        if 'windows' in content_hints:
            return 'windows'
        if 'nginx' in content_hints:
            return 'nginx'

        # 默认尝试Linux格式
        return 'linux'

    def _analyze_logs(self, log_file: str, log_type: str) -> Dict:
        """分析日志文件"""
        print(f"[*] 分析{log_type}日志: {log_file}")

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f if line.strip()]

        self.timeline_builder = TimelineBuilder()
        self.timeline_builder.build_from_logs(logs, log_type, self.log_parser)
        events = self.timeline_builder.events

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

        return {
            'log_type': log_type,
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
            ]
        }

    def _scan_webshell(self, directory: str) -> Dict:
        """扫描WebShell"""
        results = self.webshell_scanner.scan_directory(directory)

        stats = {
            'total_files': len(results),
            'webshell_count': 0,
            'by_threat_level': defaultdict(int),
            'critical_files': [],
        }

        for result in results:
            stats['by_threat_level'][result.threat_level.value] += 1
            if result.is_webshell:
                stats['webshell_count'] += 1
                if result.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                    stats['critical_files'].append({
                        'path': result.file_path,
                        'confidence': result.confidence,
                        'threat': result.threat_level.value,
                        'details': result.details
                    })

        return {
            'stats': stats,
            'results': [
                {
                    'path': r.file_path,
                    'is_webshell': r.is_webshell,
                    'confidence': r.confidence,
                    'threat': r.threat_level.value,
                    'details': r.details
                }
                for r in results
            ]
        }

    def _generate_summary(self, report: Dict) -> Dict:
        """生成执行摘要"""
        log_stats = report.get('log_analysis', {}).get('stats', {})
        webshell_stats = report.get('webshell_analysis', {}).get('stats', {}) if report.get('webshell_analysis') else {}

        total_critical = 0
        total_high = 0

        if log_stats:
            total_critical += log_stats.get('by_threat_level', {}).get('critical', 0)
            total_high += log_stats.get('by_threat_level', {}).get('high', 0)
        if webshell_stats:
            total_critical += webshell_stats.get('by_threat_level', {}).get('critical', 0)
            total_high += webshell_stats.get('by_threat_level', {}).get('high', 0)

        risk_level = "低"
        if total_critical > 0:
            risk_level = "极高"
        elif total_high > 5:
            risk_level = "高"
        elif total_high > 0:
            risk_level = "中"

        return {
            'risk_level': risk_level,
            'total_critical_events': total_critical,
            'total_high_events': total_high,
            'webshell_detected': webshell_stats.get('webshell_count', 0) > 0,
            'attack_types': list(log_stats.get('by_attack_type', {}).keys())[:5]
        }

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """生成安全建议"""
        recommendations = []
        log_stats = report.get('log_analysis', {}).get('stats', {})
        webshell_stats = report.get('webshell_analysis', {}).get('stats', {}) if report.get('webshell_analysis') else {}

        # 基于日志攻击
        if log_stats.get('by_attack_type', {}).get('暴力破解', 0) > 5:
            recommendations.append("[高危] 检测到大量暴力破解，建议：1)封禁攻击IP；2)启用双因素认证；3)加强密码策略")

        if log_stats.get('by_attack_type', {}).get('SQL注入', 0) > 0:
            recommendations.append("[高危] 检测到SQL注入攻击，建议：1)检查WAF配置；2)审查输入验证；3)更新安全规则")

        if log_stats.get('by_attack_type', {}).get('Webshell', 0) > 0:
            recommendations.append("[严重] 检测到Webshell特征，建议：1)扫描web目录；2)检查文件完整性；3)隔离受影响服务器")

        # 基于WebShell扫描
        if webshell_stats.get('webshell_count', 0) > 0:
            recommendations.append(f"[严重] 发现 {webshell_stats['webshell_count']} 个可疑文件，建议：1)立即隔离；2)取证分析；3)清除后门")

        if webshell_stats.get('by_threat_level', {}).get('critical', 0) > 0:
            recommendations.append("[极高危] 发现高置信度WebShell，可能已被攻陷，建议启动应急响应流程")

        if not recommendations:
            recommendations.append("[信息] 未发现严重威胁，建议定期审计日志和文件")

        return recommendations

    def print_report(self, report: Dict):
        """打印报告"""
        print("\n" + "=" * 70)
        print("         统一应急响应日志溯源分析报告")
        print("=" * 70)
        print(f"分析时间: {report['analysis_time']}")

        summary = report['executive_summary']
        print(f"\n[风险等级: {summary['risk_level']}]")
        print(f"  - 关键事件: {summary['total_critical_events']}")
        print(f"  - 高危事件: {summary['total_high_events']}")
        print(f"  - WebShell检测: {'是' if summary['webshell_detected'] else '否'}")

        # 日志分析
        if report['log_analysis']:
            log_stats = report['log_analysis']['stats']
            print(f"\n[日志分析]")
            print(f"  总事件数: {log_stats['total_events']}")
            print(f"  威胁等级: {dict(log_stats['by_threat_level'])}")
            print(f"  攻击类型: {dict(log_stats['by_attack_type'])}")
            if log_stats.get('source_ips'):
                print(f"  可疑IP: {dict(log_stats['source_ips'])}")

        # WebShell扫描
        if report['webshell_analysis']:
            ws_stats = report['webshell_analysis']['stats']
            print(f"\n[WebShell扫描]")
            print(f"  扫描文件: {ws_stats['total_files']}")
            print(f"  可疑文件: {ws_stats['webshell_count']}")
            if ws_stats.get('critical_files'):
                print(f"  高危文件:")
                for f in ws_stats['critical_files'][:5]:
                    print(f"    - {f['path']} (置信度: {f['confidence']:.2%})")

        # 安全建议
        print(f"\n[安全建议]")
        for rec in report['recommendations']:
            print(f"  - {rec}")

        print("\n" + "=" * 70)

    def save_report(self, report: Dict, output_file: str):
        """保存报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"[*] 报告已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='统一应急响应日志溯源分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析Linux认证日志
  python unified_incident_response.py --linux auth.log

  # 扫描Web目录
  python unified_incident_response.py --webshell-dir /var/www/html

  # 完整分析
  python unified_incident_response.py --linux auth.log --webshell-dir /var/www/html --output report.json

  # 使用DeepLog训练和分析
  python unified_incident_response.py --train normal.log --analyze suspicious.log
        """
    )

    parser.add_argument('--linux', type=str, help='Linux日志文件')
    parser.add_argument('--windows', type=str, help='Windows日志文件')
    parser.add_argument('--tomcat', type=str, help='Tomcat日志文件')
    parser.add_argument('--nginx', type=str, help='Nginx日志文件')
    parser.add_argument('--webshell-dir', type=str, help='WebShell扫描目录')
    parser.add_argument('--train', type=str, help='DeepLog训练数据')
    parser.add_argument('--analyze', type=str, help='DeepLog分析数据')
    parser.add_argument('--output', type=str, default='unified_report.json', help='输出文件')
    parser.add_argument('--format', type=str, default='json', choices=['json', 'txt'], help='输出格式')

    args = parser.parse_args()

    analyzer = UnifiedIncidentAnalyzer()

    start_time = time.time()

    # 执行分析
    report = analyzer.analyze(
        log_file=args.linux or args.windows or args.tomcat or args.nginx,
        webshell_dir=args.webshell_dir,
        train_data=args.train
    )

    # 输出报告
    if args.format == 'json':
        analyzer.save_report(report, args.output)
    else:
        analyzer.print_report(report)
        # 保存文本报告
        txt_output = args.output.replace('.json', '.txt')
        with open(txt_output, 'w', encoding='utf-8') as f:
            f.write("统一应急响应日志溯源分析报告\n")
            f.write("=" * 50 + "\n")
            analyzer.print_report(report, file=f)

    elapsed = time.time() - start_time
    print(f"[*] 分析完成，耗时: {elapsed:.2f}秒")

    return 0


if __name__ == "__main__":
    sys.exit(main())
