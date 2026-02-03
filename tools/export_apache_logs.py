"""
Apache日志导出工具
从Apache日志文件导出日志，便于DeepLog使用
"""

import os
import sys
import argparse
from datetime import datetime, timedelta


def export_apache_logs(log_file: str, output_file: str, 
                       lines: int = None, 
                       start_date: str = None,
                       end_date: str = None):
    """
    导出Apache日志
    
    Args:
        log_file: Apache日志文件路径
        output_file: 输出文件路径
        lines: 导出的行数（从文件末尾开始，None表示全部）
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）
    """
    if not os.path.exists(log_file):
        print(f"错误: 日志文件不存在: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            if lines:
                # 读取最后N行
                all_lines = f.readlines()
                log_lines = all_lines[-lines:]
            else:
                # 读取所有行
                log_lines = f.readlines()
        
        # 日期过滤
        if start_date or end_date:
            filtered_lines = []
            start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            if end_dt:
                end_dt = end_dt + timedelta(days=1)  # 包含结束日期当天
            
            for line in log_lines:
                # 尝试从日志行中提取日期（Apache日志格式）
                # 格式: [16/Jan/2024:10:00:00 +0800]
                try:
                    date_start = line.find('[')
                    if date_start != -1:
                        date_end = line.find(':', date_start + 1)
                        if date_end != -1:
                            date_str = line[date_start + 1:date_end]
                            # 解析日期: 16/Jan/2024
                            log_date = datetime.strptime(date_str, '%d/%b/%Y')
                            
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
            f.writelines(log_lines)
        
        print(f"成功导出 {len(log_lines)} 条日志到 {output_file}")
        
    except Exception as e:
        print(f"导出失败: {e}")


def find_apache_logs():
    """查找常见的Apache日志位置"""
    common_paths = [
        # Linux
        '/var/log/apache2/access.log',
        '/var/log/apache2/error.log',
        '/var/log/httpd/access_log',
        '/var/log/httpd/error_log',
        # Windows
        'C:\\Apache24\\logs\\access.log',
        'C:\\Apache24\\logs\\error.log',
        'C:\\xampp\\apache\\logs\\access.log',
        'C:\\xampp\\apache\\logs\\error.log',
    ]
    
    found_logs = []
    for path in common_paths:
        if os.path.exists(path):
            found_logs.append(path)
    
    return found_logs


def main():
    parser = argparse.ArgumentParser(
        description='导出Apache日志',
        epilog='注意: 这是Apache日志导出工具。Windows系统日志请使用 export_windows_logs.py'
    )
    parser.add_argument('--log-file', type=str, help='Apache日志文件路径')
    parser.add_argument('--output', type=str, default='apache_log.txt', help='输出文件路径')
    parser.add_argument('--lines', type=int, help='导出的行数（从文件末尾开始）')
    parser.add_argument('--start-date', type=str, help='开始日期（格式：YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（格式：YYYY-MM-DD）')
    parser.add_argument('--find', action='store_true', help='查找常见的Apache日志位置')
    
    args = parser.parse_args()
    
    # 检查是否误用了Windows日志工具的参数
    if '--all' in sys.argv or '--output-dir' in sys.argv:
        print("错误: 这是Apache日志导出工具，不支持 --all 和 --output-dir 参数")
        print("Windows系统日志请使用: python tools/export_windows_logs.py --all --output-dir logs")
        print("\nApache日志导出工具用法:")
        parser.print_help()
        return
    
    if args.find:
        found = find_apache_logs()
        if found:
            print("找到以下Apache日志文件:")
            for path in found:
                print(f"  {path}")
        else:
            print("未找到常见的Apache日志文件")
        return
    
    if not args.log_file:
        print("错误: 请指定 --log-file 参数")
        print("\n示例:")
        print("  python export_apache_logs.py --log-file /var/log/apache2/access.log --output apache_access.txt")
        print("  python export_apache_logs.py --log-file access.log --lines 10000 --output recent_logs.txt")
        print("  python export_apache_logs.py --find  # 查找日志文件")
        return
    
    export_apache_logs(
        args.log_file,
        args.output,
        lines=args.lines,
        start_date=args.start_date,
        end_date=args.end_date
    )


if __name__ == "__main__":
    main()

