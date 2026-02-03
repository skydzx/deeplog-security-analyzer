"""
通用日志异常检测分析脚本
支持BGL格式日志和普通日志文件/目录
"""

import sys
import os
import glob
from typing import Dict, Tuple, List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from deeplog import DeepLog
from collections import Counter

def load_bgl_logs(filepath='logs/github_loghub/BGL_2k.log'):
    """加载BGL日志文件（带标签格式）"""
    logs = []
    labels = []  # 记录标签（-表示正常，其他可能是异常）
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # BGL日志格式：第一列是标签（-表示正常，其他如APPREAD可能是异常）
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                label = parts[0]
                log_content = parts[1]
                logs.append(log_content)
                labels.append(label)
            else:
                logs.append(line)
                labels.append('-')
    
    return logs, labels

def load_logs_from_directory(log_dir):
    """从目录加载所有日志文件"""
    logs = []
    log_files = []
    
    # 查找所有日志文件
    for pattern in ['*.txt', '*.log']:
        log_files.extend(glob.glob(os.path.join(log_dir, pattern)))
    
    if not log_files:
        print(f"警告: 在 {log_dir} 目录下未找到日志文件")
        return logs
    
    print(f"找到 {len(log_files)} 个日志文件:")
    for filepath in log_files:
        print(f"  - {os.path.basename(filepath)}")
    
    # 读取所有日志文件
    for filepath in log_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        logs.append(line)
        except Exception as e:
            print(f"读取文件失败 {filepath}: {e}")
            continue
    
    return logs


def analyze_logs(
    log_source=None,
    is_bgl_format=False,
    window_size=5,
    top_g=5,
    epochs=5,
    batch_size=32,
    max_train_samples=2000,
):
    """
    分析日志（支持BGL格式或普通日志文件/目录）
    
    Args:
        log_source: 日志文件路径或目录路径。如果为None，默认使用BGL日志
        is_bgl_format: 是否为BGL格式（带标签）
    """
    print("=" * 60)
    if is_bgl_format or (log_source and 'bgl' in log_source.lower()):
        print("BGL日志异常检测分析")
    else:
        print("日志异常检测分析")
    print("=" * 60)
    
    # 1. 加载日志
    print("\n1. 加载日志...")
    if log_source is None:
        # 默认使用BGL日志
        logs, labels = load_bgl_logs()
        is_bgl_format = True
    elif os.path.isdir(log_source):
        # 目录：加载目录下所有日志文件
        logs = load_logs_from_directory(log_source)
        labels = ['-'] * len(logs)  # 普通日志没有标签，全部标记为待检测
        is_bgl_format = False
    elif os.path.isfile(log_source):
        # 单个文件：尝试BGL格式，如果不是则按普通日志处理
        try:
            logs, labels = load_bgl_logs(log_source)
            is_bgl_format = True
        except:
            # 如果不是BGL格式，按普通日志处理
            logs = []
            with open(log_source, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        logs.append(line)
            labels = ['-'] * len(logs)
            is_bgl_format = False
    else:
        print(f"错误: 无法找到日志源 {log_source}")
        return
    
    print(f"   总日志数: {len(logs)}")
    
    if len(logs) == 0:
        print("   错误: 没有加载到任何日志")
        return
    
    # 统计标签分布（仅BGL格式）
    if is_bgl_format:
        label_counts = Counter(labels)
        print(f"   标签分布:")
        for label, count in label_counts.most_common():
            label_name = "正常" if label == '-' else f"异常({label})"
            print(f"     {label_name}: {count} 条")
    
    # 2. 分离正常和异常日志（用于训练和测试）
    if is_bgl_format:
        normal_logs = [log for log, label in zip(logs, labels) if label == '-']
        anomaly_logs = [log for log, label in zip(logs, labels) if label != '-']
    else:
        # 普通日志：全部作为待检测日志，使用前80%作为训练数据
        normal_logs = logs[:int(len(logs) * 0.8)]
        anomaly_logs = logs[int(len(logs) * 0.8):]  # 后20%用于测试
    
    print(f"\n   训练日志: {len(normal_logs)} 条")
    if is_bgl_format:
        print(f"   标注的异常日志: {len(anomaly_logs)} 条")
    else:
        print(f"   待检测日志: {len(anomaly_logs)} 条")
    
    if len(normal_logs) < 50:
        print("   警告: 训练日志数量太少，可能影响训练效果")
        if len(normal_logs) < 10:
            print("   错误: 训练日志数量不足，无法训练模型")
            return
    
    # 3. 初始化DeepLog
    print("\n2. 初始化DeepLog...")
    deeplog = DeepLog(window_size=window_size, top_g=top_g, lstm_layers=2, lstm_units=64)
    
    # 4. 训练模型（只用正常日志）
    print("\n3. 训练模型（使用正常日志）...")
    try:
        deeplog.train(
            normal_logs[:min(max_train_samples, len(normal_logs))],  # 最多用指定数量训练
            epochs=epochs,
            batch_size=batch_size
        )
        print("   训练完成！")
    except Exception as e:
        print(f"   训练出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 检测正常日志（验证模型）
    print("\n4. 检测正常日志（验证模型准确性）...")
    test_normal_logs = normal_logs[100:110] if len(normal_logs) > 110 else normal_logs[-10:]
    normal_detected_as_normal = 0
    normal_detected_as_anomaly = 0
    
    for log in test_normal_logs:
        is_anomaly, anomaly_type, details = deeplog.detect(log)
        if is_anomaly:
            normal_detected_as_anomaly += 1
        else:
            normal_detected_as_normal += 1
    
    print(f"   测试了 {len(test_normal_logs)} 条正常日志:")
    print(f"     正确识别为正常: {normal_detected_as_normal} 条")
    print(f"     误判为异常: {normal_detected_as_anomaly} 条")
    if len(test_normal_logs) > 0:
        accuracy = normal_detected_as_normal / len(test_normal_logs) * 100
        print(f"     准确率: {accuracy:.1f}%")
    
    # 6. 检测异常日志（不再做示例，全部输出到文件）
    print("\n5. 检测异常日志（查找问题）...")
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # 根据日志源生成输出文件名
    if log_source:
        base_name = os.path.basename(log_source).replace('.log', '').replace('.txt', '')
        if os.path.isdir(log_source):
            base_name = os.path.basename(log_source)
    else:
        base_name = "bgl"
    
    detected_path = os.path.join(output_dir, f"{base_name}_detected_anomalies.txt")
    missed_path = os.path.join(output_dir, f"{base_name}_missed_anomalies.txt")
    scanned_path = os.path.join(output_dir, f"{base_name}_scan_anomalies.txt")

    if len(anomaly_logs) > 0:
        detected_anomalies = []
        missed_anomalies = []
        
        # 检测全部异常日志（不再限制前50条）
        for log in anomaly_logs:
            is_anomaly, anomaly_type, details = deeplog.detect(log)
            if is_anomaly:
                detected_anomalies.append((log, anomaly_type, details))
            else:
                missed_anomalies.append(log)
        
        print(f"   检测了 {len(anomaly_logs)} 条异常日志:")
        print(f"     成功检测到: {len(detected_anomalies)} 条")
        print(f"     未检测到: {len(missed_anomalies)} 条")
        if len(anomaly_logs) > 0:
            detection_rate = len(detected_anomalies) / len(anomaly_logs) * 100
            print(f"     检测率: {detection_rate:.1f}%")
        
        # 写入全部检测到的异常
        with open(detected_path, "w", encoding="utf-8") as f:
            for log, anomaly_type, details in detected_anomalies:
                f.write(f"[{anomaly_type}] {log}\n")
        # 写入未检测到的异常
        with open(missed_path, "w", encoding="utf-8") as f:
            for log in missed_anomalies:
                f.write(f"{log}\n")

        # 终端仅展示前10条，避免刷屏
        if detected_anomalies:
            print("\n   检测到的异常详情（前10条，全部已写入文件）:")
            for i, (log, anomaly_type, details) in enumerate(detected_anomalies[:10], 1):
                log_display = log[:80] + "..." if len(log) > 80 else log
                print(f"\n   {i}. 异常类型: {anomaly_type}")
                print(f"      日志: {log_display}")
                if details.get('predictions'):
                    print(f"      预测的top-3日志键:")
                    for j, (key, prob) in enumerate(details['predictions'][:3], 1):
                        key_display = key[:60] + "..." if len(key) > 60 else key
                        print(f"        {j}. [{prob:.4f}] {key_display}")
        
        if missed_anomalies:
            print(f"\n   未检测到的异常共 {len(missed_anomalies)} 条，已写入 {missed_path}")
    else:
        print("   没有找到标注的异常日志")
    
    # 7. 分析所有日志，找出可能的异常（全量扫描，结果写文件）
    print("\n6. 扫描所有日志，查找可能的异常...")
    all_anomalies = []
    
    for i, log in enumerate(logs):
        is_anomaly, anomaly_type, details = deeplog.detect(log)
        if is_anomaly:
            all_anomalies.append((i+1, log, anomaly_type, details))
    
    print(f"   扫描了 {len(logs)} 条日志，发现 {len(all_anomalies)} 条可能的异常")
    
    # 写入全量扫描结果
    with open(scanned_path, "w", encoding="utf-8") as f:
        for line_num, log, anomaly_type, _ in all_anomalies:
            f.write(f"[Line {line_num}] [{anomaly_type}] {log}\n")
    
    if all_anomalies:
        print("\n   发现的异常（前10条，全部已写入文件）:")
        for i, (line_num, log, anomaly_type, details) in enumerate(all_anomalies[:10], 1):
            log_display = log[:70] + "..." if len(log) > 70 else log
            print(f"\n   {i}. 第 {line_num} 行 - 异常类型: {anomaly_type}")
            print(f"      日志: {log_display}")
    
    # 8. 统计异常类型
    print("\n7. 异常类型统计...")
    anomaly_types = Counter([atype for _, _, atype, _ in all_anomalies])
    for atype, count in anomaly_types.most_common():
        print(f"   {atype}: {count} 条")

    # 9. 扫描异常的结构化汇总（帮助定位“为什么都是执行路径异常”）
    if all_anomalies:
        print("\n8. 执行路径异常汇总（定位误报原因）...")

        vocab = getattr(getattr(deeplog, "log_key_model", None), "vocab", None) or {}

        exec_path_anoms = [(ln, raw, d) for (ln, raw, atype, d) in all_anomalies if atype == "执行路径异常"]
        unseen_count = 0
        empty_pred_count = 0
        log_key_counter = Counter()
        context_counter = Counter()

        for _, _, details in exec_path_anoms:
            log_key = details.get("log_key", "")
            if log_key:
                log_key_counter[log_key] += 1
                if vocab and log_key not in vocab:
                    unseen_count += 1
            preds = details.get("predictions") or []
            if not preds:
                empty_pred_count += 1
            # 用top-3预测键作为“当前上下文状态”的粗略签名，便于定位某些上下文总误报
            context_sig = " | ".join([k for (k, _) in preds[:3]]) if preds else "<no-predictions>"
            context_counter[context_sig] += 1

        exec_total = len(exec_path_anoms)
        print(f"   执行路径异常总数: {exec_total}")
        print(f"   其中未见过的log_key: {unseen_count} (占比 {unseen_count / exec_total * 100:.1f}%)")
        print(f"   其中predictions为空: {empty_pred_count} (占比 {empty_pred_count / exec_total * 100:.1f}%)")

        # 生成汇总文件，便于你快速判断“key是否被切得太碎/训练覆盖不足”
        summary_path = os.path.join(output_dir, f"{base_name}_scan_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"scan_total={len(logs)}\n")
            f.write(f"execution_path_anomalies={exec_total}\n")
            f.write(f"unseen_log_key={unseen_count}\n")
            f.write(f"empty_predictions={empty_pred_count}\n\n")

            f.write("Top log_keys (execution path anomalies)\n")
            for key, cnt in log_key_counter.most_common(30):
                unseen_flag = " (unseen)" if (vocab and key not in vocab) else ""
                f.write(f"{cnt}\t{key}{unseen_flag}\n")

            f.write("\nTop prediction-context signatures (top-3 predicted keys)\n")
            for sig, cnt in context_counter.most_common(30):
                f.write(f"{cnt}\t{sig}\n")

            f.write("\nSample anomalies (first 30)\n")
            for ln, raw, details in exec_path_anoms[:30]:
                f.write(f"[Line {ln}] {raw}\n")
                f.write(f"  log_key: {details.get('log_key')}\n")
                preds = details.get("predictions") or []
                if preds:
                    f.write("  top_pred:\n")
                    for k, p in preds[:5]:
                        f.write(f"    - {p:.6f}\t{k}\n")
                else:
                    f.write("  top_pred: <none>\n")
                f.write("\n")

        print(f"   已写入汇总报告: {summary_path}")
    
    print("\n9. 文件输出位置:")
    print(f"   检测到的异常详情: {detected_path}")
    print(f"   未检测到的异常:   {missed_path}")
    print(f"   全量扫描的异常:   {scanned_path}")
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)


def analyze_bgl_logs():
    """分析BGL日志（保持向后兼容）"""
    analyze_logs(is_bgl_format=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='日志异常检测分析')
    parser.add_argument('--log-source', type=str, default=None,
                        help='日志文件路径或目录路径（默认使用BGL日志）')
    parser.add_argument('--bgl', action='store_true',
                        help='强制使用BGL格式解析')
    parser.add_argument('--window-size', type=int, default=5,
                        help='序列窗口长度（默认5）')
    parser.add_argument('--top-g', type=int, default=5,
                        help='Top-G 预测阈值（默认5）')
    parser.add_argument('--epochs', type=int, default=5,
                        help='训练轮数（默认5）')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='训练批大小（默认32）')
    parser.add_argument('--max-train-samples', type=int, default=2000,
                        help='训练时使用的最大样本数（默认2000）')
    
    args = parser.parse_args()
    
    analyze_logs(
        log_source=args.log_source,
        is_bgl_format=args.bgl,
        window_size=args.window_size,
        top_g=args.top_g,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_train_samples=args.max_train_samples,
    )

