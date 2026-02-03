"""
并行处理模块
提供多进程/多线程的并行处理功能
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Iterator
import numpy as np
import gc
import os


class ParallelProcessor:
    """
    并行处理器
    支持多进程和多线程处理
    """

    def __init__(self, max_workers: int = None, use_processes: bool = True):
        """
        初始化并行处理器

        Args:
            max_workers: 最大工作进程/线程数
            use_processes: 是否使用进程（True）还是线程（False）
        """
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 4)  # 默认使用CPU核心数，最多4个

        self.max_workers = max_workers
        self.use_processes = use_processes

        # 根据可用资源调整工作进程数
        if use_processes and max_workers > mp.cpu_count():
            self.max_workers = mp.cpu_count()

    def process_batch(self, data: List[Any], process_func: Callable,
                     batch_size: int = 1000) -> List[Any]:
        """
        批处理数据

        Args:
            data: 输入数据
            process_func: 处理函数
            batch_size: 批大小

        Returns:
            处理结果
        """
        if self.max_workers == 1:
            # 单线程/进程处理
            return self._process_sequential(data, process_func, batch_size)

        # 多进程/线程处理
        return self._process_parallel(data, process_func, batch_size)

    def _process_sequential(self, data: List[Any], process_func: Callable,
                           batch_size: int) -> List[Any]:
        """顺序处理"""
        results = []

        for batch in self._batch_generator(data, batch_size):
            batch_results = process_func(batch)
            results.extend(batch_results)

            # 定期内存清理
            if len(results) % (batch_size * 10) == 0:
                gc.collect()

        return results

    def _process_parallel(self, data: List[Any], process_func: Callable,
                         batch_size: int) -> List[Any]:
        """并行处理"""
        results = []

        # 将数据分批
        batches = list(self._batch_generator(data, batch_size))

        # 使用适当的执行器
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            # 提交所有批处理任务
            future_to_batch = {
                executor.submit(process_func, batch): batch
                for batch in batches
            }

            # 收集结果
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as exc:
                    print(f'批处理任务生成异常: {exc}')
                    raise

        return results

    def _batch_generator(self, data: List[Any], batch_size: int) -> Iterator[List[Any]]:
        """批数据生成器"""
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]

    def process_parameter_models_parallel(self, key_to_entries: Dict[str, List],
                                         model_factory_func: Callable,
                                         max_models_per_worker: int = 5) -> Dict[str, Any]:
        """
        并行训练参数模型

        Args:
            key_to_entries: 日志键到条目的映射
            model_factory_func: 模型工厂函数
            max_models_per_worker: 每个工作进程的最大模型数

        Returns:
            训练好的模型字典
        """
        # 将任务分组给不同的工作进程
        task_groups = []
        current_group = {}
        current_count = 0

        for log_key, entries in key_to_entries.items():
            current_group[log_key] = entries
            current_count += 1

            if current_count >= max_models_per_worker:
                task_groups.append(current_group)
                current_group = {}
                current_count = 0

        if current_group:
            task_groups.append(current_group)

        def process_model_group(group):
            """处理一组模型"""
            results = {}
            for log_key, entries in group.items():
                try:
                    model = model_factory_func(log_key, entries)
                    if model is not None:
                        results[log_key] = model
                except Exception as e:
                    print(f"训练模型失败 {log_key}: {e}")
            return results

        # 并行处理
        all_results = self._process_parallel(task_groups, process_model_group, batch_size=1)

        # 合并结果
        final_results = {}
        for result_dict in all_results:
            final_results.update(result_dict)

        return final_results


class MemoryManager:
    """
    内存管理器
    提供内存监控和优化的功能
    """

    def __init__(self, memory_threshold_mb: int = 1000):
        """
        初始化内存管理器

        Args:
            memory_threshold_mb: 内存阈值（MB）
        """
        self.memory_threshold_mb = memory_threshold_mb

    def should_gc(self) -> bool:
        """
        检查是否应该进行垃圾回收

        Returns:
            是否需要GC
        """
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > self.memory_threshold_mb
        except ImportError:
            # 如果没有psutil，定期GC
            return True

    def force_gc_if_needed(self):
        """需要时强制垃圾回收"""
        if self.should_gc():
            gc.collect()

    def get_memory_usage(self) -> Dict[str, float]:
        """
        获取内存使用情况

        Returns:
            内存信息字典
        """
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()

            return {
                'rss_mb': mem_info.rss / 1024 / 1024,
                'vms_mb': mem_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}

    @staticmethod
    def optimize_array_operations():
        """优化数组操作"""
        # 设置NumPy内存对齐
        np.seterr(all='ignore')  # 忽略数值警告以提升性能


def create_optimized_processor(n_jobs: int = -1) -> ParallelProcessor:
    """
    创建优化配置的处理器

    Args:
        n_jobs: 作业数 (-1表示使用所有CPU核心)

    Returns:
        配置好的并行处理器
    """
    if n_jobs == -1:
        n_jobs = mp.cpu_count()
    elif n_jobs == 0:
        n_jobs = 1

    # 在内存有限的环境中使用线程而不是进程
    use_processes = n_jobs > 1 and mp.cpu_count() > 2

    return ParallelProcessor(max_workers=n_jobs, use_processes=use_processes)