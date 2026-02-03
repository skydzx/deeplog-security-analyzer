"""
工作流模型和增量学习示例
演示如何使用DeepLog构建工作流模型并进行异常诊断
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from deeplog import DeepLog
import glob
import random


def load_logs_from_directory(log_dir='logs', max_logs=2000):
    """
    从日志目录加载真实日志文件（用于工作流构建）
    
    Args:
        log_dir: 日志目录路径
        max_logs: 最大加载日志条数
    """
    log_lines = []
    log_files = []
                                                                                                                                                                                                                                                    
    # 查找所有日志文件
    for pattern in ['*.txt', '*.log']:
        # Windows日志
        for windows_pattern in ['windows_logs', 'local_windows_logs', '*windows*']:
            log_files.extend(glob.glob(os.path.join(log_dir, windows_pattern, pattern)))
        
        # Linux日志
        for linux_pattern in ['linux_logs', 'local_linux_logs', '*linux*']:
            log_files.extend(glob.glob(os.path.join(log_dir, linux_pattern, pattern)))
        
        # Apache日志
        log_files.extend(glob.glob(os.path.join(log_dir, '*apache*', pattern)))
        log_files.extend(glob.glob(os.path.join(log_dir, '*apache*', '**', pattern), recursive=True))
        
        # GitHub LogHub数据集
        log_files.extend(glob.glob(os.path.join(log_dir, 'github_loghub', '*.log')))
    
    # 去重
    log_files = list(set(log_files))
    
    if not log_files:
        print(f"警告: 在 {log_dir} 目录下未找到日志文件，使用示例数据")
        return generate_sample_logs()
    
    print(f"找到 {len(log_files)} 个日志文件")
    
    # 读取日志
    for filepath in log_files[:10]:  # 限制文件数量
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if len(log_lines) >= max_logs:
                        break
                    line = line.strip()
                    if line:
                        log_lines.append(line)
        except Exception as e:
            print(f"读取文件失败 {filepath}: {e}")
            continue
        
        if len(log_lines) >= max_logs:
            break
    
    return log_lines


def generate_sample_logs():
    """生成包含多个任务的示例日志"""
    logs = [
        # 任务1：创建VM
        "2024-01-01 10:00:00 INFO Starting VM creation",
        "2024-01-01 10:00:01 INFO Allocating resources",
        "2024-01-01 10:00:02 INFO Creating instance instance_id=vm001",
        "2024-01-01 10:00:03 INFO VM created successfully",
        # 任务2：删除VM
        "2024-01-01 10:00:04 INFO Starting VM deletion",
        "2024-01-01 10:00:05 INFO Destroying instance instance_id=vm001",
        "2024-01-01 10:00:06 INFO VM deleted successfully",
        # 任务3：创建VM（重复）
        "2024-01-01 10:00:07 INFO Starting VM creation",
        "2024-01-01 10:00:08 INFO Allocating resources",
        "2024-01-01 10:00:09 INFO Creating instance instance_id=vm002",
        "2024-01-01 10:00:10 INFO VM created successfully",
    ]
    return logs


def main():
    print("=" * 60)
    print("工作流模型和增量学习示例")
    print("=" * 60)
    
    # 1. 初始化并训练
    print("\n1. 初始化DeepLog...")
    deeplog = DeepLog(window_size=5, top_g=5, lstm_layers=2, lstm_units=64)
    
    print("\n2. 准备训练数据...")
    normal_logs = load_logs_from_directory('logs', max_logs=2000)
    print(f"训练日志数量: {len(normal_logs)}")
    
    print("\n3. 训练模型...")
    deeplog.train(normal_logs, epochs=5, batch_size=32)
    
    # 4. 构建工作流（使用LSTM方法）
    print("\n4. 构建工作流模型（LSTM方法）...")
    try:
        workflows_lstm = deeplog.build_workflows(normal_logs[:500], method="lstm")
        print(f"使用LSTM方法构建了 {len(workflows_lstm)} 个工作流")
        
        # 显示前3个工作流
        for i, workflow in enumerate(workflows_lstm[:3]):
            print(f"\n工作流 {i+1} ({workflow.task_name}):")
            print(workflow.visualize()[:500])  # 限制输出长度
            print("...")
    except Exception as e:
        print(f"LSTM工作流构建出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 构建工作流（使用聚类方法）
    print("\n5. 构建工作流模型（聚类方法）...")
    try:
        workflows_cluster = deeplog.build_workflows(normal_logs[:500], method="clustering")
        print(f"使用聚类方法构建了 {len(workflows_cluster)} 个工作流")
        
        # 显示前3个工作流
        for i, workflow in enumerate(workflows_cluster[:3]):
            print(f"\n工作流 {i+1} ({workflow.task_name}):")
            print(workflow.visualize()[:500])  # 限制输出长度
            print("...")
    except Exception as e:
        print(f"聚类工作流构建出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 测试增量学习
    print("\n6. 测试增量学习...")
    # 从训练数据中选择一个正常日志作为假阳性示例
    if normal_logs:
        false_positive_log = random.choice(normal_logs)
        print(f"添加假阳性样本: {false_positive_log[:80]}...")
        try:
            deeplog.update_model(false_positive_log, is_false_positive=True)
            print("模型已更新（如果缓冲区已满）")
        except Exception as e:
            print(f"增量学习出错: {e}")
    
    # 7. 异常诊断
    print("\n7. 测试异常诊断...")
    anomaly_logs = [
        "ERROR Critical system failure detected",
        "CRITICAL Database corruption occurred",
        "FATAL Application crashed with exception"
    ]
    
    for anomaly_log in anomaly_logs:
        try:
            is_anomaly, anomaly_type, workflow, diagnosis = deeplog.diagnose_anomaly(anomaly_log)
            print(f"\n日志: {anomaly_log}")
            print(f"  是否异常: {is_anomaly}")
            print(f"  异常类型: {anomaly_type}")
            if workflow:
                print(f"  相关工作流: {workflow.task_name}")
            if diagnosis:
                print(f"  诊断信息: {diagnosis}")
        except Exception as e:
            print(f"异常诊断出错: {e}")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

