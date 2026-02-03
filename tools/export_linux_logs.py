"""
Linux系统日志导出工具
导出Linux系统日志为文本格式，便于DeepLog使用
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime, timedelta


def find_linux_logs():
    """查找常见的Linux日志文件"""
    common_logs = {
        'syslog': '/var/log/syslog',
        'messages': '/var/log/messages',
        'auth': '/var/log/auth.log',
        'kern': '/var/log/kern.log',
        'daemon': '/var/log/daemon.log',
        'system': '/var/log/system.log',  # macOS
    }
    
    found_logs = {}
    for name, path in common_logs.items():
        if os.path.exists(path):
            found_logs[name] = path
    
    return found_logs


def export_log_file(log_file: str, output_file: str, 
                   lines: int = None,
                   start_date: str = None,
                   end_date: str = None):
    """
    导出日志文件
    
    Args:
        log_file: 日志文件路径
        output_file: 输出文件路径
        lines: 导出的行数（从文件末尾开始，None表示全部）
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）
    """
    if not os.path.exists(log_file):
        print(f"错误: 日志文件不存在: {log_file}")
        return False
    
    try:
        # 读取日志
        if lines:
            # 使用tail命令读取最后N行（更高效）
            try:
                result = subprocess.run(
                    ['tail', '-n', str(lines), log_file],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if result.returncode == 0:
                    log_lines = result.stdout.splitlines()
                else:
                    # 回退到Python方法
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        log_lines = [line.strip() for line in all_lines[-lines:]]
            except:
                # 如果tail命令不可用，使用Python方法
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    log_lines = [line.strip() for line in all_lines[-lines:]]
        else:
            # 读取所有行
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_lines = [line.strip() for line in f if line.strip()]
        
        # 日期过滤
        if start_date or end_date:
            filtered_lines = []
            start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            if end_dt:
                end_dt = end_dt + timedelta(days=1)  # 包含结束日期当天
            
            for line in log_lines:
                # 尝试从日志行中提取日期
                # Linux syslog格式: Jan 16 10:00:00 hostname message
                # 或: 2024-01-16T10:00:00 message
                try:
                    # 尝试解析标准syslog格式
                    if len(line) > 15:
                        # 格式1: Jan 16 10:00:00
                        date_str = line[:15]
                        try:
                            log_date = datetime.strptime(date_str, '%b %d %H:%M:%S')
                            # 使用当前年份（因为syslog不包含年份）
                            log_date = log_date.replace(year=datetime.now().year)
                        except:
                            # 格式2: 2024-01-16T10:00:00
                            if 'T' in line[:20]:
                                date_str = line[:19]
                                log_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                            else:
                                # 格式3: 2024-01-16 10:00:00
                                date_str = line[:19]
                                log_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            
                            if start_dt and log_date < start_dt:
                                continue
                            if end_dt and log_date >= end_dt:
                                continue
                except:
                    pass  # 如果解析失败，保留该行
                
                filtered_lines.append(line)
            
            log_lines = filtered_lines
        
        # 写入输出文件
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in log_lines:
                f.write(line + '\n')
        
        print(f"成功导出 {len(log_lines)} 条日志到 {output_file}")
        return True
        
    except PermissionError:
        print(f"错误: 没有权限读取文件 {log_file}")
        print("提示: 请使用sudo运行此脚本")
        return False
    except Exception as e:
        print(f"导出失败: {e}")
        return False


def export_all_logs(output_dir: str = "logs/linux_logs", lines: int = None):
    """
    导出所有找到的Linux日志
    
    Args:
        output_dir: 输出目录
        lines: 每个日志的最大行数
    """
    os.makedirs(output_dir, exist_ok=True)
    
    found_logs = find_linux_logs()
    
    if not found_logs:
        print("未找到常见的Linux日志文件")
        print("常见位置: /var/log/syslog, /var/log/messages, /var/log/auth.log 等")
        return
    
    print(f"找到 {len(found_logs)} 个日志文件:\n")
    
    for name, path in found_logs.items():
        output_file = os.path.join(output_dir, f"linux_{name}_log.txt")
        print(f"导出 {name} 日志 ({path})...")
        export_log_file(path, output_file, lines=lines)
        print()


def main():
    parser = argparse.ArgumentParser(
        description='导出Linux系统日志',
        epilog='注意: 某些日志文件可能需要root权限才能读取'
    )
    parser.add_argument('--log-file', type=str, help='日志文件路径')
    parser.add_argument('--output', type=str, default='linux_log.txt', help='输出文件路径')
    parser.add_argument('--lines', type=int, help='导出的行数（从文件末尾开始）')
    parser.add_argument('--start-date', type=str, help='开始日期（格式：YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（格式：YYYY-MM-DD）')
    parser.add_argument('--find', action='store_true', help='查找常见的Linux日志位置')
    parser.add_argument('--all', action='store_true', help='导出所有找到的日志')
    parser.add_argument('--output-dir', type=str, default='logs/linux_logs', help='输出目录（用于--all选项）')
    
    args = parser.parse_args()
    
    if args.find:
        found = find_linux_logs()
        if found:
            print("找到以下Linux日志文件:")
            for name, path in found.items():
                print(f"  {name}: {path}")
        else:
            print("未找到常见的Linux日志文件")
            print("\n常见位置:")
            print("  /var/log/syslog")
            print("  /var/log/messages")
            print("  /var/log/auth.log")
            print("  /var/log/kern.log")
            print("  /var/log/daemon.log")
        return
    
    if args.all:
        export_all_logs(args.output_dir, lines=args.lines)
        return
    
    if not args.log_file:
        print("错误: 请指定 --log-file 参数")
        print("\n示例:")
        print("  python export_linux_logs.py --log-file /var/log/syslog --output syslog.txt")
        print("  python export_linux_logs.py --log-file /var/log/syslog --lines 10000")
        print("  python export_linux_logs.py --all --output-dir logs/linux_logs")
        print("  python export_linux_logs.py --find  # 查找日志文件")
        print("\n注意: 某些日志文件可能需要sudo权限")
        return
    
    export_log_file(
        args.log_file,
        args.output,
        lines=args.lines,
        start_date=args.start_date,
        end_date=args.end_date
    )


if __name__ == "__main__":
    main()

