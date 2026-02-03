#!/usr/bin/env python3
"""
============================================================
   安全事件应急响应分析系统 - Production Edition
   Security Incident Response Analysis System
============================================================

   版本: 2.0.0
   作者: Security Team

   支持的数据源:
   - Linux系统日志 (/var/log/*)
   - Windows事件日志
   - Web服务器日志 (Nginx/Apache/Tomcat)
   - 数据库日志 (MySQL/PostgreSQL)
   - 应用程序日志
   - 网络设备日志
   - EDR/XDR告警

   攻击检测:
   - 暴力破解
   - SQL注入/XSS/命令注入
   - WebShell上传
   - 路径遍历
   - 权限提升
   - 横向移动
   - 数据外泄
   - 持久化后门
   - 等等

   使用方法:
   1. 单日志分析:
      python security_incident_analyzer.py --input /var/log/auth.log

   2. 批量日志分析:
      python security_incident_analyzer.py --input /path/to/logs/ --recursive

   3. WebShell扫描:
      python security_incident_analyzer.py --webshell /var/www/html

   4. 完整分析:
      python security_incident_analyzer.py --input auth.log --webshell /var/www/html --output report.json

   5. 实时监控模式:
      python security_incident_analyzer.py --watch --input /var/log/syslog

   6. SIEM格式导入:
      python security_incident_analyzer.py --siem cef --input alert.json
============================================================
"""

import os
import sys
import json
import re
import argparse
import gzip
import glob
import hashlib
import logging
import ipaddress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter, Counter
from enum import Enum
import csv
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('security_analyzer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """威胁等级"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1
    UNKNOWN = 0


class AttackCategory(Enum):
    """攻击类别"""
    BRUTE_FORCE = "暴力破解"
    SQL_INJECTION = "SQL注入"
    XSS = "XSS攻击"
    WEBSHELL = "WebShell"
    PATH_TRAVERSAL = "路径遍历"
    COMMAND_INJECTION = "命令注入"
    FILE_UPLOAD = "文件上传攻击"
    PRIVILEGE_ESCALATION = "权限提升"
    LATERAL_MOVEMENT = "横向移动"
    DATA_EXFILTRATION = "数据外泄"
    PERSISTENCE = "持久化"
    MALWARE = "恶意软件"
    PORT_SCAN = "端口扫描"
    DENIAL_OF_SERVICE = "拒绝服务"
    UNAUTHORIZED_ACCESS = "未授权访问"
    SUSPICIOUS_LOGIN = "可疑登录"
    POLICY_VIOLATION = "策略违规"
    SYSTEM_ERROR = "系统错误"
    UNKNOWN = "未知"


@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    hostname: Optional[str] = None
    username: Optional[str] = None
    event_type: str = ""
    process_name: Optional[str] = None
    command_line: Optional[str] = None
    raw_log: str = ""
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    attack_category: AttackCategory = AttackCategory.UNKNOWN
    attack_id: Optional[str] = None
    confidence: float = 0.0
    mitre_technique: Optional[str] = None
    detection_rule: Optional[str] = None
    description: str = ""
    remediation: str = ""
    timeline_order: int = 0


@dataclass
class AttackPattern:
    """攻击模式定义"""
    pattern: re.Pattern
    attack_category: AttackCategory
    threat_level: ThreatLevel
    mitre_technique: Optional[str] = None
    confidence: float = 1.0
    description: str = ""
    detection_rule: str = ""
    remediation: str = ""


class ProductionSecurityAnalyzer:
    """
    生产级安全事件分析器
    支持多种日志格式和攻击检测
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.events: List[SecurityEvent] = []
        self.attack_patterns = self._build_attack_patterns()
        self.ip_reputation = self._load_ip_reputation()
        self.stats = Counter()

    def _build_attack_patterns(self) -> List[AttackPattern]:
        """构建攻击检测规则"""
        patterns = [
            # ============ 暴力破解 ============
            AttackPattern(
                pattern=re.compile(r'Failed password.*from\s+([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1110',
                description='SSH登录失败',
                detection_rule='SSH_FAILED_LOGIN',
                remediation='检查源IP，封禁攻击者，考虑启用双因素认证'
            ),
            AttackPattern(
                pattern=re.compile(r'authentication failure.*ip=([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1110',
                description='PAM认证失败',
                detection_rule='PAM_AUTH_FAILURE',
                remediation='检查认证日志，审查账户安全'
            ),
            AttackPattern(
                pattern=re.compile(r'Invalid user.*from\s+([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1110',
                description='无效用户登录尝试',
                detection_rule='INVALID_USER_ATTEMPT',
                remediation='可能存在暴力破解，检查用户枚举攻击'
            ),
            AttackPattern(
                pattern=re.compile(r'EventID=4625', re.IGNORECASE),
                attack_category=AttackCategory.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1110',
                description='Windows登录失败',
                detection_rule='WINDOWS_LOGIN_FAILURE',
                remediation='检查Windows安全日志，识别暴力破解模式'
            ),

            # ============ SQL注入 ============
            AttackPattern(
                pattern=re.compile(r"('|%).*(or|and).*(=|--)", re.IGNORECASE),
                attack_category=AttackCategory.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.8,
                description='可能的SQL注入尝试',
                detection_rule='SQLI_BASIC',
                remediation='检查Web应用防火墙日志，审查数据库查询'
            ),
            AttackPattern(
                pattern=re.compile(r'union\s+select', re.IGNORECASE),
                attack_category=AttackCategory.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.9,
                description='UNION SELECT注入',
                detection_rule='SQLI_UNION_SELECT',
                remediation='检测到UNION注入攻击，检查数据库泄露'
            ),
            AttackPattern(
                pattern=re.compile(r'exec\s*\(\s*xp_cmdshell', re.IGNORECASE),
                attack_category=AttackCategory.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                confidence=0.95,
                description='xp_cmdshell命令执行',
                detection_rule='SQLI_XPCMD',
                remediation='严重！攻击者可能获得系统权限，立即隔离服务器'
            ),

            # ============ XSS攻击 ============
            AttackPattern(
                pattern=re.compile(r'<script', re.IGNORECASE),
                attack_category=AttackCategory.XSS,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1190',
                confidence=0.7,
                description='XSS脚本标签',
                detection_rule='XSS_SCRIPT_TAG',
                remediation='检查XSS攻击Payload，审查Web应用输入验证'
            ),
            AttackPattern(
                pattern=re.compile(r'javascript:', re.IGNORECASE),
                attack_category=AttackCategory.XSS,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1190',
                confidence=0.8,
                description='JavaScript协议注入',
                detection_rule='XSS_JAVASCRIPT',
                remediation='检测到JavaScript协议，检查Cookie盗用风险'
            ),

            # ============ WebShell ============
            AttackPattern(
                pattern=re.compile(r'shell\.php', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                confidence=0.85,
                description='WebShell文件访问',
                detection_rule='WEBSHELL_ACCESS',
                remediation='检查文件上传功能，审查上传目录'
            ),
            AttackPattern(
                pattern=re.compile(r'eval\s*\(\s*\$_', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                confidence=0.9,
                description='eval执行用户输入',
                detection_rule='WEBSHELL_EVAL',
                remediation='检测到WebShell，立即隔离并取证'
            ),
            AttackPattern(
                pattern=re.compile(r'system\s*\(\s*\$_', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                confidence=0.9,
                description='system执行用户输入',
                detection_rule='WEBSHELL_SYSTEM',
                remediation='检测到命令注入WebShell，立即响应'
            ),

            # ============ 路径遍历 ============
            AttackPattern(
                pattern=re.compile(r'\.\./', re.IGNORECASE),
                attack_category=AttackCategory.PATH_TRAVERSAL,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1190',
                confidence=0.6,
                description='路径遍历尝试',
                detection_rule='PATH_TRAVERSAL_DOTDOT',
                remediation='检查目录穿越攻击，审查文件读取漏洞'
            ),
            AttackPattern(
                pattern=re.compile(r'etc/passwd', re.IGNORECASE),
                attack_category=AttackCategory.PATH_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.8,
                description='尝试读取/etc/passwd',
                detection_rule='SENSITIVE_FILE_READ',
                remediation='检测到敏感文件读取，检查文件包含漏洞'
            ),

            # ============ 命令注入 ============
            AttackPattern(
                pattern=re.compile(r';\s*(cat|ls|wget|curl|nc|bash|sh)', re.IGNORECASE),
                attack_category=AttackCategory.COMMAND_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1059',
                confidence=0.85,
                description='命令注入尝试',
                detection_rule='CMD_INJECTION',
                remediation='检测到命令注入，检查Web应用安全'
            ),
            AttackPattern(
                pattern=re.compile(r'\|(cat|ls|wget|curl|nc)', re.IGNORECASE),
                attack_category=AttackCategory.COMMAND_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1059',
                confidence=0.85,
                description='管道命令注入',
                detection_rule='PIPE_INJECTION',
                remediation='检查命令注入攻击，检查网络外联'
            ),

            # ============ 权限提升 ============
            AttackPattern(
                pattern=re.compile(r'sudo.*(chmod|chown).*0{1,3}', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1548',
                confidence=0.95,
                description='权限修改尝试',
                detection_rule='SUDO_CHMOD_ROOT',
                remediation='检测到危险sudo使用，检查权限提升攻击'
            ),
            AttackPattern(
                pattern=re.compile(r'EventID=4672', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1548',
                description='Windows特殊权限登录',
                detection_rule='WINDOWS_PRIVILEGE',
                remediation='检查管理员权限分配，审查异常登录'
            ),
            AttackPattern(
                pattern=re.compile(r'su\s+root', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1548',
                description='切换到root用户',
                detection_rule='SU_TO_ROOT',
                remediation='检查su命令使用，审查特权账户访问'
            ),

            # ============ 数据外泄 ============
            AttackPattern(
                pattern=re.compile(r'(exfil|exfiltrate|steal|download).*(sensitive|confidential|secret)', re.IGNORECASE),
                attack_category=AttackCategory.DATA_EXFILTRATION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1041',
                confidence=0.8,
                description='数据外泄关键词',
                detection_rule='DATA_EXFIL_KEYWORD',
                remediation='检测到外泄相关行为，检查数据泄露'
            ),
            AttackPattern(
                pattern=re.compile(r'curl.*(192\.168\.|10\.\d+|172\.1[6-9]|172\.2[0-9]|172\.3[01])', re.IGNORECASE),
                attack_category=AttackCategory.DATA_EXFILTRATION,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1041',
                confidence=0.6,
                description='可疑外联行为',
                detection_rule='CURL_INTERNAL_IP',
                remediation='检查curl外联，识别数据外泄通道'
            ),

            # ============ 持久化 ============
            AttackPattern(
                pattern=re.compile(r'cron.*(python|perl|bash|sh).*-c', re.IGNORECASE),
                attack_category=AttackCategory.PERSISTENCE,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1053',
                confidence=0.7,
                description='可疑定时任务',
                detection_rule='SUSPICIOUS_CRON',
                remediation='检查cron定时任务，识别后门持久化'
            ),
            AttackPattern(
                pattern=re.compile(r'reg.*add.*HKCU.*Run', re.IGNORECASE),
                attack_category=AttackCategory.PERSISTENCE,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1547',
                confidence=0.85,
                description='注册表启动项',
                detection_rule='REG_PERSISTENCE',
                remediation='检查注册表启动项，识别后门'
            ),

            # ============ 横向移动 ============
            AttackPattern(
                pattern=re.compile(r'psexec.*\\\\([\w.-]+)', re.IGNORECASE),
                attack_category=AttackCategory.LATERAL_MOVEMENT,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1021',
                confidence=0.8,
                description='PsExec远程执行',
                detection_rule='PSEXEC_USAGE',
                remediation='检查PsExec使用，识别横向移动'
            ),
            AttackPattern(
                pattern=re.compile(r'wmic.*process.*call.*create', re.IGNORECASE),
                attack_category=AttackCategory.LATERAL_MOVEMENT,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1021',
                confidence=0.75,
                description='WMI远程进程创建',
                detection_rule='WMI_LATERAL',
                remediation='检查WMI使用，识别横向移动攻击'
            ),
            AttackPattern(
                pattern=re.compile(r'rdp.*(192\.168\.|10\.\d+|172\.1[6-9]|172\.2[0-9]|172\.3[01])', re.IGNORECASE),
                attack_category=AttackCategory.LATERAL_MOVEMENT,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1021',
                confidence=0.6,
                description='RDP远程连接',
                detection_rule='RDP_CONNECTION',
                remediation='检查RDP连接，识别横向移动'
            ),

            # ============ 可疑登录 ============
            AttackPattern(
                pattern=re.compile(r'login.*success.*from\s+([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.SUSPICIOUS_LOGIN,
                threat_level=ThreatLevel.INFO,
                mitre_technique='T1078',
                description='成功登录',
                detection_rule='SUCCESSFUL_LOGIN',
                remediation='记录正常登录行为'
            ),
            AttackPattern(
                pattern=re.compile(r'EventID=4624.*(Success)', re.IGNORECASE),
                attack_category=AttackCategory.SUSPICIOUS_LOGIN,
                threat_level=ThreatLevel.INFO,
                mitre_technique='T1078',
                description='Windows登录成功',
                detection_rule='WINDOWS_LOGIN_SUCCESS',
                remediation='记录正常Windows登录'
            ),

            # ============ 端口扫描 ============
            AttackPattern(
                pattern=re.compile(r'Connect.*port\s+\d+', re.IGNORECASE),
                attack_category=AttackCategory.PORT_SCAN,
                threat_level=ThreatLevel.LOW,
                mitre_technique='T1046',
                description='端口连接尝试',
                detection_rule='PORT_CONNECT',
                remediation='可能存在端口扫描，检查网络流量'
            ),

            # ============ 服务异常 ============
            AttackPattern(
                pattern=re.compile(r'service.*failed|main process exited', re.IGNORECASE),
                attack_category=AttackCategory.SYSTEM_ERROR,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1496',
                description='服务失败',
                detection_rule='SERVICE_FAILURE',
                remediation='检查服务状态，识别DoS攻击或配置问题'
            ),
            AttackPattern(
                pattern=re.compile(r'No space left on device', re.IGNORECASE),
                attack_category=AttackCategory.SYSTEM_ERROR,
                threat_level=ThreatLevel.MEDIUM,
                description='磁盘空间不足',
                detection_rule='DISK_FULL',
                remediation='检查磁盘使用，清理临时文件或扩展存储'
            ),
        ]
        return patterns

    def _load_ip_reputation(self) -> Dict:
        """加载IP信誉库（模拟）"""
        return {
            'private_ranges': [
                '10.0.0.0/8',
                '172.16.0.0/12',
                '192.168.0.0/16',
                '127.0.0.0/8',
            ],
            'known_malicious': [
                # 示例恶意IP，实际使用时需要更新
            ]
        }

    def is_private_ip(self, ip: str) -> bool:
        """检查是否为私有IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False

    def extract_ip(self, log: str) -> Optional[str]:
        """从日志中提取IP地址"""
        patterns = [
            r'from\s+([\d.]+)',
            r'src=([\d.]+)',
            r'SRC=([\d.]+)',
            r'Source:\s*([\d.]+)',
            r'([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})',
        ]
        for pattern in patterns:
            match = re.search(pattern, log)
            if match:
                ip = match.group(1)
                if re.match(r'^[\d.]+$', ip):
                    return ip
        return None

    def analyze_log_line(self, log_line: str, timestamp: Optional[datetime] = None) -> Optional[SecurityEvent]:
        """分析单条日志"""
        if not log_line or log_line.startswith('#'):
            return None

        # 解析时间戳
        if timestamp is None:
            timestamp = self._parse_timestamp(log_line)

        # 提取源IP
        source_ip = self.extract_ip(log_line)

        # 检测攻击模式
        event = None
        for attack_pattern in self.attack_patterns:
            if attack_pattern.pattern.search(log_line):
                event = SecurityEvent(
                    timestamp=timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                    source_ip=source_ip,
                    raw_log=log_line,
                    threat_level=attack_pattern.threat_level,
                    attack_category=attack_pattern.attack_category,
                    mitre_technique=attack_pattern.mitre_technique,
                    confidence=attack_pattern.confidence,
                    detection_rule=attack_pattern.detection_rule,
                    description=attack_pattern.description,
                    remediation=attack_pattern.remediation
                )
                break

        return event

    def _parse_timestamp(self, log_line: str) -> datetime:
        """解析日志时间戳"""
        timestamp_patterns = [
            (r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', '%Y-%m-%dT%H:%M:%S'),
            (r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
            (r'([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
            (r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})', '%d/%b/%Y:%H:%M:%S'),
        ]

        for pattern, fmt in timestamp_patterns:
            match = re.search(pattern, log_line)
            if match:
                try:
                    ts = datetime.strptime(match.group(1), fmt)
                    # 如果年份是1900，设置为当前年份
                    if ts.year == 1900:
                        ts = ts.replace(year=datetime.now().year)
                    return ts
                except ValueError:
                    continue

        return datetime.now()

    def analyze_file(self, filepath: str) -> List[SecurityEvent]:
        """分析单个日志文件"""
        logger.info(f"分析文件: {filepath}")
        events = []

        try:
            # 检查是否为 gzip 文件
            if filepath.endswith('.gz'):
                open_func = gzip.open
            else:
                open_func = open

            with open_func(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    event = self.analyze_log_line(line.strip())
                    if event:
                        event.timeline_order = line_num
                        events.append(event)
                        self.stats[event.attack_category.value] += 1

        except Exception as e:
            logger.error(f"分析文件失败 {filepath}: {e}")

        logger.info(f"从 {filepath} 检测到 {len(events)} 个安全事件")
        return events

    def analyze_directory(self, directory: str, recursive: bool = True,
                          extensions: List[str] = None) -> List[SecurityEvent]:
        """分析目录中的所有日志文件"""
        if extensions is None:
            extensions = ['.log', '.txt', '.csv']

        all_events = []
        pattern = '**/*' if recursive else '*'

        for ext in extensions:
            for filepath in Path(directory).rglob(f'{pattern}{ext}'):
                if filepath.is_file():
                    events = self.analyze_file(str(filepath))
                    all_events.extend(events)

        return all_events

    def scan_webshell(self, directory: str, extensions: List[str] = None) -> List[Dict]:
        """扫描Web目录查找WebShell"""
        if extensions is None:
            extensions = ['.php', '.jsp', '.asp', '.aspx', '.txt']

        webshell_patterns = [
            (re.compile(r'eval\s*\(\s*\$_', re.IGNORECASE), 'eval($_REQUEST', 0.9),
            (re.compile(r'system\s*\(\s*\$_', re.IGNORECASE), 'system($_REQUEST', 0.9),
            (re.compile(r'shell_exec\s*\(\s*\$_', re.IGNORECASE), 'shell_exec($_REQUEST', 0.85),
            (re.compile(r'passthru\s*\(\s*\$_', re.IGNORECASE), 'passthru($_REQUEST', 0.85),
            (re.compile(r'exec\s*\(\s*\$_', re.IGNORECASE), 'exec($_REQUEST', 0.85),
            (re.compile(r'assert\s*\(\s*\$_', re.IGNORECASE), 'assert($_REQUEST', 0.9),
            (re.compile(r'base64_decode\s*\(\s*\$', re.IGNORECASE), 'base64_decode($_', 0.7),
            (re.compile(r'gzinflate\s*\(\s*base64_decode', re.IGNORECASE), 'gzinflate+base64', 0.8),
            (re.compile(r'\$\w+\s*=\s*["\'][A-Za-z0-9+/=]{50,}["\']', re.IGNORECASE), '可疑编码字符串', 0.7),
            (re.compile(r'cmd\.php|shell\.php|hack\.php', re.IGNORECASE), '可疑文件名', 0.8),
        ]

        webshell_files = []

        for ext in extensions:
            for filepath in Path(directory).rglob(f'*{ext}'):
                if filepath.is_file():
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for pattern, name, confidence in webshell_patterns:
                            if pattern.search(content):
                                file_hash = hashlib.md5(content.encode()).hexdigest()
                                webshell_files.append({
                                    'file_path': str(filepath),
                                    'pattern': name,
                                    'confidence': confidence,
                                    'file_size': len(content),
                                    'file_hash': file_hash,
                                    'threat_level': 'HIGH' if confidence >= 0.8 else 'MEDIUM'
                                })
                                logger.warning(f"发现可疑文件: {filepath} - {name}")
                                break
                    except Exception as e:
                        logger.error(f"扫描文件失败 {filepath}: {e}")

        return webshell_files

    def generate_report(self, events: List[SecurityEvent],
                       webshell_results: List[Dict] = None,
                       output_format: str = 'json') -> Dict:
        """生成分析报告"""
        # 按时间排序
        sorted_events = sorted(events, key=lambda x: (x.timestamp, x.timeline_order))

        # 统计摘要
        threat_stats = defaultdict(int)
        category_stats = defaultdict(int)
        source_ips = Counter()
        critical_events = []

        for event in sorted_events:
            threat_stats[event.threat_level.name] += 1
            category_stats[event.attack_category.value] += 1
            if event.source_ip:
                source_ips[event.source_ip] += 1
            if event.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                critical_events.append(event)

        report = {
            'report_info': {
                'tool_version': '2.0.0',
                'generated_at': datetime.now().isoformat(),
                'total_events': len(sorted_events),
                'critical_events': len(critical_events),
            },
            'executive_summary': {
                'risk_level': self._calculate_risk_level(threat_stats),
                'total_events': len(sorted_events),
                'critical_events': len(critical_events),
                'high_events': threat_stats.get('HIGH', 0),
                'medium_events': threat_stats.get('MEDIUM', 0),
                'top_attack_categories': dict(Counter(category_stats).most_common(10)),
                'top_source_ips': dict(source_ips.most_common(10)),
            },
            'threat_level_distribution': dict(threat_stats),
            'attack_category_distribution': dict(category_stats),
            'critical_events': [
                {
                    'timestamp': e.timestamp,
                    'threat_level': e.threat_level.name,
                    'attack_type': e.attack_category.value,
                    'source_ip': e.source_ip,
                    'description': e.description,
                    'raw_log': e.raw_log[:200],
                    'remediation': e.remediation
                }
                for e in critical_events[:50]
            ],
            'timeline': [
                {
                    'order': e.timeline_order,
                    'timestamp': e.timestamp,
                    'threat': e.threat_level.name,
                    'attack_type': e.attack_category.value,
                    'source_ip': e.source_ip,
                    'raw_log': e.raw_log[:150]
                }
                for e in sorted_events
            ],
            'web_shell_scan': {
                'total_suspect_files': len(webshell_results) if webshell_results else 0,
                'high_confidence': len([w for w in (webshell_results or []) if w['confidence'] >= 0.8]),
                'suspect_files': webshell_results[:20] if webshell_results else []
            },
            'recommendations': self._generate_recommendations(threat_stats, category_stats, webshell_results),
        }

        return report

    def _calculate_risk_level(self, threat_stats: Dict) -> str:
        """计算风险等级"""
        critical = threat_stats.get('CRITICAL', 0)
        high = threat_stats.get('HIGH', 0)
        medium = threat_stats.get('MEDIUM', 0)

        if critical > 0:
            return 'CRITICAL'
        elif high > 5:
            return 'HIGH'
        elif high > 0 or medium > 10:
            return 'MEDIUM'
        elif medium > 0:
            return 'LOW'
        else:
            return 'INFO'

    def _generate_recommendations(self, threat_stats: Dict,
                                 category_stats: Dict,
                                 webshell_results: List[Dict] = None) -> List[Dict]:
        """生成安全建议"""
        recommendations = []

        # 暴力破解建议
        if category_stats.get('暴力破解', 0) > 5:
            recommendations.append({
                'severity': 'HIGH',
                'category': '暴力破解',
                'finding': f'检测到{category_stats["暴力破解"]}次暴力破解尝试',
                'recommendation': '1. 封禁攻击源IP\n2. 启用账户锁定策略\n3. 启用双因素认证\n4. 审查失败的登录日志'
            })

        # SQL注入建议
        if category_stats.get('SQL注入', 0) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': 'SQL注入',
                'finding': f'检测到{category_stats["SQL注入"]}次SQL注入尝试',
                'recommendation': '1. 立即审查Web应用防火墙配置\n2. 检查数据库审计日志\n3. 审查输入验证和参数化查询\n4. 考虑临时阻断受影响IP'
            })

        # WebShell建议
        if webshell_results and len(webshell_results) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': 'WebShell',
                'finding': f'发现{len(webshell_results)}个可疑文件',
                'recommendation': '1. 立即隔离受影响服务器\n2. 取证分析可疑文件\n3. 检查文件上传功能\n4. 审查Web目录完整性'
            })

        # 权限提升建议
        if category_stats.get('权限提升', 0) > 0:
            recommendations.append({
                'severity': 'HIGH',
                'category': '权限提升',
                'finding': f'检测到{category_stats["权限提升"]}次权限提升行为',
                'recommendation': '1. 审查sudo使用记录\n2. 检查账户权限配置\n3. 审查本地管理员组\n4. 启用特权访问管理'
            })

        # 横向移动建议
        if category_stats.get('横向移动', 0) > 0:
            recommendations.append({
                'severity': 'HIGH',
                'category': '横向移动',
                'finding': f'检测到{category_stats["横向移动"]}次横向移动行为',
                'recommendation': '1. 审查RDP和SMB连接\n2. 检查服务账户使用\n3. 启用网络分段\n4. 部署EDR解决方案'
            })

        # 默认建议
        if not recommendations:
            recommendations.append({
                'severity': 'INFO',
                'category': '总体',
                'finding': '未发现高危威胁',
                'recommendation': '继续监控，定期审计日志，确保安全策略有效'
            })

        return recommendations

    def save_report(self, report: Dict, output_path: str, format: str = 'json'):
        """保存报告"""
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        elif format == 'txt':
            self._save_text_report(report, output_path)

    def _save_text_report(self, report: Dict, output_path: str):
        """保存文本格式报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("        安全事件应急响应分析报告\n")
            f.write("        Security Incident Response Report\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"报告时间: {report['report_info']['generated_at']}\n")
            f.write(f"工具版本: {report['report_info']['tool_version']}\n")
            f.write(f"总事件数: {report['report_info']['total_events']}\n")
            f.write(f"风险等级: {report['executive_summary']['risk_level']}\n\n")

            f.write("-" * 70 + "\n")
            f.write("执行摘要\n")
            f.write("-" * 70 + "\n")
            f.write(f"  风险等级: {report['executive_summary']['risk_level']}\n")
            f.write(f"  关键事件: {report['executive_summary']['critical_events']}\n")
            f.write(f"  高危事件: {report['executive_summary']['high_events']}\n")
            f.write(f"  中危事件: {report['executive_summary']['medium_events']}\n\n")

            f.write("-" * 70 + "\n")
            f.write("威胁等级分布\n")
            f.write("-" * 70 + "\n")
            for level, count in report['threat_level_distribution'].items():
                f.write(f"  {level}: {count}\n")
            f.write("\n")

            f.write("-" * 70 + "\n")
            f.write("攻击类型分布\n")
            f.write("-" * 70 + "\n")
            for attack, count in report['attack_category_distribution'].items():
                f.write(f"  {attack}: {count}\n")
            f.write("\n")

            if report['critical_events']:
                f.write("-" * 70 + "\n")
                f.write("关键事件详情\n")
                f.write("-" * 70 + "\n")
                for event in report['critical_events'][:20]:
                    f.write(f"\n[{event['timestamp']}] [{event['threat_level']}] {event['attack_type']}\n")
                    f.write(f"  源IP: {event['source_ip']}\n")
                    f.write(f"  描述: {event['description']}\n")
                    f.write(f"  建议: {event['remediation']}\n")

            f.write("\n" + "-" * 70 + "\n")
            f.write("安全建议\n")
            f.write("-" * 70 + "\n")
            for rec in report['recommendations']:
                f.write(f"\n[{rec['severity']}] {rec['category']}\n")
                f.write(f"  发现: {rec['finding']}\n")
                f.write(f"  建议: {rec['recommendation']}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("报告结束\n")
            f.write("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='安全事件应急响应分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单个日志文件
  python security_incident_analyzer.py --input /var/log/auth.log

  # 递归分析日志目录
  python security_incident_analyzer.py --input /var/log/ --recursive

  # 扫描WebShell
  python security_incident_analyzer.py --webshell /var/www/html

  # 完整分析（日志+WebShell）
  python security_incident_analyzer.py --input auth.log --webshell /var/www/html -o report.json

  # 保存文本报告
  python security_incident_analyzer.py --input auth.log --output report.txt --format txt
        """
    )

    parser.add_argument('--input', '-i', type=str, help='输入日志文件或目录')
    parser.add_argument('--recursive', '-r', action='store_true', help='递归扫描目录')
    parser.add_argument('--webshell', '-w', type=str, help='WebShell扫描目录')
    parser.add_argument('--output', '-o', type=str, default='security_report.json', help='输出报告路径')
    parser.add_argument('--format', '-f', type=str, choices=['json', 'txt'], default='json', help='输出格式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 初始化分析器
    analyzer = ProductionSecurityAnalyzer()
    all_events = []
    webshell_results = []

    # 分析日志
    if args.input:
        path = Path(args.input)
        if path.is_file():
            events = analyzer.analyze_file(str(path))
            all_events.extend(events)
        elif path.is_dir():
            events = analyzer.analyze_directory(str(path), recursive=args.recursive)
            all_events.extend(events)

    # 扫描WebShell
    if args.webshell:
        webshell_results = analyzer.scan_webshell(args.webshell)

    # 生成报告
    report = analyzer.generate_report(all_events, webshell_results)

    # 保存报告
    output_path = args.output
    if not output_path.endswith(('.json', '.txt')):
        output_path += '.json' if args.format == 'json' else '.txt'

    analyzer.save_report(report, output_path, args.format)

    # 打印摘要
    print("\n" + "=" * 60)
    print("        安全事件分析完成")
    print("=" * 60)
    print(f"总事件数: {report['report_info']['total_events']}")
    print(f"风险等级: {report['executive_summary']['risk_level']}")
    print(f"关键事件: {report['report_info']['critical_events']}")
    print(f"WebShell扫描: {report['web_shell_scan']['total_suspect_files']} 个可疑文件")
    print(f"\n报告已保存至: {output_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
