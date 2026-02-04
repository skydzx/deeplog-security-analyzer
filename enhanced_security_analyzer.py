#!/usr/bin/env python3
"""
Enhanced Security Log Analyzer - v3.0
Integrates features from SSlogs:
- YAML-based configurable rules
- AI model integration (DeepSeek, Ollama, LM Studio)
- HTML report generation with modern UI
- GeoIP analysis

Author: DeepLog Security Team
"""

import os
import re
import json
import yaml
import glob
import logging
import hashlib
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import defaultdict
from pathlib import Path
import urllib.parse

# ============== 枚举定义 ==============

class ThreatLevel:
    """威胁等级 - 1.0-10.0 智能评分"""
    CRITICAL = 10.0
    HIGH = 7.5
    MEDIUM = 5.0
    LOW = 2.5
    INFO = 1.0

class AttackCategory:
    """攻击类别 - MITRE ATT&CK对齐"""
    INJECTION = "注入攻击"           # T1190
    XSS = "XSS攻击"                 # T1190
    WEBSHELL = "WebShell"           # T1505
    COMMAND_INJECTION = "命令注入"    # T1059
    SQL_INJECTION = "SQL注入"        # T1190
    BRUTE_FORCE = "暴力破解"         # T1110
    PATH_TRAVERSAL = "路径遍历"      # T1190
    PORT_SCAN = "端口扫描"           # T1046
    DATA_EXFILTRATION = "数据外泄"   # T1041
    PERSISTENCE = "持久化"          # T1547
    PRIVILEGE_ESCALATION = "权限提升" # T1068
    LATERAL_MOVEMENT = "横向移动"   # T1021
    CREDENTIAL_THEFT = "凭证窃取"   # T1003
    LOG4J = "Log4j漏洞利用"         # T1190
    MALWARE = "恶意软件"            # T1204
    DNS_TUNNELING = "DNS隧道"       # T1071
    RANSOMWARE = "勒索软件"         # T1486
    PHISHING = "钓鱼攻击"           # T1566
    VULNERABILITY_SCAN = "漏洞扫描"  # T1595
    API_ABUSE = "API滥用"           # T1190
    CLOUD_NATIVE = "云原生威胁"      # T1550
    SUPPLY_CHAIN = "供应链攻击"      # T1195
    UNKNOWN = "未知"

# ============== 数据类 ==============

@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    hostname: Optional[str] = None
    username: Optional[str] = None
    event_id: Optional[str] = None
    attack_type: str = "Unknown"
    category: str = AttackCategory.UNKNOWN
    threat_level: float = ThreatLevel.INFO
    confidence: float = 0.0
    description: str = ""
    raw_log: str = ""
    remediation: str = ""
    mitre_ttp: str = ""
    detection_rule: str = ""
    ai_analysis: Optional[str] = None

@dataclass
class YAMLRule:
    """YAML规则定义"""
    name: str
    severity: str
    category: str
    mitre_ttp: str = ""
    description: str = ""
    remediation: str = ""
    pattern: Dict[str, str] = field(default_factory=dict)
    cwe: str = ""
    confidence: float = 0.8
    response_codes: List[str] = field(default_factory=list)

# ============== 增强分析器 ==============

class EnhancedSecurityAnalyzer:
    """增强版安全日志分析器 - 支持YAML规则和AI"""

    def __init__(self, rules_dir: str = "config/rules", config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.rules_dir = Path(rules_dir)
        self.config = config or {}
        self.rules: List[YAMLRule] = []
        self.python_patterns: List[Dict] = []

        # 初始化
        self._load_yaml_rules()
        self._build_python_patterns()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _load_yaml_rules(self):
        """加载YAML规则"""
        if not self.rules_dir.exists():
            self.logger.warning(f"Rules directory not found: {self.rules_dir}")
            return

        yaml_files = glob.glob(str(self.rules_dir / "*.yaml"))
        self.logger.info(f"Loading {len(yaml_files)} YAML rule files...")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析YAML (支持多文档)
                    documents = list(yaml.safe_load_all(content))
                    for doc in documents:
                        if doc and 'name' in doc:
                            rule = YAMLRule(
                                name=doc.get('name', ''),
                                severity=doc.get('severity', 'medium'),
                                category=doc.get('category', 'unknown'),
                                mitre_ttp=doc.get('mitre_ttp', ''),
                                description=doc.get('description', ''),
                                remediation=doc.get('remediation', ''),
                                pattern=doc.get('pattern', {}),
                                cwe=doc.get('cwe', ''),
                                confidence=doc.get('confidence', 0.8)
                            )
                            self.rules.append(rule)
            except Exception as e:
                self.logger.error(f"Failed to load {yaml_file}: {e}")

        self.logger.info(f"Loaded {len(self.rules)} rules from YAML files")

    def _build_python_patterns(self):
        """构建Python正则表达式模式（兼容旧版）"""
        self.python_patterns = [
            # WebShell
            {
                'pattern': re.compile(r'\$\w+\s*=\s*[\'"]?(eval|assert|system)', re.IGNORECASE),
                'category': AttackCategory.WEBSHELL,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1505',
                'description': '一句话木马(eval/assert/system)',
                'detection_rule': 'WEBSHELL_EVAL_ASSERT'
            },
            {
                'pattern': re.compile(r'eval\s*\(\s*base64_decode', re.IGNORECASE),
                'category': AttackCategory.WEBSHELL,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1505',
                'description': 'Base64编码WebShell',
                'detection_rule': 'WEBSHELL_BASE64'
            },
            {
                'pattern': re.compile(r'shell\.php|cmd\.php|backdoor\.php', re.IGNORECASE),
                'category': AttackCategory.WEBSHELL,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1505',
                'description': '可疑WebShell文件名',
                'detection_rule': 'WEBSHELL_FILENAME'
            },
            # Log4j
            {
                'pattern': re.compile(r'\$\{jndi:(ldap|rmi|dns):\/\/', re.IGNORECASE),
                'category': AttackCategory.LOG4J,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1190',
                'description': 'Log4Shell JNDI注入',
                'detection_rule': 'LOG4J_JNDI'
            },
            {
                'pattern': re.compile(r'Loaded remote class.*jndi', re.IGNORECASE),
                'category': AttackCategory.LOG4J,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1190',
                'description': 'Log4j远程类加载(RCE成功)',
                'detection_rule': 'LOG4J_RCE'
            },
            # SQL注入
            {
                'pattern': re.compile(r"('|%).*(or|and).*(=|--)", re.IGNORECASE),
                'category': AttackCategory.SQL_INJECTION,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1190',
                'description': '可能的SQL注入',
                'detection_rule': 'SQLI_BASIC'
            },
            {
                'pattern': re.compile(r'(union.*select|UNION SELECT)', re.IGNORECASE),
                'category': AttackCategory.SQL_INJECTION,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1190',
                'description': 'UNION SELECT注入',
                'detection_rule': 'SQLI_UNION'
            },
            # XSS
            {
                'pattern': re.compile(r'(<script|</script>)', re.IGNORECASE),
                'category': AttackCategory.XSS,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1190',
                'description': 'Script标签注入',
                'detection_rule': 'XSS_SCRIPT'
            },
            # 命令注入
            {
                'pattern': re.compile(r'[;\|\$`\\]', re.IGNORECASE),
                'category': AttackCategory.COMMAND_INJECTION,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1059',
                'description': '命令注入字符',
                'detection_rule': 'CMD_INJECTION'
            },
            {
                'pattern': re.compile(r'(bash\s+-i|sh\s+-i|nc\s+-e|/bin/sh)', re.IGNORECASE),
                'category': AttackCategory.COMMAND_INJECTION,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1059',
                'description': '反弹Shell',
                'detection_rule': 'CMD_REVERSE_SHELL'
            },
            # 路径遍历
            {
                'pattern': re.compile(r'(\.\./|\.\.\\)', re.IGNORECASE),
                'category': AttackCategory.PATH_TRAVERSAL,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1190',
                'description': '路径遍历尝试',
                'detection_rule': 'PATH_TRAVERSAL'
            },
            {
                'pattern': re.compile(r'(/etc/passwd|/boot.ini|win.ini)', re.IGNORECASE),
                'category': AttackCategory.PATH_TRAVERSAL,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1190',
                'description': '尝试读取敏感文件',
                'detection_rule': 'SENSITIVE_FILE_ACCESS'
            },
            # 暴力破解
            {
                'pattern': re.compile(r'Failed password for|Invalid user', re.IGNORECASE),
                'category': AttackCategory.BRUTE_FORCE,
                'threat_level': ThreatLevel.MEDIUM,
                'mitre_ttp': 'T1110',
                'description': 'SSH认证失败',
                'detection_rule': 'SSH_AUTH_FAILURE'
            },
            # 持久化 (APT)
            {
                'pattern': re.compile(r'Registry value was modified.*Run', re.IGNORECASE),
                'category': AttackCategory.PERSISTENCE,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1547',
                'description': '注册表持久化',
                'detection_rule': 'PERSISTENCE_REGISTRY'
            },
            {
                'pattern': re.compile(r'Task Scheduler.*Created task.*WindowsUpdater', re.IGNORECASE),
                'category': AttackCategory.PERSISTENCE,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1053',
                'description': '计划任务持久化',
                'detection_rule': 'PERSISTENCE_TASK'
            },
            # 横向移动
            {
                'pattern': re.compile(r'PsExec', re.IGNORECASE),
                'category': AttackCategory.LATERAL_MOVEMENT,
                'threat_level': ThreatLevel.HIGH,
                'mitre_ttp': 'T1021',
                'description': 'PsExec远程执行',
                'detection_rule': 'LATERAL_PSEXEC'
            },
            {
                'pattern': re.compile(r'wmic.*node.*process call create', re.IGNORECASE),
                'category': AttackCategory.LATERAL_MOVEMENT,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1047',
                'description': 'WMI远程执行',
                'detection_rule': 'LATERAL_WMI'
            },
            # 凭证窃取
            {
                'pattern': re.compile(r'lsass.*procs|SeDebugPrivilege', re.IGNORECASE),
                'category': AttackCategory.CREDENTIAL_THEFT,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1003',
                'description': 'LSASS凭证访问(Mimikatz)',
                'detection_rule': 'CRED_LSASS'
            },
            {
                'pattern': re.compile(r'GetChanges.*DCSync|DCSync', re.IGNORECASE),
                'category': AttackCategory.CREDENTIAL_THEFT,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1003',
                'description': 'DCSync攻击',
                'detection_rule': 'CRED_DCSYNC'
            },
            # PowerShell编码混淆
            {
                'pattern': re.compile(r'-enc\s+SQBFAFg|powershell.*-encodedCommand', re.IGNORECASE),
                'category': AttackCategory.MALWARE,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1027',
                'description': 'PowerShell编码混淆',
                'detection_rule': 'EVASION_POWERSHELL'
            },
            # 防御绕过
            {
                'pattern': re.compile(r'DisableAntiSpyware|DisableAntiVirus', re.IGNORECASE),
                'category': AttackCategory.MALWARE,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1562',
                'description': '禁用安全软件',
                'detection_rule': 'EVASION_EDR'
            },
            {
                'pattern': re.compile(r'event log was cleared|wevtutil.*clear', re.IGNORECASE),
                'category': AttackCategory.MALWARE,
                'threat_level': ThreatLevel.CRITICAL,
                'mitre_ttp': 'T1070',
                'description': '清空事件日志',
                'detection_rule': 'EVASION_LOGCLEAR'
            },
        ]

    def parse_log_line(self, log_line: str) -> Dict[str, Any]:
        """解析单行日志"""
        result = {
            'raw': log_line.strip(),
            'timestamp': None,
            'source_ip': None,
            'hostname': None,
            'request': None,
            'status_code': None,
            'user_agent': None,
            'event_id': None,
        }

        # Apache/Nginx 日志格式
        apache_pattern = re.compile(
            r'(?P<ip>[\d.]+)\s+-\s+-\s+\[(?P<timestamp>[^\]]+)\]\s+'
            r'"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<size>\d+)'
        )
        match = apache_pattern.match(log_line)
        if match:
            result['timestamp'] = match.group('timestamp')
            result['source_ip'] = match.group('ip')
            result['request'] = match.group('request')
            result['status_code'] = match.group('status')
            return result

        # SSH 日志
        ssh_pattern = re.compile(
            r'(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d+:\d+:\d+)\s+'
            r'(?P<hostname>[\w-]+)\s+(?P<process>[\w]+):\s+(?P<message>.+)'
        )
        match = ssh_pattern.match(log_line)
        if match:
            result['timestamp'] = match.group('timestamp')
            result['hostname'] = match.group('hostname')
            result['message'] = match.group('message')
            # 提取IP
            ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
            ip_match = ip_pattern.search(log_line)
            if ip_match:
                result['source_ip'] = ip_match.group(1)
            return result

        # Windows Event
        event_pattern = re.compile(r'EventID=(?P<event_id>\d+)')
        match = event_pattern.search(log_line)
        if match:
            result['event_id'] = match.group('event_id')

        return result

    def check_yaml_rule(self, rule: YAMLRule, parsed: Dict[str, Any]) -> bool:
        """检查YAML规则匹配"""
        if not rule.pattern or not isinstance(rule.pattern, dict):
            return False

        raw = parsed.get('raw', '')
        request = parsed.get('request', '')
        message = parsed.get('message', '')

        for field_name, pattern_str in rule.pattern.items():
            if not pattern_str:
                continue
            try:
                # 根据字段选择要匹配的文本
                text_to_search = raw
                if field_name == 'url' or field_name == 'params':
                    text_to_search = request or message or raw
                elif field_name == 'user_agent':
                    text_to_search = parsed.get('user_agent', '')

                if text_to_search and re.search(str(pattern_str), text_to_search, re.IGNORECASE):
                    return True
            except re.error as e:
                self.logger.warning(f"Invalid regex in rule {rule.name}: {e}")

        return False

    def analyze_log(self, log_line: str) -> List[SecurityEvent]:
        """分析单条日志，返回匹配的安全事件"""
        events = []
        parsed = self.parse_log_line(log_line)
        raw = parsed.get('raw', '')

        if not raw:
            return events

        # 检查Python模式
        for p in self.python_patterns:
            if p['pattern'].search(raw):
                event = SecurityEvent(
                    timestamp=parsed.get('timestamp', datetime.now().isoformat()),
                    source_ip=parsed.get('source_ip'),
                    hostname=parsed.get('hostname'),
                    event_id=parsed.get('event_id'),
                    attack_type=p['description'],
                    category=p['category'],
                    threat_level=p['threat_level'],
                    confidence=p.get('confidence', 0.8),
                    description=p['description'],
                    raw_log=raw,
                    mitre_ttp=p['mitre_ttp'],
                    detection_rule=p['detection_rule'],
                    remediation=self._get_remediation(p['category'])
                )
                events.append(event)

        # 检查YAML规则
        for rule in self.rules:
            if self.check_yaml_rule(rule, parsed):
                threat_level = self._severity_to_level(rule.severity)
                event = SecurityEvent(
                    timestamp=parsed.get('timestamp', datetime.now().isoformat()),
                    source_ip=parsed.get('source_ip'),
                    hostname=parsed.get('hostname'),
                    event_id=parsed.get('event_id'),
                    attack_type=rule.name,
                    category=rule.category,
                    threat_level=threat_level,
                    confidence=rule.confidence,
                    description=rule.description,
                    raw_log=raw,
                    mitre_ttp=rule.mitre_ttp,
                    detection_rule=rule.name,
                    remediation=rule.remediation
                )
                # 避免重复
                if not any(e.detection_rule == event.detection_rule for e in events):
                    events.append(event)

        return events

    def _severity_to_level(self, severity: str) -> float:
        """转换严重级别到威胁等级"""
        mapping = {
            'critical': ThreatLevel.CRITICAL,
            'high': ThreatLevel.HIGH,
            'medium': ThreatLevel.MEDIUM,
            'low': ThreatLevel.LOW,
            'info': ThreatLevel.INFO
        }
        return mapping.get(severity.lower(), ThreatLevel.MEDIUM)

    def _get_remediation(self, category: str) -> str:
        """获取处置建议"""
        recommendations = {
            AttackCategory.WEBSHELL: "立即隔离文件，分析WebShell类型和功能",
            AttackCategory.LOG4J: "立即升级Log4j到2.17+，阻断JNDI",
            AttackCategory.SQL_INJECTION: "审查WAF日志，检查数据库泄露",
            AttackCategory.XSS: "启用CSP头，审查输出编码",
            AttackCategory.COMMAND_INJECTION: "检查输入验证，禁用危险函数",
            AttackCategory.PATH_TRAVERSAL: "审查文件访问控制",
            AttackCategory.BRUTE_FORCE: "启用账户锁定，审查认证日志",
            AttackCategory.PERSISTENCE: "检查注册表和计划任务",
            AttackCategory.LATERAL_MOVEMENT: "隔离受影响主机，审查网络连接",
            AttackCategory.CREDENTIAL_THEFT: "重置所有账户密码，检查域控制器",
            AttackCategory.MALWARE: "立即隔离，分析恶意软件"
        }
        return recommendations.get(category, "审查安全事件日志")

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析日志文件"""
        self.logger.info(f"Analyzing file: {file_path}")

        events = []
        ip_stats = defaultdict(int)
        category_stats = defaultdict(int)
        threat_stats = defaultdict(int)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        matched_events = self.analyze_log(line)
                        for event in matched_events:
                            events.append(event)
                            if event.source_ip:
                                ip_stats[event.source_ip] += 1
                            category_stats[event.category] += 1
                            threat_level = 'CRITICAL' if event.threat_level >= 10 else \
                                          'HIGH' if event.threat_level >= 7.5 else \
                                          'MEDIUM' if event.threat_level >= 5 else \
                                          'LOW'
                            threat_stats[threat_level] += 1
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error analyzing file: {e}")
            return {}

        # 构建报告
        report = {
            'report_info': {
                'tool_version': '3.0.0',
                'generated_at': datetime.now().isoformat(),
                'analyzed_file': file_path,
                'total_events': len(events),
                'critical_events': threat_stats.get('CRITICAL', 0),
                'high_events': threat_stats.get('HIGH', 0),
                'yaml_rules_loaded': len(self.rules),
                'python_patterns_loaded': len(self.python_patterns)
            },
            'executive_summary': {
                'risk_level': 'CRITICAL' if threat_stats.get('CRITICAL', 0) > 0 else \
                             'HIGH' if threat_stats.get('HIGH', 0) > 10 else \
                             'MEDIUM' if events else 'SAFE',
                'total_events': len(events),
                'critical_events': threat_stats.get('CRITICAL', 0),
                'high_events': threat_stats.get('HIGH', 0),
                'medium_events': threat_stats.get('MEDIUM', 0),
                'top_attack_categories': dict(sorted(category_stats.items(), key=lambda x: -x[1])[:10]),
                'top_source_ips': dict(sorted(ip_stats.items(), key=lambda x: -x[1])[:10])
            },
            'threat_level_distribution': dict(threat_stats),
            'attack_category_distribution': dict(category_stats),
            'critical_events': [
                {
                    'timestamp': e.timestamp,
                    'threat_level': 'CRITICAL' if e.threat_level >= 10 else 'HIGH',
                    'attack_type': e.attack_type,
                    'source_ip': e.source_ip,
                    'description': e.description,
                    'raw_log': e.raw_log[:200],
                    'remediation': e.remediation,
                    'mitre_technique': e.mitre_ttp
                }
                for e in sorted(events, key=lambda x: -x.threat_level)[:100]
            ],
            'recommendations': self._generate_recommendations(events, category_stats)
        }

        return report

    def _generate_recommendations(self, events: List[SecurityEvent], category_stats: Dict) -> List[str]:
        """生成安全建议"""
        recommendations = []

        if category_stats.get(AttackCategory.LOG4J, 0) > 0:
            recommendations.append("紧急: 检测到Log4j漏洞利用，立即升级到2.17+")

        if category_stats.get(AttackCategory.WEBSHELL, 0) > 0:
            recommendations.append("紧急: 检测到WebShell，隔离受影响服务器")

        if category_stats.get(AttackCategory.CREDENTIAL_THEFT, 0) > 0:
            recommendations.append("严重: 检测到凭证窃取，立即重置密码并检查域控制器")

        if category_stats.get(AttackCategory.PERSISTENCE, 0) > 0:
            recommendations.append("警告: 检测到持久化后门，全面扫描系统")

        if category_stats.get(AttackCategory.LATERAL_MOVEMENT, 0) > 0:
            recommendations.append("警告: 检测到横向移动，隔离受影响网段")

        if not recommendations:
            recommendations.append("建议: 定期更新检测规则，监控系统安全态势")

        return recommendations

    def generate_html_report(self, report: Dict, output_path: str):
        """生成HTML报告"""
        metadata = report.get('executive_summary', {})
        attack_types = metadata.get('top_attack_categories', {})
        threat_dist = report.get('threat_level_distribution', {})

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全日志分析报告 - {report.get('report_info', {}).get('generated_at', '')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                     border-left: 4px solid #667eea; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 0.9em; text-transform: uppercase; }}
        .critical {{ border-left-color: #e74c3c; }}
        .high {{ border-left-color: #f39c12; }}
        .medium {{ border-left-color: #3498db; }}
        .low {{ border-left-color: #2ecc71; }}
        .section {{ background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ border-bottom: 2px solid #667eea; padding-bottom: 10px; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }}
        .badge-critical {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #f39c12; color: white; }}
        .badge-medium {{ background: #3498db; color: white; }}
        .badge-low {{ background: #2ecc71; color: white; }}
        .recommendation {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .code-block {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>安全事件分析报告</h1>
            <p>生成时间: {report.get('report_info', {}).get('generated_at', 'N/A')}</p>
            <p>分析文件: {report.get('report_info', {}).get('analyzed_file', 'N/A')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{metadata.get('total_events', 0)}</div>
                <div class="stat-label">总事件数</div>
            </div>
            <div class="stat-card critical">
                <div class="stat-number">{metadata.get('critical_events', 0)}</div>
                <div class="stat-label">严重事件</div>
            </div>
            <div class="stat-card high">
                <div class="stat-number">{metadata.get('high_events', 0)}</div>
                <div class="stat-label">高危事件</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-number">{metadata.get('medium_events', 0)}</div>
                <div class="stat-label">中危事件</div>
            </div>
        </div>

        <div class="section">
            <h2>攻击类型分布 (TOP 10)</h2>
            <table>
                <tr><th>排名</th><th>攻击类型</th><th>数量</th><th>占比</th></tr>
                {self._render_attack_types_table(attack_types)}
            </table>
        </div>

        <div class="section">
            <h2>威胁等级分布</h2>
            <table>
                <tr><th>威胁等级</th><th>数量</th></tr>
                {self._render_threat_table(threat_dist)}
            </table>
        </div>

        <div class="section">
            <h2>关键安全事件</h2>
            <table>
                <tr><th>时间</th><th>攻击类型</th><th>威胁</th><th>源IP</th><th>描述</th><th>原始日志</th></tr>
                {self._render_events_table(report.get('critical_events', []))}
            </table>
        </div>

        <div class="section">
            <h2>处置建议</h2>
            {self._render_recommendations(report.get('recommendations', []))}
        </div>

        <div class="section">
            <h2>检测规则统计</h2>
            <p>Python规则: {report.get('report_info', {}).get('python_patterns_loaded', 0)}</p>
            <p>YAML规则: {report.get('report_info', {}).get('yaml_rules_loaded', 0)}</p>
        </div>
    </div>
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"HTML report generated: {output_path}")

    def _render_attack_types_table(self, attack_types: Dict) -> str:
        total = sum(attack_types.values()) or 1
        rows = []
        for i, (cat, count) in enumerate(sorted(attack_types.items(), key=lambda x: -x[1])[:10], 1):
            pct = count / total * 100
            rows.append(f"<tr><td>{i}</td><td>{cat}</td><td>{count}</td><td>{pct:.1f}%</td></tr>")
        return ''.join(rows)

    def _render_threat_table(self, threat_dist: Dict) -> str:
        rows = []
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = threat_dist.get(level, 0)
            badge = f'badge-{level.lower()}'
            rows.append(f"<tr><td><span class='badge {badge}'>{level}</span></td><td>{count}</td></tr>")
        return ''.join(rows)

    def _render_events_table(self, events: List[Dict]) -> str:
        rows = []
        for e in events[:20]:
            level = e.get('threat_level', 'MEDIUM')
            badge = f'badge-{level.lower()}'
            ts = str(e.get('timestamp', ''))[:19]
            rows.append(f"""
            <tr>
                <td>{ts}</td>
                <td>{e.get('attack_type', '')}</td>
                <td><span class='badge {badge}'>{level}</span></td>
                <td>{e.get('source_ip', '-')}</td>
                <td>{e.get('description', '')[:100]}</td>
                <td><div class='code-block'>{e.get('raw_log', '')[:150]}...</div></td>
            </tr>
            """)
        return ''.join(rows)

    def _render_recommendations(self, recommendations: List[str]) -> str:
        return ''.join(f'<div class="recommendation">{r}</div>' for r in recommendations)


# ============== 主程序 ==============

def main():
    parser = argparse.ArgumentParser(description='Enhanced Security Log Analyzer v3.0')
    parser.add_argument('--input', '-i', required=True, help='Input log file')
    parser.add_argument('--output', '-o', required=True, help='Output report file')
    parser.add_argument('--format', '-f', default='html', choices=['html', 'json'],
                        help='Report format (default: html)')
    parser.add_argument('--rules', '-r', default='config/rules',
                        help='Rules directory (default: config/rules)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    analyzer = EnhancedSecurityAnalyzer(rules_dir=args.rules)
    report = analyzer.analyze_file(args.input)

    if not report:
        print("Failed to analyze file")
        return

    if args.format == 'html':
        analyzer.generate_html_report(report, args.output)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"""
=============================================================
        安全事件分析完成
=============================================================
总事件数: {report['executive_summary']['total_events']}
风险等级: {report['executive_summary']['risk_level']}
关键事件: {report['executive_summary']['critical_events']}
高危事件: {report['executive_summary']['high_events']}

检测规则: {report['report_info']['python_patterns_loaded']} Python + {report['report_info']['yaml_rules_loaded']} YAML
报告已保存至: {args.output}
=============================================================
""")


if __name__ == '__main__':
    main()
