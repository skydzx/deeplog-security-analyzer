#!/usr/bin/env python3
"""
DeepLog统一日志分析工具

功能：
1. 从文件加载日志数据
2. 训练异常检测模型
3. 分析日志并检测异常
4. 生成分析报告

使用方法：
python scripts/analyze_logs.py [选项]

选项：
--train FILE       使用指定文件训练模型
--analyze FILE     分析指定文件中的日志
--model DIR        指定模型保存/加载目录 (默认: models/)
--output FILE      指定输出报告文件 (默认: analysis_report.txt)
--help             显示帮助信息
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deeplog import DeepLog
from deeplog.exceptions import DeepLogError, ValidationError


class LogAnalyzer:
    """日志分析器"""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.deeplog = None
        self.is_trained = False

    def load_logs_from_file(self, filepath: str, max_lines: int = None) -> List[str]:
        """从文件加载日志"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        print(f"正在加载日志文件: {filepath}")

        logs = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if max_lines and i >= max_lines:
                    break
                line = line.strip()
                if line:  # 跳过空行
                    logs.append(line)

        print(f"成功加载 {len(logs)} 条日志")
        return logs

    def train_model(self, log_file: str, epochs: int = 5, batch_size: int = 32):
        """训练模型"""
        print("=" * 60)
        print("开始训练DeepLog模型")
        print("=" * 60)

        # 加载训练数据
        try:
            train_logs = self.load_logs_from_file(log_file, max_lines=2000)  # 限制训练数据量
            if len(train_logs) < 50:
                print("警告: 训练数据较少，可能影响模型效果")
        except Exception as e:
            print(f"加载训练数据失败: {e}")
            return False

        # 初始化模型
        try:
            print("\n初始化模型...")
            self.deeplog = DeepLog(
                window_size=5,      # 历史窗口大小
                top_g=3,           # 正常候选数
                lstm_layers=2,     # LSTM层数
                lstm_units=64      # LSTM单元数
            )
        except Exception as e:
            print(f"模型初始化失败: {e}")
            return False

        # 训练模型
        try:
            print("开始训练...")
            start_time = time.time()

            self.deeplog.train(
                train_logs,
                epochs=epochs,
                batch_size=batch_size
            )

            train_time = time.time() - start_time
            print(f"训练完成，耗时: {train_time:.2f}秒")
            self.is_trained = True

            # 保存模型
            try:
                self.model_dir.mkdir(exist_ok=True)
                self.deeplog.save(str(self.model_dir))
                print(f"模型已保存到: {self.model_dir}")
            except Exception as e:
                print(f"保存模型失败: {e}")

            return True

        except Exception as e:
            print(f"训练失败: {e}")
            return False

    def load_model(self) -> bool:
        """加载已训练的模型"""
        try:
            if not self.model_dir.exists():
                print(f"模型目录不存在: {self.model_dir}")
                return False

            print(f"正在加载模型: {self.model_dir}")
            self.deeplog = DeepLog()
            self.deeplog.load(str(self.model_dir))
            self.is_trained = True
            print("模型加载成功")
            return True
        except Exception as e:
            print(f"加载模型失败: {e}")
            return False

    def analyze_logs(self, log_file: str, output_file: str = None) -> Dict:
        """分析日志文件"""
        if not self.is_trained:
            print("错误: 模型未训练，请先训练模型或加载已训练的模型")
            return None

        print("=" * 60)
        print("开始分析日志")
        print("=" * 60)

        # 加载待分析的日志
        try:
            logs = self.load_logs_from_file(log_file, max_lines=1000)  # 限制分析数量
        except Exception as e:
            print(f"加载分析日志失败: {e}")
            return None

        # 分析日志
        results = {
            'total_logs': len(logs),
            'anomalies': [],
            'normal': [],
            'summary': {}
        }

        print("正在检测异常...")
        anomaly_count = 0

        for i, log in enumerate(logs):
            try:
                is_anomaly, anomaly_type, details = self.deeplog.detect(log)

                if is_anomaly:
                    anomaly_count += 1
                    results['anomalies'].append({
                        'line_number': i + 1,
                        'content': log,
                        'type': anomaly_type
                    })
                else:
                    results['normal'].append({
                        'line_number': i + 1,
                        'content': log
                    })

                # 显示进度
                if (i + 1) % 100 == 0:
                    print(f"已处理 {i + 1}/{len(logs)} 条日志...")

            except Exception as e:
                print(f"分析第 {i+1} 行日志时出错: {e}")
                continue

        # 生成统计信息
        results['summary'] = {
            'total_logs': len(logs),
            'anomaly_count': len(results['anomalies']),
            'normal_count': len(results['normal']),
            'anomaly_rate': (len(results['anomalies']) / len(logs)) * 100 if logs else 0
        }

        print("\n分析完成!")
        print(f"总日志数: {results['summary']['total_logs']}")
        print(f"异常日志: {results['summary']['anomaly_count']}")
        print(f"正常日志: {results['summary']['normal_count']}")
        print(".1f")
        # 保存报告
        if output_file:
            self.save_report(results, output_file)

        return results

    def save_report(self, results: Dict, output_file: str):
        """保存分析报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("DeepLog日志分析报告\n")
                f.write("=" * 50 + "\n\n")

                # 统计信息
                summary = results['summary']
                f.write("统计信息:\n")
                f.write("-" * 30 + "\n")
                f.write(f"总日志数: {summary['total_logs']}\n")
                f.write(f"异常日志: {summary['anomaly_count']}\n")
                f.write(f"正常日志: {summary['normal_count']}\n")
                f.write(".1f")
                f.write("\n")

                # 异常日志详情
                if results['anomalies']:
                    f.write("异常日志详情:\n")
                    f.write("-" * 30 + "\n")
                    for anomaly in results['anomalies'][:50]:  # 只显示前50个
                        f.write(f"行 {anomaly['line_number']}: {anomaly['content']}\n")
                        f.write(f"  类型: {anomaly['type']}\n")
                        f.write("\n")

                    # 显示所有异常日志，不再限制数量

                else:
                    f.write("未发现异常日志\n")

            print(f"报告已保存到: {output_file}")

        except Exception as e:
            print(f"保存报告失败: {e}")

    def interactive_analysis(self):
        """交互式分析"""
        if not self.is_trained:
            print("请先训练模型或加载已保存的模型")
            return

        print("\n进入交互式分析模式")
        print("输入日志消息进行分析，输入 'quit' 退出")

        while True:
            try:
                user_input = input("\n请输入日志: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                if not user_input:
                    continue

                is_anomaly, anomaly_type, details = self.deeplog.detect(user_input)

                print(f"日志: {user_input}")
                if is_anomaly:
                    print("结果: 异常日志")
                    print(f"类型: {anomaly_type}")
                else:
                    print("结果: 正常日志")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"分析出错: {e}")


def main():
    parser = argparse.ArgumentParser(description="DeepLog日志分析工具")
    parser.add_argument('--train', help='训练模型的数据文件')
    parser.add_argument('--analyze', help='要分析的日志文件')
    parser.add_argument('--model', default='models', help='模型目录 (默认: models/)')
    parser.add_argument('--output', help='输出报告文件')
    parser.add_argument('--interactive', action='store_true', help='进入交互式分析模式')

    args = parser.parse_args()

    # 创建分析器
    analyzer = LogAnalyzer(args.model)

    # 如果指定了训练文件，先训练模型
    if args.train:
        if not analyzer.train_model(args.train):
            print("训练失败")
            return 1

    # 如果没有训练文件，尝试加载现有模型
    elif not analyzer.load_model():
        print("未找到已训练的模型，请使用 --train 参数指定训练数据")
        return 1

    # 分析日志
    if args.analyze:
        results = analyzer.analyze_logs(args.analyze, args.output)
        if results is None:
            return 1

    # 交互式分析
    if args.interactive or (not args.analyze and not args.train):
        analyzer.interactive_analysis()

    return 0


if __name__ == "__main__":
    sys.exit(main())