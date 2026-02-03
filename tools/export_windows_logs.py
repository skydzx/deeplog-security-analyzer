"""
Windows系统日志导出工具
导出Windows事件日志为文本格式，便于DeepLog使用
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("警告: 未安装pywin32，将使用PowerShell方法")
    print("安装方法: pip install pywin32")


def export_with_powershell(log_name: str, output_file: str, max_events: int = 1000):
    """
    使用PowerShell导出日志
    
    Args:
        log_name: 日志名称（如 'System', 'Application', 'Security'）
        output_file: 输出文件路径
        max_events: 最大事件数
    """
    import subprocess
    
    ps_script = f'''
$events = Get-WinEvent -LogName "{log_name}" -MaxEvents {max_events} -ErrorAction SilentlyContinue
if ($events) {{
    $events | ForEach-Object {{
        $time = $_.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss.fff")
        $level = $_.LevelDisplayName
        $id = $_.Id
        $message = $_.Message -replace "`r`n", " " -replace "`n", " "
        "{0} {1} EventID={2} {3}" -f $time, $level, $id, $message
    }} | Out-File -FilePath "{output_file}" -Encoding UTF8
}} else {{
    Write-Host "无法读取日志: {log_name}"
}}
'''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"成功导出 {log_name} 日志到 {output_file}")
        else:
            print(f"导出失败: {result.stderr}")
    except Exception as e:
        print(f"执行PowerShell脚本失败: {e}")


def export_with_win32(log_name: str, output_file: str, max_events: int = 1000):
    """
    使用pywin32导出日志
    
    Args:
        log_name: 日志名称
        output_file: 输出文件路径
        max_events: 最大事件数
    """
    if not HAS_WIN32:
        return export_with_powershell(log_name, output_file, max_events)
    
    try:
        hand = win32evtlog.OpenEventLog(None, log_name)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        events = []
        count = 0
        
        while count < max_events:
            events_batch = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events_batch:
                break
            
            for event in events_batch:
                if count >= max_events:
                    break
                
                try:
                    time_str = event.TimeGenerated.Format()
                    # 获取事件级别
                    level_map = {
                        1: "CRITICAL",
                        2: "ERROR", 
                        3: "WARNING",
                        4: "INFO",
                        5: "VERBOSE"
                    }
                    level_name = level_map.get(event.EventType, "INFO")
                    
                    # 获取事件消息
                    try:
                        message = win32evtlogutil.SafeFormatMessage(event, log_name)
                    except:
                        message = f"Event ID: {event.EventID}"
                    
                    # 格式化日志行
                    log_line = f"{time_str} {level_name} EventID={event.EventID} {message}"
                    events.append(log_line)
                    count += 1
                except Exception as e:
                    # 如果单个事件处理失败，跳过
                    continue
        
        win32evtlog.CloseEventLog(hand)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(event + '\n')
        
        print(f"成功导出 {len(events)} 条 {log_name} 日志到 {output_file}")
        
    except Exception as e:
        print(f"导出 {log_name} 日志失败: {e}")
        # 回退到PowerShell方法
        export_with_powershell(log_name, output_file, max_events)


def export_all_logs(output_dir: str = "logs", max_events: int = 1000):
    """
    导出所有主要日志
    
    Args:
        output_dir: 输出目录
        max_events: 每个日志的最大事件数
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 主要日志类型
    log_types = ['System', 'Application', 'Security']
    
    for log_type in log_types:
        output_file = os.path.join(output_dir, f"windows_{log_type.lower()}_log.txt")
        print(f"\n导出 {log_type} 日志...")
        
        if HAS_WIN32:
            export_with_win32(log_type, output_file, max_events)
        else:
            export_with_powershell(log_type, output_file, max_events)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='导出Windows系统日志',
        epilog='注意: 这是Windows系统日志导出工具。Apache日志请使用 export_apache_logs.py'
    )
    parser.add_argument('--log', type=str, help='日志名称（System, Application, Security）')
    parser.add_argument('--output', type=str, default='windows_log.txt', help='输出文件路径')
    parser.add_argument('--max-events', type=int, default=1000, help='最大事件数')
    parser.add_argument('--all', action='store_true', help='导出所有主要日志')
    parser.add_argument('--output-dir', type=str, default='logs', help='输出目录（用于--all选项）')
    
    args = parser.parse_args()
    
    if args.all:
        export_all_logs(args.output_dir, args.max_events)
    elif args.log:
        if HAS_WIN32:
            export_with_win32(args.log, args.output, args.max_events)
        else:
            export_with_powershell(args.log, args.output, args.max_events)
    else:
        print("请指定 --log 或 --all 选项")
        print("\n示例:")
        print("  python export_windows_logs.py --log System --output system_log.txt")
        print("  python export_windows_logs.py --all --output-dir logs")


if __name__ == "__main__":
    main()

