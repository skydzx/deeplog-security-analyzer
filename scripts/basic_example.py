"""
DeepLog基础使用示例
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from deeplog import DeepLog
from datetime import datetime, timedelta
import re


def load_logs_from_directory(log_dir='logs', max_logs=5000):
    """
    从日志目录加载真实日志文件
    
    Args:
        log_dir: 日志目录路径
        max_logs: 最大加载日志条数
    """
    import glob
    import random
    
    log_lines = []
    log_files_by_type = {
        'windows': [],
        'linux': [],
        'apache': []
    }
    
    # 查找所有日志文件并按类型分类
    for pattern in ['*.txt', '*.log']:
        # Windows日志（支持多种命名方式）
        for windows_pattern in ['windows_logs', 'local_windows_logs', '*windows*']:
            windows_files = glob.glob(os.path.join(log_dir, windows_pattern, pattern))
            log_files_by_type['windows'].extend(windows_files)
        
        # Linux日志（支持多种命名方式）
        for linux_pattern in ['linux_logs', 'local_linux_logs', '*linux*']:
            linux_files = glob.glob(os.path.join(log_dir, linux_pattern, pattern))
            log_files_by_type['linux'].extend(linux_files)
        
        # Apache日志（支持多种命名方式）
        apache_files = glob.glob(os.path.join(log_dir, '*apache*', pattern))
        apache_files.extend(glob.glob(os.path.join(log_dir, '*apache*', '**', pattern), recursive=True))
        log_files_by_type['apache'].extend(apache_files)
        
        # GitHub LogHub数据集
        github_files = glob.glob(os.path.join(log_dir, 'github_loghub', 'Windows_*.log'))
        log_files_by_type['windows'].extend(github_files)
        github_files = glob.glob(os.path.join(log_dir, 'github_loghub', 'Linux_*.log'))
        log_files_by_type['linux'].extend(github_files)
        github_files = glob.glob(os.path.join(log_dir, 'github_loghub', 'Apache_*.log'))
        log_files_by_type['apache'].extend(github_files)
    
    # 去重，避免重复添加文件
    for log_type in log_files_by_type:
        log_files_by_type[log_type] = list(set(log_files_by_type[log_type]))
    
    all_files = []
    for log_type, files in log_files_by_type.items():
        if files:
            all_files.extend(files)
            print(f"  {log_type}: {len(files)} 个文件")
    
    if not all_files:
        print(f"警告: 在 {log_dir} 目录下未找到日志文件")
        print("使用示例数据...")
        return generate_sample_logs()
    
    print(f"找到 {len(all_files)} 个日志文件:")
    
    # 均匀地从各类日志中读取，确保多样性
    logs_by_type = {'windows': [], 'linux': [], 'apache': []}
    logs_per_type = max_logs // 3  # 每类日志分配大致相等的数量
    
    for log_type, files in log_files_by_type.items():
        if not files:
            continue
        for filepath in files:
            if len(logs_by_type[log_type]) >= logs_per_type:
                break
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if len(logs_by_type[log_type]) >= logs_per_type:
                            break
                        line = line.strip()
                        if line:
                            logs_by_type[log_type].append(line)
            except Exception as e:
                print(f"读取文件失败 {filepath}: {e}")
                continue
    
    # 合并所有日志
    for logs in logs_by_type.values():
        log_lines.extend(logs)
    
    # 如果总数不足，随机打乱
    if len(log_lines) < max_logs:
        random.shuffle(log_lines)
    else:
        log_lines = log_lines[:max_logs]
        random.shuffle(log_lines)
    
    return log_lines


def generate_sample_logs():
    """生成示例日志数据（当没有真实日志时使用）"""
    logs = [
        "2024-01-01 10:00:00 INFO Starting application",
        "2024-01-01 10:00:01 INFO Connected to database",
        "2024-01-01 10:00:02 INFO User login successful user_id=12345",
        "2024-01-01 10:00:03 INFO Processing request request_id=req001",
        "2024-01-01 10:00:04 INFO Request completed in 0.5 seconds",
    ] * 10  # 重复以增加数据量
    return logs


def main():
    print("=" * 60)
    print("DeepLog 基础使用示例")
    print("=" * 60)
    
    # 1. 初始化DeepLog
    print("\n1. 初始化DeepLog...")
    # 使用较小的window_size以便在小数据集上训练参数值模型
    deeplog = DeepLog(window_size=3, top_g=3, lstm_layers=1, lstm_units=32)
    
    # 2. 准备训练数据（从真实日志文件加载）
    print("\n2. 准备训练数据...")
    normal_logs = load_logs_from_directory('logs', max_logs=5000)
    print(f"训练日志数量: {len(normal_logs)}")
    
    # 3. 训练模型
    print("\n3. 训练模型...")
    try:
        deeplog.train(
            normal_logs,
            train_key_model=True,
            train_param_models=True,
            epochs=5,
            batch_size=8
        )
        print("训练完成！")
    except Exception as e:
        print(f"训练出错: {e}")
        return
    
    # 4. 检测正常日志（从训练数据中选取，确保历史窗口足够）
    print("\n4. 检测正常日志（从训练数据中选取，包含不同类型）...")
    if len(normal_logs) > deeplog.window_size + 10:
        # 从不同位置选取，确保覆盖不同类型的日志
        test_indices = [
            deeplog.window_size + 10,
            len(normal_logs) // 2,
            len(normal_logs) - 10
        ]
        test_normal_logs = [normal_logs[i] for i in test_indices if i < len(normal_logs)]
    else:
        test_normal_logs = normal_logs[-3:] if len(normal_logs) >= 3 else normal_logs
    
    # 识别日志类型
    def identify_log_type(log_line):
        """识别日志类型"""
        # Windows事件日志特征（优先级最高，因为格式最明确）
        if ('EventID' in log_line or 
            re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4}', log_line) or
            'Event ID' in log_line or
            'EventName' in log_line or
            '脱机下级迁移' in log_line or
            '软件保护服务' in log_line):
            return "Windows"
        # Apache错误日志特征（格式：[星期 月 日 时:分:秒.微秒 年] [模块:级别] [pid 进程号:tid 线程号] 消息）
        elif (re.match(r'^\[(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d{4}\]', log_line) or
              re.match(r'^\[.*\]\s+\[.*:.*\]\s+\[pid\s+\d+:tid\s+\d+\]', log_line) or
              re.match(r'^\[.*\]\s+\[.*:.*\]\s+AH\d+:', log_line)):
            return "Apache"
        # Apache访问日志特征（IP地址开头或HTTP方法）
        elif (re.match(r'^\d+\.\d+\.\d+\.\d+', log_line) or
              re.match(r'\[.*\]\s+"(GET|POST|PUT|DELETE|HEAD|OPTIONS)', log_line) or
              ('GET ' in log_line and 'HTTP/' in log_line) or
              ('POST ' in log_line and 'HTTP/' in log_line)):
            return "Apache"
        # Linux系统日志特征（syslog格式：月 日 时:分:秒 主机名 服务:消息）
        elif (re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s+\d{2}:\d{2}:\d{2}', log_line) or
              re.match(r'^\w+\s+\d+\s+\d{2}:\d{2}:\d{2}', log_line)):
            # 进一步检查Linux特有的服务标识
            if ('kernel:' in log_line or 'systemd:' in log_line or 'su:' in log_line or 
                'sshd:' in log_line or 'auth:' in log_line or 'pam_' in log_line or
                'device ' in log_line or 'left promiscuous' in log_line):
                return "Linux"
            # 如果匹配syslog格式但没有明确标识，也认为是Linux
            return "Linux"
        return "未知"
    
    for log in test_normal_logs:
        is_anomaly, anomaly_type, details = deeplog.detect(log)
        status = "异常" if is_anomaly else "正常"
        log_type = identify_log_type(log)
        log_display = log[:80] + "..." if len(log) > 80 else log
        print(f"\n日志 [{log_type}]: {log_display}")
        print(f"  状态: {status}")
        if is_anomaly:
            print(f"  异常类型: {anomaly_type}")
            if details.get('predictions'):
                print(f"  预测的top-3日志键:")
                for i, (key, prob) in enumerate(details['predictions'][:3], 1):
                    # 限制显示长度
                    key_display = key[:60] + "..." if len(key) > 60 else key
                    print(f"    {i}. [{prob:.4f}] {key_display}")
    
    # 5. 检测异常日志（使用明显的异常模式）
    print("\n5. 检测异常日志...")
    anomaly_logs = [
        "ERROR Critical system failure detected",
        "CRITICAL Database corruption occurred", 
        "FATAL Application crashed with exception",
    ]
    
    for log in anomaly_logs:
        is_anomaly, anomaly_type, details = deeplog.detect(log)
        status = "异常" if is_anomaly else "正常"
        print(f"\n日志: {log}")
        print(f"  状态: {status}")
        if is_anomaly:
            print(f"  异常类型: {anomaly_type}")
            if details.get('predictions'):
                print(f"  预测的top-3日志键:")
                for i, (key, prob) in enumerate(details['predictions'][:3], 1):
                    # 限制显示长度
                    key_display = key[:60] + "..." if len(key) > 60 else key
                    print(f"    {i}. [{prob:.4f}] {key_display}")
    
    # 6. 保存模型
    print("\n6. 保存模型...")
    try:
        deeplog.save("models")
        print("模型已保存到 models/ 目录")
    except Exception as e:
        print(f"保存模型出错: {e}")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

