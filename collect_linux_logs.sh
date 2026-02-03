#!/bin/bash
# 应急响应日志收集脚本 - Incident Response Collection Script
# 在目标Linux服务器上运行此脚本收集日志

set -e

# 配置
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="incident_response_${TIMESTAMP}"
LOG_FILE="${OUTPUT_DIR}/collection.log"

# 创建输出目录
mkdir -p "${OUTPUT_DIR}"

# 记录收集开始
echo "[$(date)] 开始收集系统日志..." > "${LOG_FILE}"

# 收集系统信息
echo "=== 系统信息 ===" > "${OUTPUT_DIR}/system_info.txt"
uname -a >> "${OUTPUT_DIR}/system_info.txt" 2>/dev/null
hostname >> "${OUTPUT_DIR}/system_info.txt" 2>/dev/null
uptime >> "${OUTPUT_DIR}/system_info.txt" 2>/dev/null

# 收集网络连接
echo "=== 网络连接 ===" > "${OUTPUT_DIR}/network_connections.txt"
netstat -tunap 2>/dev/null >> "${OUTPUT_DIR}/network_connections.txt" || ss -tunap >> "${OUTPUT_DIR}/network_connections.txt"

# 收集进程列表
echo "=== 进程列表 ===" > "${OUTPUT_DIR}/process_list.txt"
ps auxf >> "${OUTPUT_DIR}/process_list.txt" 2>/dev/null || ps -ef >> "${OUTPUT_DIR}/process_list.txt"

# 收集定时任务
echo "=== 定时任务 ===" > "${OUTPUT_DIR}/cron_jobs.txt"
crontab -l >> "${OUTPUT_DIR}/cron_jobs.txt" 2>/dev/null
ls -la /etc/cron.d/ >> "${OUTPUT_DIR}/cron_jobs.txt" 2>/dev/null
ls -la /etc/cron.hourly/ >> "${OUTPUT_DIR}/cron_jobs.txt" 2>/dev/null

# 收集用户信息
echo "=== 用户信息 ===" > "${OUTPUT_DIR}/users.txt"
cat /etc/passwd >> "${OUTPUT_DIR}/users.txt" 2>/dev/null
lastlog >> "${OUTPUT_DIR}/users.txt" 2>/dev/null
who >> "${OUTPUT_DIR}/users.txt" 2>/dev/null

# 收集sudo使用记录
echo "=== Sudo使用记录 ===" > "${OUTPUT_DIR}/sudo_history.txt"
cat /var/log/auth.log 2>/dev/null | grep sudo >> "${OUTPUT_DIR}/sudo_history.txt" || true
cat /var/log/secure 2>/dev/null | grep sudo >> "${OUTPUT_DIR}/sudo_history.txt" || true

# 收集认证日志
echo "=== 认证日志 ===" > "${OUTPUT_DIR}/auth_logs.txt"
if [ -f /var/log/auth.log ]; then
    tail -n 10000 /var/log/auth.log > "${OUTPUT_DIR}/auth.log" 2>/dev/null || true
fi
if [ -f /var/log/secure ]; then
    tail -n 10000 /var/log/secure > "${OUTPUT_DIR}/secure.log" 2>/dev/null || true
fi

# 收集系统日志
echo "=== 系统日志 ===" > "${OUTPUT_DIR}/system_logs.txt"
if [ -f /var/log/syslog ]; then
    tail -n 10000 /var/log/syslog > "${OUTPUT_DIR}/syslog.log" 2>/dev/null || true
fi
if [ -f /var/log/messages ]; then
    tail -n 10000 /var/log/messages > "${OUTPUT_DIR}/messages.log" 2>/dev/null || true
fi

# 收集内核日志
if [ -f /var/log/kern.log ]; then
    tail -n 5000 /var/log/kern.log > "${OUTPUT_DIR}/kern.log" 2>/dev/null || true
fi

# 收集Web服务器日志
echo "=== Web服务器日志 ===" > "${OUTPUT_DIR}/web_logs.txt"
for dir in /var/log/apache2 /var/log/nginx /var/log/httpd; do
    if [ -d "$dir" ]; then
        mkdir -p "${OUTPUT_DIR}/web_logs/$(basename $dir)"
        for log in $dir/*.log; do
            if [ -f "$log" ]; then
                tail -n 5000 "$log" > "${OUTPUT_DIR}/web_logs/$(basename $dir)/$(basename $log)" 2>/dev/null || true
            fi
        done
    fi
done

# 收集数据库日志
echo "=== 数据库日志 ===" > "${OUTPUT_DIR}/db_logs.txt"
for dir in /var/log/mysql /var/log/postgresql /var/log/mongodb; do
    if [ -d "$dir" ]; then
        mkdir -p "${OUTPUT_DIR}/db_logs/$(basename $dir)"
        for log in $dir/*.log; do
            if [ -f "$log" ]; then
                tail -n 5000 "$log" > "${OUTPUT_DIR}/db_logs/$(basename $dir)/$(basename $log)" 2>/dev/null || true
            fi
        done
    fi
done

# 收集SSH记录
echo "=== SSH记录 ===" > "${OUTPUT_DIR}/ssh_logs.txt"
if [ -f /var/log/auth.log ]; then
    grep sshd "${OUTPUT_DIR}/auth.log" > "${OUTPUT_DIR}/sshd.log" 2>/dev/null || true
fi
cat /var/log/btmp* 2>/dev/null > "${OUTPUT_DIR}/btmp.bin" || true

# 收集ARP和DNS缓存
echo "=== 网络缓存 ===" > "${OUTPUT_DIR}/network_cache.txt"
arp -n >> "${OUTPUT_DIR}/network_cache.txt" 2>/dev/null || true
cat /etc/hosts >> "${OUTPUT_DIR}/network_cache.txt" 2>/dev/null || true

# 收集系统调用审计
if [ -f /var/log/audit/audit.log ]; then
    echo "=== 审计日志 ===" > "${OUTPUT_DIR}/audit_logs.txt"
    tail -n 10000 /var/log/audit/audit.log > "${OUTPUT_DIR}/audit.log" 2>/dev/null || true
fi

# 压缩收集的数据
echo "[$(date)] 压缩收集的数据..." >> "${LOG_FILE}"
tar -czf "${OUTPUT_DIR}.tar.gz" "${OUTPUT_DIR}" 2>/dev/null

# 清理临时目录
rm -rf "${OUTPUT_DIR}"

echo ""
echo "========================================"
echo "   应急响应日志收集完成"
echo "========================================"
echo "输出文件: ${OUTPUT_DIR}.tar.gz"
echo ""
echo "使用方法:"
echo "  1. 解压: tar -xzf ${OUTPUT_DIR}.tar.gz"
echo "  2. 分析: python incident_response.py --auto ${OUTPUT_DIR}"
echo "========================================"
