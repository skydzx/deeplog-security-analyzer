"""
评估模块
提供评估指标和对比功能
"""

from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import numpy as np


class Evaluator:
    """评估器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置统计"""
        self.true_positives = 0  # 真正例
        self.false_positives = 0  # 假正例
        self.true_negatives = 0  # 真负例
        self.false_negatives = 0  # 假负例
    
    def add_result(self, predicted: bool, actual: bool):
        """
        添加一个预测结果
        
        Args:
            predicted: 预测结果（True=异常，False=正常）
            actual: 实际结果（True=异常，False=正常）
        """
        if predicted and actual:
            self.true_positives += 1
        elif predicted and not actual:
            self.false_positives += 1
        elif not predicted and actual:
            self.false_negatives += 1
        else:
            self.true_negatives += 1
    
    def add_results(self, predictions: List[bool], actuals: List[bool]):
        """
        批量添加结果
        
        Args:
            predictions: 预测结果列表
            actuals: 实际结果列表
        """
        for pred, actual in zip(predictions, actuals):
            self.add_result(pred, actual)
    
    def precision(self) -> float:
        """精确率"""
        total_positive = self.true_positives + self.false_positives
        if total_positive == 0:
            return 0.0
        return self.true_positives / total_positive
    
    def recall(self) -> float:
        """召回率"""
        total_actual_positive = self.true_positives + self.false_negatives
        if total_actual_positive == 0:
            return 0.0
        return self.true_positives / total_actual_positive
    
    def f_measure(self) -> float:
        """F-measure (F1-score)"""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)
    
    def accuracy(self) -> float:
        """准确率"""
        total = (self.true_positives + self.false_positives + 
                self.true_negatives + self.false_negatives)
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    def get_metrics(self) -> Dict[str, float]:
        """获取所有指标"""
        return {
            'precision': self.precision(),
            'recall': self.recall(),
            'f_measure': self.f_measure(),
            'accuracy': self.accuracy(),
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives
        }
    
    def print_report(self):
        """打印评估报告"""
        metrics = self.get_metrics()
        print("\n" + "=" * 60)
        print("评估报告")
        print("=" * 60)
        print(f"精确率 (Precision): {metrics['precision']:.4f}")
        print(f"召回率 (Recall):    {metrics['recall']:.4f}")
        print(f"F-measure:          {metrics['f_measure']:.4f}")
        print(f"准确率 (Accuracy):  {metrics['accuracy']:.4f}")
        print("\n混淆矩阵:")
        print(f"  真正例 (TP): {metrics['true_positives']}")
        print(f"  假正例 (FP): {metrics['false_positives']}")
        print(f"  真负例 (TN): {metrics['true_negatives']}")
        print(f"  假负例 (FN): {metrics['false_negatives']}")
        print("=" * 60)


def evaluate_on_dataset(deeplog, log_lines: List[str], 
                        ground_truth: List[bool],
                        timestamps: Optional[List] = None) -> Dict[str, float]:
    """
    在数据集上评估DeepLog
    
    Args:
        deeplog: DeepLog实例
        log_lines: 日志行列表
        ground_truth: 真实标签列表（True=异常，False=正常）
        timestamps: 时间戳列表（可选）
        
    Returns:
        评估指标字典
    """
    evaluator = Evaluator()
    
    results = deeplog.detect_batch(log_lines, timestamps)
    predictions = [is_anomaly for is_anomaly, _, _ in results]
    
    evaluator.add_results(predictions, ground_truth)
    
    return evaluator.get_metrics()


def compare_methods(results: Dict[str, Dict[str, float]]):
    """
    对比不同方法的结果
    
    Args:
        results: 方法名到评估指标的映射
    """
    print("\n" + "=" * 80)
    print("方法对比")
    print("=" * 80)
    print(f"{'方法':<20} {'精确率':<12} {'召回率':<12} {'F-measure':<12} {'准确率':<12}")
    print("-" * 80)
    
    for method_name, metrics in results.items():
        print(f"{method_name:<20} "
              f"{metrics['precision']:<12.4f} "
              f"{metrics['recall']:<12.4f} "
              f"{metrics['f_measure']:<12.4f} "
              f"{metrics['accuracy']:<12.4f}")
    
    print("=" * 80)

