#!/usr/bin/env python3
"""
安全事件分析器 - 集成DeepLog和扩展攻击模式库
Production Security Incident Analyzer with DeepLog Integration

功能:
- 50+ MITRE ATT&CK对齐的攻击检测模式
- DeepLog LSTM异常检测
- WebShell扫描
- 多格式日志解析
- 攻击链关联分析
"""

import re
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from pathlib import Path
import argparse

# DeepLog imports
try:
    from deeplog import DeepLog
    from deeplog.exceptions import DeepLogError
    DEEPLOG_AVAILABLE = True
except ImportError:
    DEEPLOG_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== 枚举定义 ==============

class ThreatLevel:
    """威胁等级"""
    CRITICAL = "CRITICAL"  # 立即响应
    HIGH = "HIGH"          # 紧急处理
    MEDIUM = "MEDIUM"      # 正常工作时间内处理
    LOW = "LOW"            # 低优先级
    INFO = "INFO"          # 信息性
    SAFE = "SAFE"          # 安全
    UNKNOWN = "UNKNOWN"    # 未知


class AttackCategory:
    """攻击类别 - MITRE ATT&CK对齐"""
    BRUTE_FORCE = "暴力破解"           # T1110
    SQL_INJECTION = "SQL注入"          # T1190
    XSS = "XSS攻击"                    # T1190
    PATH_TRAVERSAL = "路径遍历"        # T1190
    WEBSHELL = "WebShell"              # T1505
    COMMAND_INJECTION = "命令注入"     # T1059
    FILE_UPLOAD = "文件上传攻击"       # T1567
    PRIVILEGE_ESCALATION = "权限提升"  # T1068
    LATERAL_MOVEMENT = "横向移动"      # T1021
    DATA_EXFILTRATION = "数据外泄"     # T1041
    PERSISTENCE = "持久化"             # T1547
    MALWARE = "恶意软件"               # T1204
    PORT_SCAN = "端口扫描"             # T1046
    DENIAL_OF_SERVICE = "拒绝服务"     # T1498
    UNAUTHORIZED_ACCESS = "未授权访问"  # T1078
    SUSPICIOUS_LOGIN = "可疑登录"      # T1078
    POLICY_VIOLATION = "策略违规"      # T1484
    SYSTEM_ERROR = "系统错误"          # --
    DNS_TUNNELING = "DNS隧道"          # T1071
    RANSOMWARE = "勒索软件"            # T1486
    PHISHING = "钓鱼攻击"              # T1566
    VULNERABILITY_SCAN = "漏洞扫描"    # T1595
    CREDENTIAL_THEFT = "凭证窃取"      # T1110
    BACKDOOR = "后门"                  # T1053
    INFORMATION_DISCLOSURE = "信息泄露" # T1082
    CODE_EXECUTION = "代码执行"        # T1203
    BINARY_PAYLOAD = "二进制载荷"       # T1204
    ENCODED_PAYLOAD = "编码载荷"       # T1027
    SUSPICIOUS_PROCESS = "可疑进程"    # T1057
    NETWORK_ABUSE = "网络滥用"         # T1090
    CRYPTO_MINING = "挖矿活动"         # T1496
    LOG4J = "Log4j漏洞利用"            # T1190 CVE-2021-44228
    UNKNOWN = "未知"


# ============== 数据类定义 ==============

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
    threat_level: str = ThreatLevel.UNKNOWN
    attack_category: str = AttackCategory.UNKNOWN
    attack_id: Optional[str] = None
    confidence: float = 0.0
    mitre_technique: Optional[str] = None
    detection_rule: Optional[str] = None
    description: str = ""
    remediation: str = ""
    timeline_order: int = 0
    # DeepLog相关
    deeplog_score: Optional[float] = None
    is_anomaly: bool = False


@dataclass
class AttackPattern:
    """攻击模式定义"""
    pattern: re.Pattern
    attack_category: str
    threat_level: str
    mitre_technique: Optional[str] = None
    confidence: float = 1.0
    description: str = ""
    detection_rule: str = ""
    remediation: str = ""
    # 攻击链关联
    chain_id: Optional[str] = None
    chain_stage: Optional[str] = None


@dataclass
class AttackChain:
    """攻击链"""
    chain_id: str
    stages: List[Dict] = field(default_factory=list)
    source_ips: Set[str] = field(default_factory=set)
    target_hosts: Set[str] = field(default_factory=set)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    threat_level: str = ThreatLevel.MEDIUM
    description: str = ""


# ============== 增强分析器 ==============

class EnhancedSecurityAnalyzer:
    """
    增强安全事件分析器
    集成DeepLog和扩展攻击模式库
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.events: List[SecurityEvent] = []
        self.attack_patterns = self._build_attack_patterns()
        self.ip_reputation = self._load_ip_reputation()
        self.attack_chains: List[AttackChain] = []
        self.stats = Counter()

        # DeepLog集成
        self.deeplog_model = None
        self.deeplog_trained = False
        if DEEPLOG_AVAILABLE and self.config.get('use_deeplog', True):
            self._init_deeplog()

    def _init_deeplog(self):
        """初始化DeepLog模型"""
        try:
            self.deeplog_model = DeepLog(
                window_size=self.config.get('deeplog_window', 10),
                top_g=self.config.get('deeplog_top_g', 5),
                lstm_layers=self.config.get('deeplog_layers', 2),
                lstm_units=self.config.get('deeplog_units', 64)
            )
            logger.info("DeepLog模型初始化成功")
        except Exception as e:
            logger.warning(f"DeepLog初始化失败: {e}")
            self.deeplog_model = None

    def _build_attack_patterns(self) -> List[AttackPattern]:
        """构建扩展的攻击检测规则 - 50+规则"""
        patterns = []

        # ============== 暴力破解 (T1110) ==============
        patterns.extend([
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
            AttackPattern(
                pattern=re.compile(r'Connection closed by.*port\s*\d+\s*\[preauth\]', re.IGNORECASE),
                attack_category=AttackCategory.PORT_SCAN,
                threat_level=ThreatLevel.LOW,
                mitre_technique='T1110',
                description='SSH预认证连接关闭',
                detection_rule='SSH_PREAUTH_DISCONNECT',
                remediation='可能是暴力破解的前奏'
            ),
        ])

        # ============== SQL注入 (T1190) ==============
        patterns.extend([
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
            AttackPattern(
                pattern=re.compile(r'drop\s+table', re.IGNORECASE),
                attack_category=AttackCategory.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                confidence=0.95,
                description='DROP TABLE攻击',
                detection_rule='SQLI_DROP_TABLE',
                remediation='检测到数据库破坏攻击，立即检查数据库完整性'
            ),
            AttackPattern(
                pattern=re.compile(r'load_file\s*\(', re.IGNORECASE),
                attack_category=AttackCategory.INFORMATION_DISCLOSURE,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1082',
                description='LOAD_FILE尝试读取文件',
                detection_rule='SQLI_LOAD_FILE',
                remediation='检测到文件读取尝试，可能泄露敏感信息'
            ),
            AttackPattern(
                pattern=re.compile(r'into\s+outfile', re.IGNORECASE),
                attack_category=AttackCategory.FILE_UPLOAD,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1567',
                description='INTO OUTFILE尝试写文件',
                detection_rule='SQLI_OUTFILE',
                remediation='检测到文件写入尝试，可能存在WebShell'
            ),
        ])

        # ============== XSS攻击 (T1190) ==============
        patterns.extend([
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
                pattern=re.compile(r'onerror\s*=', re.IGNORECASE),
                attack_category=AttackCategory.XSS,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1190',
                confidence=0.8,
                description='XSS onerror事件',
                detection_rule='XSS_ONERROR',
                remediation='检测到事件处理器XSS，检查输入过滤'
            ),
            AttackPattern(
                pattern=re.compile(r'javascript\s*:', re.IGNORECASE),
                attack_category=AttackCategory.XSS,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1190',
                confidence=0.7,
                description='JavaScript协议尝试',
                detection_rule='XSS_JAVASCRIPT',
                remediation='检测到javascript协议，检查输出编码'
            ),
        ])

        # ============== 路径遍历 (T1190) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'\.\.(\/|\\)', re.IGNORECASE),
                attack_category=AttackCategory.PATH_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.8,
                description='路径遍历尝试',
                detection_rule='PATH_TRAVERSAL_DOT_DOT',
                remediation='检测到目录遍历，审查文件访问控制'
            ),
            AttackPattern(
                pattern=re.compile(r'%2e%2e', re.IGNORECASE),
                attack_category=AttackCategory.PATH_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.85,
                description='URL编码路径遍历',
                detection_rule='PATH_TRAVERSAL_URL_ENCODED',
                remediation='检测到编码绕过尝试，加强输入验证'
            ),
            AttackPattern(
                pattern=re.compile(r'(\/etc\/passwd|\/etc\/shadow|boot\.ini|win\.ini)', re.IGNORECASE),
                attack_category=AttackCategory.PATH_TRAVERSAL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                confidence=0.9,
                description='尝试读取敏感文件',
                detection_rule='SENSITIVE_FILE_ACCESS',
                remediation='检测到敏感文件访问，立即检查系统完整性'
            ),
        ])

        # ============== WebShell (T1505) ==============
        patterns.extend([
            # 可疑文件名
            AttackPattern(
                pattern=re.compile(r'shell\.php|cmd\.php|backdoor\.php|hack\.php|admin\.php', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='可疑PHP文件',
                detection_rule='WEBSHELL_SUSPICIOUS_FILE',
                remediation='检测到可疑文件名，立即隔离文件'
            ),
            # WebShell命令参数
            AttackPattern(
                pattern=re.compile(r'\?cmd=|\?action=|\?exec=|\?c=|\?_=', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='WebShell命令参数',
                detection_rule='WEBSHELL_CMD_PARAM',
                remediation='检测到可能的WebShell，审查文件内容'
            ),
            # 一句话木马 - eval/assert/system
            AttackPattern(
                pattern=re.compile(r'\$\w+\s*=\s*[\'"]?(eval|assert|system|shell_exec|passthru|proc_open|popen)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='一句话木马(eval/assert/system)',
                detection_rule='WEBSHELL_EVAL_ASSERT',
                remediation='检测到一句话木马，立即隔离文件'
            ),
            # Base64编码WebShell
            AttackPattern(
                pattern=re.compile(r'eval\s*\(\s*base64_decode\s*\(|gzinflate\s*\(\s*base64_decode', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='Base64编码WebShell',
                detection_rule='WEBSHELL_BASE64_ENCODED',
                remediation='检测到编码WebShell，解码分析恶意代码'
            ),
            # 动态变量函数调用
            AttackPattern(
                pattern=re.compile(r'\$(\w+)\s*=\s*["\']?\w+["\']?;\s*\$(\w+)\s*=\s*\$(\w+)\s*\(', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='动态变量函数调用',
                detection_rule='WEBSHELL_DYNAMIC_FUNC',
                remediation='检测到动态函数调用，可能存在混淆WebShell'
            ),
            # 文件包含利用
            AttackPattern(
                pattern=re.compile(r'(include|require|include_once|require_once)\s*\(?\s*\$_(GET|POST|REQUEST)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='动态文件包含',
                detection_rule='WEBSHELL_FILE_INCLUDE',
                remediation='检测到动态文件包含，可能存在远程文件包含漏洞'
            ),
            # 可疑字符串拼接
            AttackPattern(
                pattern=re.compile(r'\.\s*\$|\$\s*\.|\$[a-zA-Z_]\w*\s*\.\s*\$', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1505',
                confidence=0.6,
                description='可疑字符串拼接',
                detection_rule='WEBSHELL_STRING_CONCAT',
                remediation='检测到可疑字符串拼接，检查是否为混淆代码'
            ),
            #preg_replace危险用法
            AttackPattern(
                pattern=re.compile(r'preg_replace\s*\(\s*["\']/.*["\']\s*,\s*.*\$_(GET|POST|REQUEST)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='preg_replace代码执行',
                detection_rule='WEBSHELL_PREG_REPLACE',
                remediation='检测到preg_replace动态代码执行，立即隔离'
            ),
            # ASP/ASPX WebShell
            AttackPattern(
                pattern=re.compile(r'<%@\s*Page|<%@.*Language=.*VB|eval\s*\(\s*Request', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='ASP/ASPX WebShell',
                detection_rule='WEBSHELL_ASP',
                remediation='检测到ASP WebShell代码'
            ),
            # JavaScript Node.js WebShell
            AttackPattern(
                pattern=re.compile(r'(child_process|execSync|spawn)\s*\(.*\$_(GET|POST|REQUEST)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1505',
                description='Node.js命令注入WebShell',
                detection_rule='WEBSHELL_NODEJS',
                remediation='检测到Node.js恶意命令执行'
            ),
            # 可疑路径
            AttackPattern(
                pattern=re.compile(r'/uploads/.*\.(php|asp|aspx|jsp|js)|/temp/.*\.(php|asp|aspx|jsp)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='可疑路径访问',
                detection_rule='WEBSHELL_SUSPICIOUS_PATH',
                remediation='检测到可疑路径访问，可能上传了WebShell'
            ),
            # .htaccess恶意配置
            AttackPattern(
                pattern=re.compile(r'AddType\s+application/x-httpd-php|SetHandler\s+application/x-httpd-php', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='.htaccess PHP解析配置',
                detection_rule='WEBSHELL_HTACCESS',
                remediation='检测到恶意.htaccess配置，可能导致任意文件作为PHP执行'
            ),
            # XML外部实体注入
            AttackPattern(
                pattern=re.compile(r'(simplexml_load_file|simplexml_load_string|xml_load|Entity.*SYSTEM)', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='XML外部实体注入',
                detection_rule='WEBSHELL_XXE',
                remediation='检测到XXE可能，检查XML解析安全'
            ),
            # Python/Perl WebShell
            AttackPattern(
                pattern=re.compile(r'os\.system|subprocess|exec\(|eval\s*\(\s*\$|print\s*\(\s*\$', re.IGNORECASE),
                attack_category=AttackCategory.WEBSHELL,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1505',
                description='Python/Perl命令执行WebShell',
                detection_rule='WEBSHELL_PYTHON_PERL',
                remediation='检测到动态命令执行'
            ),
        ])

        # ============== 命令注入 (T1059) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'[;\|\$`\\]', re.IGNORECASE),
                attack_category=AttackCategory.COMMAND_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1059',
                confidence=0.7,
                description='命令注入字符',
                detection_rule='CMD_INJECTION_CHARS',
                remediation='检测到命令注入字符，检查输入验证'
            ),
            AttackPattern(
                pattern=re.compile(r'(wget|curl|nc|netcat).*(http|ftp)', re.IGNORECASE),
                attack_category=AttackCategory.COMMAND_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1059',
                description='下载工具使用',
                detection_rule='CMD_DOWNLOAD_TOOL',
                remediation='检测到可疑下载，可能下载恶意软件'
            ),
            AttackPattern(
                pattern=re.compile(r'bash\s+-i|sh\s+-i', re.IGNORECASE),
                attack_category=AttackCategory.COMMAND_INJECTION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1059',
                description='交互式Shell反弹',
                detection_rule='CMD_REVERSE_SHELL',
                remediation='检测到反弹Shell，立即隔离服务器'
            ),
        ])

        # ============== 权限提升 (T1068) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'su:.*successful.*root', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1068',
                description='用户切换到root',
                detection_rule='SU_TO_ROOT',
                remediation='检测到root权限获取，审查用户操作'
            ),
            AttackPattern(
                pattern=re.compile(r'chmod\s+[0-7]{3,4}\s+[0-7]{3,4}', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1068',
                description='敏感权限修改',
                detection_rule='CHMOD_SENSITIVE',
                remediation='检测到敏感文件权限修改'
            ),
            AttackPattern(
                pattern=re.compile(r'useradd.*UID\s*0|usermod.*-u\s*0', re.IGNORECASE),
                attack_category=AttackCategory.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1068',
                description='创建UID 0用户',
                detection_rule='UID_0_USER_CREATE',
                remediation='检测到后门用户创建，立即隔离'
            ),
        ])

        # ============== 横向移动 (T1021) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'Accepted publickey.*from\s+([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.LATERAL_MOVEMENT,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1021',
                description='SSH公钥认证成功',
                detection_rule='SSH_PUBKEY_SUCCESS',
                remediation='记录新SSH连接，检查是否异常'
            ),
            AttackPattern(
                pattern=re.compile(r'Failed password.*from\s+([\d.]+).*to\s+([\d.]+)', re.IGNORECASE),
                attack_category=AttackCategory.LATERAL_MOVEMENT,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1021',
                description='内部IP间SSH连接尝试',
                detection_rule='INTERNAL_SSH_ATTEMPT',
                remediation='检测到内部横向移动尝试'
            ),
        ])

        # ============== Log4j漏洞利用 (CVE-2021-44228) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'\$\{jndi:(ldap|rmi|dns):\/\/', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4Shell JNDI注入尝试',
                detection_rule='LOG4J_JNDI_INJECTION',
                remediation='立即阻断！这是Log4j RCE漏洞利用尝试'
            ),
            AttackPattern(
                pattern=re.compile(r'\$\{.*jndi.*ldap', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4j JNDI LDAP调用',
                detection_rule='LOG4J_JNDI_LDAP',
                remediation='检测到JNDI LDAP调用，检查是否加载恶意类'
            ),
            AttackPattern(
                pattern=re.compile(r'JNDI lookup for.*jndi', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4j JNDI查找操作',
                detection_rule='LOG4J_JNDI_LOOKUP',
                remediation='检测到JNDI查找，可能存在漏洞利用'
            ),
            AttackPattern(
                pattern=re.compile(r'Loaded remote class.*jndi', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4j加载远程类',
                detection_rule='LOG4J_REMOTE_CLASS',
                remediation='已加载远程类，确认被入侵！'
            ),
            AttackPattern(
                pattern=re.compile(r'CVE-2021-44228|Log4Shell', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4j漏洞利用告警',
                detection_rule='LOG4J_CVE_ALERT',
                remediation='检测到CVE-2021-44228漏洞利用告警'
            ),
            AttackPattern(
                pattern=re.compile(r'\$\{lower:.*\$\{upper:.*jndi', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1190',
                description='Log4j嵌套变量混淆',
                detection_rule='LOG4J_OBFUSCATED',
                remediation='检测到混淆的Log4j payload'
            ),
            AttackPattern(
                pattern=re.compile(r'Exception thrown processing.*jndi', re.IGNORECASE),
                attack_category=AttackCategory.LOG4J,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1190',
                description='Log4j JNDI处理异常',
                detection_rule='LOG4J_JNDI_EXCEPTION',
                remediation='应用尝试处理JNDI时抛出异常'
            ),
        ])

        # ============== 数据外泄 (T1041) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(rsync|scp|sftp).*(upload|send).*(\d+\s+KB|\d+\s+MB)', re.IGNORECASE),
                attack_category=AttackCategory.DATA_EXFILTRATION,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1041',
                description='大量数据上传',
                detection_rule='DATA_EXFIL_UPLOAD',
                remediation='检测到大量数据外泄'
            ),
            AttackPattern(
                pattern=re.compile(r'tar\s+.*cvzf.*\|.*nc\s+|nc\s+.*\|.*tar', re.IGNORECASE),
                attack_category=AttackCategory.DATA_EXFILTRATION,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1041',
                description='通过nc传输数据',
                detection_rule='DATA_EXFIL_NC_TAR',
                remediation='检测到nc隧道数据传输，立即隔离'
            ),
        ])

        # ============== DNS隧道 (T1071) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'query:\s*(TXT|NULL|MX)\s+[a-z0-9]+\.(evil|exfil|tunnel|c2|stealth)', re.IGNORECASE),
                attack_category=AttackCategory.DNS_TUNNELING,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1071',
                description='可疑DNS查询',
                detection_rule='DNS_SUSPICIOUS_QUERY',
                remediation='检测到DNS隧道迹象'
            ),
            AttackPattern(
                pattern=re.compile(r'DNS.*TXT.*size=\d{3,}', re.IGNORECASE),
                attack_category=AttackCategory.DNS_TUNNELING,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1071',
                description='大量DNS响应',
                detection_rule='DNS_LARGE_RESPONSE',
                remediation='检测到异常DNS响应大小'
            ),
        ])

        # ============== DDoS (T1498) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(SYN|UDP|ICMP|ACK|RST)\s+flood.*rate=\d+', re.IGNORECASE),
                attack_category=AttackCategory.DENIAL_OF_SERVICE,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1498',
                description='DDoS攻击检测',
                detection_rule='DDOS_FLOOD_DETECTED',
                remediation='检测到DDoS攻击，启动流量清洗'
            ),
            AttackPattern(
                pattern=re.compile(r'rate=\d+pps', re.IGNORECASE),
                attack_category=AttackCategory.DENIAL_OF_SERVICE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1498',
                description='高流量速率',
                detection_rule='HIGH_RATE_DETECTED',
                remediation='检测到异常高流量'
            ),
        ])

        # ============== 勒索软件 (T1486) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(\.encrypted|\.locked|\.crypto|\.ransom|READ_ME)', re.IGNORECASE),
                attack_category=AttackCategory.RANSOMWARE,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1486',
                description='勒索软件加密扩展名',
                detection_rule='RANSOMWARE_EXTENSION',
                remediation='检测到勒索软件，立即隔离并启动恢复流程'
            ),
            AttackPattern(
                pattern=re.compile(r'ransom|bitcoin|btc|payment', re.IGNORECASE),
                attack_category=AttackCategory.RANSOMWARE,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1486',
                description='勒索相关信息',
                detection_rule='RANSOMWARE_NOTE',
                remediation='检测到勒索软件相关信息'
            ),
        ])

        # ============== 钓鱼攻击 (T1566) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(login|account|verify|secure|update).*(redirect|callback)', re.IGNORECASE),
                attack_category=AttackCategory.PHISHING,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1566',
                description='可疑重定向参数',
                detection_rule='PHISHING_REDIRECT',
                remediation='检测到可疑URL重定向'
            ),
            AttackPattern(
                pattern=re.compile(r'token=STOLEN|token=PHISHING', re.IGNORECASE),
                attack_category=AttackCategory.PHISHING,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1566',
                description='钓鱼Token检测',
                detection_rule='PHISHING_TOKEN',
                remediation='检测到钓鱼攻击Token'
            ),
        ])

        # ============== 持久化 (T1547) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'new\s+user.*UID\s+\d+|useradd.*UID\s+\d+', re.IGNORECASE),
                attack_category=AttackCategory.PERSISTENCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1547',
                description='创建新用户',
                detection_rule='NEW_USER_CREATED',
                remediation='检测到新用户创建'
            ),
            AttackPattern(
                pattern=re.compile(r'cronjob|cron.*\*|crontab', re.IGNORECASE),
                attack_category=AttackCategory.PERSISTENCE,
                threat_level=ThreatLevel.MEDIUM,
                mitre_technique='T1547',
                description='定时任务配置',
                detection_rule='CRON_JOB_CONFIGURED',
                remediation='检测到定时任务，可能用于持久化'
            ),
        ])

        # ============== 漏洞扫描 (T1595) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(nikto|burp|owasp|acunetix|nessus|openvas)', re.IGNORECASE),
                attack_category=AttackCategory.VULNERABILITY_SCAN,
                threat_level=ThreatLevel.LOW,
                mitre_technique='T1595',
                description='漏洞扫描器User-Agent',
                detection_rule='SCANNER_USER_AGENT',
                remediation='检测到漏洞扫描器'
            ),
        ])

        # ============== 可疑进程 (T1057) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(mimikatz|powershell.*-enc|base64.*decode)', re.IGNORECASE),
                attack_category=AttackCategory.CREDENTIAL_THEFT,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1003',
                description='凭证窃取工具',
                detection_rule='CREDENTIAL_TOOL_DETECTED',
                remediation='检测到凭证窃取工具，立即隔离'
            ),
        ])

        # ============== 挖矿活动 (T1496) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(xmrig|cryptonight|monero|ethminer|coinminer)', re.IGNORECASE),
                attack_category=AttackCategory.CRYPTO_MINING,
                threat_level=ThreatLevel.HIGH,
                mitre_technique='T1496',
                description='加密货币挖矿进程',
                detection_rule='CRYPTO_MINING_DETECTED',
                remediation='检测到挖矿活动，终止进程并检查系统'
            ),
        ])

        # ============== 二进制载荷 (T1204) ==============
        patterns.extend([
            AttackPattern(
                pattern=re.compile(r'(exe|elf|dll|so)\s+uploaded|upload.*(exe|elf|dll)', re.IGNORECASE),
                attack_category=AttackCategory.BINARY_PAYLOAD,
                threat_level=ThreatLevel.CRITICAL,
                mitre_technique='T1204',
                description='可执行文件上传',
                detection_rule='BINARY_UPLOAD',
                remediation='检测到可执行文件上传，立即隔离'
            ),
        ])

        return patterns

    def _load_ip_reputation(self) -> Dict[str, Dict]:
        """加载IP信誉库"""
        return {
            # Tor出口节点
            '185.220.101.46': {'type': 'malicious', 'tags': ['tor', 'exit-node']},
            '23.129.64.213': {'type': 'malicious', 'tags': ['tor', 'exit-node']},
            # 已知恶意IP
            '45.154.255.147': {'type': 'malicious', 'tags': ['brute-force', 'scanner']},
            '91.121.87.18': {'type': 'suspicious', 'tags': ['scan']},
        }

    def analyze_file(self, filepath: str) -> List[SecurityEvent]:
        """分析单个日志文件"""
        logger.info(f"分析文件: {filepath}")
        events = []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    detected = self._analyze_line(line, line_num)
                    if detected:
                        events.extend(detected)

        except Exception as e:
            logger.error(f"分析文件失败 {filepath}: {e}")

        logger.info(f"从 {filepath} 检测到 {len(events)} 个安全事件")
        return events

    def analyze_directory(self, directory: str, recursive: bool = True) -> List[SecurityEvent]:
        """分析目录中的所有日志文件"""
        all_events = []
        directory_path = Path(directory)

        if directory_path.is_file():
            return self.analyze_file(str(directory_path))

        pattern = '**/*.log' if recursive else '*.log'
        for log_file in directory_path.glob(pattern):
            events = self.analyze_file(str(log_file))
            all_events.extend(events)

        return all_events

    def _analyze_line(self, line: str, line_num: int) -> List[SecurityEvent]:
        """分析单行日志"""
        events = []
        timestamp = self._extract_timestamp(line)

        for pattern in self.attack_patterns:
            try:
                match = pattern.pattern.search(line)
                if match:
                    event = self._create_event(line, line_num, timestamp, match, pattern)
                    if event:
                        events.append(event)
            except Exception as e:
                logger.debug(f"模式匹配错误: {e}")

        return events

    def _extract_timestamp(self, line: str) -> str:
        """提取时间戳"""
        # 多种时间格式
        formats = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
        ]

        for fmt in formats:
            match = re.search(fmt, line)
            if match:
                return match.group()

        return datetime.now().isoformat()

    def _create_event(self, line: str, line_num: int, timestamp: str,
                      match, pattern: AttackPattern) -> Optional[SecurityEvent]:
        """创建安全事件"""
        source_ip = None
        groups = match.groups() if match.groups() else []

        # 提取源IP
        if groups:
            for g in groups:
                if g and re.match(r'^[\d.]+$', g):
                    source_ip = g
                    break

        # 检查IP信誉
        threat_level = pattern.threat_level
        if source_ip and source_ip in self.ip_reputation:
            rep = self.ip_reputation[source_ip]
            if rep['type'] == 'malicious':
                threat_level = ThreatLevel.CRITICAL

        event = SecurityEvent(
            timestamp=timestamp,
            source_ip=source_ip,
            raw_log=line,
            threat_level=threat_level,
            attack_category=pattern.attack_category,
            mitre_technique=pattern.mitre_technique,
            confidence=pattern.confidence,
            detection_rule=pattern.detection_rule,
            description=pattern.description,
            remediation=pattern.remediation,
            timeline_order=line_num
        )

        self.stats[pattern.attack_category] += 1
        return event

    def run_deeplog_anomaly_detection(self, log_lines: List[str]) -> List[SecurityEvent]:
        """使用DeepLog进行异常检测"""
        if not self.deeplog_model or not self.deeplog_trained:
            logger.warning("DeepLog模型未训练，无法进行异常检测")
            return []

        events = []
        try:
            results = self.deeplog_model.detect(log_lines)
            for i, (is_anomaly, score) in enumerate(results):
                if is_anomaly:
                    event = SecurityEvent(
                        timestamp=datetime.now().isoformat(),
                        raw_log=log_lines[i] if i < len(log_lines) else "",
                        threat_level=ThreatLevel.MEDIUM,
                        attack_category=AttackCategory.UNKNOWN,
                        deeplog_score=score,
                        is_anomaly=True,
                        description=f"DeepLog检测到异常 (分数: {score:.4f})"
                    )
                    events.append(event)
        except Exception as e:
            logger.error(f"DeepLog检测失败: {e}")

        return events

    def train_deeplog(self, log_lines: List[str], epochs: int = 10):
        """训练DeepLog模型"""
        if not self.deeplog_model:
            logger.warning("DeepLog模型未初始化")
            return

        try:
            self.deeplog_model.train(log_lines, epochs=epochs)
            self.deeplog_trained = True
            logger.info("DeepLog模型训练完成")
        except Exception as e:
            logger.error(f"DeepLog训练失败: {e}")

    def scan_webshell(self, directory: str, extensions: List[str] = None) -> List[Dict]:
        """扫描WebShell文件"""
        if extensions is None:
            extensions = ['.php', '.jsp', '.asp', '.aspx', '.html', '.js']

        webshell_patterns = [
            (re.compile(r'eval\s*\(\s*\$', re.IGNORECASE), 'eval($_REQUEST', 0.9),
            (re.compile(r'system\s*\(\s*\$', re.IGNORECASE), 'system($_REQUEST', 0.9),
            (re.compile(r'shell_exec\s*\(\s*\$', re.IGNORECASE), 'shell_exec($_REQUEST', 0.85),
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

    def analyze_attack_chains(self, events: List[SecurityEvent]) -> List[AttackChain]:
        """分析攻击链"""
        # 按源IP和时间分组
        ip_events = defaultdict(list)
        for event in events:
            if event.source_ip:
                ip_events[event.source_ip].append(event)

        chains = []
        for ip, ip_events_list in ip_events.items():
            # 排序
            ip_events_list.sort(key=lambda x: x.timeline_order)

            # 检测攻击链模式
            stages = []
            chain = AttackChain(
                chain_id=f"CHAIN_{ip.replace('.', '')}",
                source_ips={ip},
                threat_level=ThreatLevel.MEDIUM
            )

            for event in ip_events_list:
                if event.attack_category == AttackCategory.BRUTE_FORCE:
                    stages.append({'stage': 'initial_access', 'event': event})
                elif event.attack_category == AttackCategory.SQL_INJECTION:
                    stages.append({'stage': 'initial_access', 'event': event})
                elif event.attack_category == AttackCategory.PRIVILEGE_ESCALATION:
                    stages.append({'stage': 'privilege_escalation', 'event': event})
                elif event.attack_category == AttackCategory.LATERAL_MOVEMENT:
                    stages.append({'stage': 'lateral_movement', 'event': event})
                elif event.attack_category == AttackCategory.DATA_EXFILTRATION:
                    stages.append({'stage': 'exfiltration', 'event': event})
                    chain.threat_level = ThreatLevel.CRITICAL

            if len(stages) >= 2:
                chain.stages = stages
                chain.description = f"从 {ip} 开始的攻击链，包含 {len(stages)} 个阶段"
                chains.append(chain)

        return chains

    def generate_report(self, events: List[SecurityEvent],
                       webshell_results: List[Dict] = None,
                       output_format: str = 'json') -> Dict:
        """生成分析报告"""
        # 排序事件
        sorted_events = sorted(events, key=lambda x: (
            x.threat_level == ThreatLevel.CRITICAL,
            x.threat_level == ThreatLevel.HIGH,
            -x.timeline_order
        ))

        # 统计
        threat_stats = Counter(e.threat_level for e in events)
        category_stats = Counter(e.attack_category for e in events)
        source_ips = Counter(e.source_ip for e in events if e.source_ip)

        # 关键事件
        critical_events = [e for e in sorted_events
                         if e.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]]

        # 计算风险等级
        risk_level = ThreatLevel.INFO
        if threat_stats.get(ThreatLevel.CRITICAL, 0) > 0:
            risk_level = ThreatLevel.CRITICAL
        elif threat_stats.get(ThreatLevel.HIGH, 0) > 10:
            risk_level = ThreatLevel.CRITICAL
        elif threat_stats.get(ThreatLevel.HIGH, 0) > 0:
            risk_level = ThreatLevel.HIGH
        elif threat_stats.get(ThreatLevel.MEDIUM, 0) > 20:
            risk_level = ThreatLevel.HIGH
        elif threat_stats.get(ThreatLevel.MEDIUM, 0) > 0:
            risk_level = ThreatLevel.MEDIUM

        # WebShell统计
        webshell_stats = {
            'total_suspect_files': len(webshell_results) if webshell_results else 0,
            'high_confidence': len([r for r in webshell_results or [] if r.get('threat_level') == 'HIGH']),
        }

        report = {
            'report_info': {
                'tool_version': '2.0.0',
                'generated_at': datetime.now().isoformat(),
                'total_events': len(events),
                'critical_events': len(critical_events),
                'deeplog_available': DEEPLOG_AVAILABLE,
                'deeplog_trained': self.deeplog_trained,
            },
            'executive_summary': {
                'risk_level': risk_level,
                'total_events': len(events),
                'critical_events': len(critical_events),
                'high_events': threat_stats.get(ThreatLevel.HIGH, 0),
                'medium_events': threat_stats.get(ThreatLevel.MEDIUM, 0),
                'top_attack_categories': dict(category_stats.most_common(10)),
                'top_source_ips': dict(source_ips.most_common(10)),
            },
            'threat_level_distribution': dict(threat_stats),
            'attack_category_distribution': dict(category_stats),
            'critical_events': [
                {
                    'timestamp': e.timestamp,
                    'threat_level': e.threat_level,
                    'attack_type': e.attack_category,
                    'source_ip': e.source_ip,
                    'description': e.description,
                    'raw_log': e.raw_log[:200],
                    'remediation': e.remediation,
                    'mitre_technique': e.mitre_technique,
                    'deeplog_score': e.deeplog_score,
                }
                for e in critical_events[:50]
            ],
            'timeline': [
                {
                    'order': e.timeline_order,
                    'timestamp': e.timestamp,
                    'threat': e.threat_level,
                    'attack_type': e.attack_category,
                    'source_ip': e.source_ip,
                    'raw_log': e.raw_log[:100],
                }
                for e in sorted_events[:100]
            ],
            'web_shell_scan': {
                **webshell_stats,
                'suspect_files': webshell_results[:20] if webshell_results else []
            },
            'recommendations': self._generate_recommendations(threat_stats, category_stats),
        }

        return report

    def _generate_recommendations(self, threat_stats: Counter, category_stats: Counter) -> List[Dict]:
        """生成修复建议"""
        recommendations = []

        if category_stats.get('暴力破解', 0) > 5:
            recommendations.append({
                'severity': 'HIGH',
                'category': '暴力破解',
                'finding': f'检测到{category_stats["暴力破解"]}次暴力破解尝试',
                'recommendation': '1. 封禁攻击源IP\n2. 启用账户锁定策略\n3. 启用双因素认证\n4. 审查失败的登录日志'
            })

        if category_stats.get('SQL注入', 0) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': 'SQL注入',
                'finding': f'检测到{category_stats["SQL注入"]}次SQL注入尝试',
                'recommendation': '1. 立即审查Web应用防火墙配置\n2. 检查数据库审计日志\n3. 审查输入验证和参数化查询\n4. 考虑临时阻断受影响IP'
            })

        if category_stats.get('WebShell', 0) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': 'WebShell',
                'finding': f'检测到{category_stats["WebShell"]}次WebShell活动',
                'recommendation': '1. 立即隔离可疑文件\n2. 检查文件上传功能\n3. 审查Web目录\n4. 检查Web服务器配置'
            })

        if category_stats.get('权限提升', 0) > 0:
            recommendations.append({
                'severity': 'HIGH',
                'category': '权限提升',
                'finding': f'检测到{category_stats["权限提升"]}次权限提升行为',
                'recommendation': '1. 审查sudo日志\n2. 检查用户创建记录\n3. 审核文件权限\n4. 检查认证配置'
            })

        if category_stats.get('数据外泄', 0) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': '数据外泄',
                'finding': f'检测到{category_stats["数据外泄"]}次数据外泄行为',
                'recommendation': '1. 立即隔离受影响系统\n2. 检查数据传输记录\n3. 审查网络出口流量\n4. 通知安全团队'
            })

        if category_stats.get('勒索软件', 0) > 0:
            recommendations.append({
                'severity': 'CRITICAL',
                'category': '勒索软件',
                'finding': '检测到勒索软件活动',
                'recommendation': '1. 立即隔离所有受影响系统\n2. 不要支付赎金\n3. 联系安全团队\n4. 启动灾难恢复流程\n5. 检查备份完整性'
            })

        return recommendations


# ============== CLI入口 ==============

def main():
    parser = argparse.ArgumentParser(
        description='增强安全事件分析器 - 集成DeepLog和扩展攻击模式库'
    )
    parser.add_argument('--input', '-i', required=True, help='输入文件或目录')
    parser.add_argument('--output', '-o', default='security_report.json', help='输出报告文件')
    parser.add_argument('--webshell', '-w', help='WebShell扫描目录')
    parser.add_argument('--format', choices=['json', 'txt'], default='json', help='输出格式')
    parser.add_argument('--deeplog-train', action='store_true', help='训练DeepLog模型')
    parser.add_argument('--deeplog-detect', action='store_true', help='使用DeepLog检测')

    args = parser.parse_args()

    analyzer = EnhancedSecurityAnalyzer(config={
        'use_deeplog': args.deeplog_detect or args.deeplog_train
    })

    # 分析日志
    if os.path.isdir(args.input):
        events = analyzer.analyze_directory(args.input)
    else:
        events = analyzer.analyze_file(args.input)

    # WebShell扫描
    webshell_results = []
    if args.webshell:
        webshell_results = analyzer.scan_webshell(args.webshell)

    # DeepLog训练
    if args.deeplog_train:
        log_lines = []
        if os.path.isdir(args.input):
            for root, _, files in os.walk(args.input):
                for f in files:
                    if f.endswith('.log'):
                        with open(os.path.join(root, f), 'r') as fp:
                            log_lines.extend(fp.readlines()[:1000])
        elif os.path.isfile(args.input):
            with open(args.input, 'r') as f:
                log_lines = f.readlines()[:1000]

        if log_lines:
            analyzer.train_deeplog(log_lines)

    # DeepLog异常检测
    if args.deeplog_detect and analyzer.deeplog_trained:
        log_lines = []
        if os.path.isfile(args.input):
            with open(args.input, 'r') as f:
                log_lines = f.readlines()
        deeplog_events = analyzer.run_deeplog_anomaly_detection(log_lines)
        events.extend(deeplog_events)

    # 生成报告
    report = analyzer.generate_report(events, webshell_results, args.format)

    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=============================================================")
    print(f"        安全事件分析完成")
    print(f"=============================================================")
    print(f"总事件数: {report['executive_summary']['total_events']}")
    print(f"风险等级: {report['executive_summary']['risk_level']}")
    print(f"关键事件: {report['executive_summary']['critical_events']}")
    print(f"WebShell扫描: {report['web_shell_scan']['total_suspect_files']} 个可疑文件")
    print(f"\n报告已保存至: {args.output}")
    print(f"=============================================================")


if __name__ == '__main__':
    main()
