"""
工作流模型构建模块
从日志序列构建有限状态自动机（FSA）工作流
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque
from .parser import LogEntry
from .models import LogKeyModel


class WorkflowNode:
    """工作流节点"""
    
    def __init__(self, log_key: str, node_id: int = None):
        self.log_key = log_key
        self.node_id = node_id
        self.next_nodes: List['WorkflowNode'] = []
        self.is_loop = False
        self.loop_count = 0
        
    def __repr__(self):
        return f"WorkflowNode({self.log_key}, id={self.node_id})"
    
    def __eq__(self, other):
        if isinstance(other, WorkflowNode):
            return self.log_key == other.log_key
        return False
    
    def __hash__(self):
        return hash(self.log_key)


class WorkflowModel:
    """
    工作流模型（有限状态自动机）
    用于表示任务的执行路径
    """
    
    def __init__(self, task_name: str = "default"):
        self.task_name = task_name
        self.start_node: Optional[WorkflowNode] = None
        self.nodes: Dict[str, WorkflowNode] = {}  # log_key -> node
        self.node_counter = 0
        
    def add_node(self, log_key: str) -> WorkflowNode:
        """添加节点"""
        if log_key not in self.nodes:
            node = WorkflowNode(log_key, self.node_counter)
            self.node_counter += 1
            self.nodes[log_key] = node
            if self.start_node is None:
                self.start_node = node
        return self.nodes[log_key]
    
    def add_transition(self, from_key: str, to_key: str):
        """添加状态转换"""
        from_node = self.add_node(from_key)
        to_node = self.add_node(to_key)
        if to_node not in from_node.next_nodes:
            from_node.next_nodes.append(to_node)
    
    def detect_loops(self):
        """检测循环"""
        visited = set()
        path = []
        
        def dfs(node: WorkflowNode):
            if node in path:
                # 发现循环
                loop_start = path.index(node)
                loop_nodes = path[loop_start:]
                for n in loop_nodes:
                    n.is_loop = True
                    n.loop_count += 1
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for next_node in node.next_nodes:
                dfs(next_node)
            
            path.pop()
        
        if self.start_node:
            dfs(self.start_node)
    
    def get_execution_path(self, log_keys: List[str]) -> Tuple[List[str], Optional[str], Optional[List[str]]]:
        """
        获取执行路径和异常位置
        
        Args:
            log_keys: 日志键序列
            
        Returns:
            (执行路径, 异常位置描述, 期望的后续步骤)
        """
        if not self.start_node or not log_keys:
            return [], None, None
        
        path = []
        current = self.start_node
        expected_next = None
        
        for i, key in enumerate(log_keys):
            if key not in self.nodes:
                # 查找最相似的节点
                similar_key = self._find_similar_key(key)
                expected = list(current.next_nodes)[:3] if current and current.next_nodes else []
                expected_keys = [n.log_key[:50] for n in expected]  # 限制长度
                
                if similar_key:
                    return path, f"未知日志键: {key[:50]}... (位置 {i})，最相似的已知键: {similar_key[:50]}...", expected_keys
                else:
                    return path, f"未知日志键: {key[:50]}... (位置 {i})", expected_keys
            
            target_node = self.nodes[key]
            
            # 检查是否是有效的转换
            if current and target_node not in current.next_nodes:
                # 获取期望的下一步
                expected = list(current.next_nodes)[:3]
                expected_keys = [n.log_key[:50] for n in expected]  # 限制长度
                
                # 检查是否是循环的一部分
                if not current.is_loop:
                    return path, f"无效转换: {current.log_key[:50]}... -> {key[:50]}... (位置 {i})，期望的下一步: {expected_keys}", expected_keys
            
            path.append(key)
            current = target_node
            # 更新期望的下一步
            if current and current.next_nodes:
                expected_next = [n.log_key[:50] for n in list(current.next_nodes)[:3]]
        
        return path, None, expected_next
    
    def _find_similar_key(self, key: str) -> Optional[str]:
        """
        查找最相似的已知日志键（简单的字符串相似度）
        
        Args:
            key: 要查找的日志键
            
        Returns:
            最相似的已知键，如果没有则返回None
        """
        if not self.nodes:
            return None
        
        best_match = None
        best_score = 0.0
        
        # 简单的相似度计算：共同单词比例
        key_words = set(key.lower().split())
        
        for known_key in self.nodes.keys():
            known_words = set(known_key.lower().split())
            
            if not key_words or not known_words:
                continue
            
            # 计算Jaccard相似度
            intersection = len(key_words & known_words)
            union = len(key_words | known_words)
            score = intersection / union if union > 0 else 0.0
            
            if score > best_score:
                best_score = score
                best_match = known_key
        
        # 如果相似度太低，返回None
        if best_score < 0.3:
            return None
        
        return best_match
    
    def visualize(self) -> str:
        """可视化工作流（简单的文本表示）"""
        if not self.start_node:
            return "空工作流"
        
        lines = [f"工作流: {self.task_name}"]
        lines.append("=" * 50)
        
        visited = set()
        
        def traverse(node: WorkflowNode, indent: int = 0):
            if node in visited:
                return
            
            visited.add(node)
            prefix = "  " * indent
            loop_marker = " [循环]" if node.is_loop else ""
            lines.append(f"{prefix}{node.log_key}{loop_marker}")
            
            for next_node in node.next_nodes:
                traverse(next_node, indent + 1)
        
        traverse(self.start_node)
        return "\n".join(lines)


class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(self, log_key_model: Optional[LogKeyModel] = None):
        """
        初始化工作流构建器
        
        Args:
            log_key_model: 日志键模型（用于任务分离）
        """
        self.log_key_model = log_key_model
        
    def build_from_sequence(self, log_keys: List[str], 
                          task_name: str = "default") -> WorkflowModel:
        """
        从日志键序列构建工作流
        
        Args:
            log_keys: 日志键序列
            task_name: 任务名称
            
        Returns:
            WorkflowModel对象
        """
        workflow = WorkflowModel(task_name)
        
        if len(log_keys) < 2:
            return workflow
        
        # 构建状态转换
        for i in range(len(log_keys) - 1):
            from_key = log_keys[i]
            to_key = log_keys[i + 1]
            workflow.add_transition(from_key, to_key)
        
        # 检测循环
        workflow.detect_loops()
        
        return workflow
    
    def separate_tasks_using_lstm(self, log_entries: List[LogEntry], 
                                  window_size: int = 3) -> List[List[LogEntry]]:
        """
        使用LSTM模型分离多任务（基于论文4.2.1节）
        
        Args:
            log_entries: 日志条目列表
            window_size: 用于预测的窗口大小
            
        Returns:
            分离后的任务列表
        """
        if not self.log_key_model:
            raise ValueError("需要提供log_key_model")
        
        log_keys = [entry.log_key for entry in log_entries]
        tasks = []
        current_task = []
        history = deque(maxlen=window_size)
        
        for i, entry in enumerate(log_entries):
            if len(history) < window_size:
                # 历史不足，继续当前任务
                current_task.append(entry)
                history.append(entry.log_key)
                continue
            
            # 获取预测
            predictions = self.log_key_model.predict(list(history), top_k=5)
            predicted_keys = [key for key, _ in predictions]
            
            # 检查是否是发散点（divergence point）
            if entry.log_key not in predicted_keys:
                # 可能是新任务开始
                # 检查后续几个日志键是否形成新路径
                if i + 1 < len(log_entries):
                    next_key = log_entries[i + 1].log_key
                    # 简单启发式：如果下一个键也不在预测中，可能是新任务
                    if next_key not in predicted_keys:
                        # 保存当前任务
                        if current_task:
                            tasks.append(current_task)
                        # 开始新任务
                        current_task = [entry]
                        history.clear()
                        history.append(entry.log_key)
                        continue
            
            # 继续当前任务
            current_task.append(entry)
            history.append(entry.log_key)
        
        # 添加最后一个任务
        if current_task:
            tasks.append(current_task)
        
        return tasks
    
    def separate_tasks_using_clustering(self, log_entries: List[LogEntry],
                                       distance_threshold: float = 0.9,
                                       max_distance: int = 3) -> List[List[LogEntry]]:
        """
        使用基于密度的聚类方法分离任务（基于论文4.3.1节）
        
        Args:
            log_entries: 日志条目列表
            distance_threshold: 共现概率阈值
            max_distance: 最大距离
            
        Returns:
            分离后的任务列表
        """
        log_keys = [entry.log_key for entry in log_entries]
        
        # 构建共现矩阵
        cooccurrence_matrices = {}
        for d in range(1, max_distance + 1):
            cooccurrence_matrices[d] = self._build_cooccurrence_matrix(log_keys, d)
        
        # 使用聚类方法分离任务
        tasks = self._cluster_tasks(log_keys, cooccurrence_matrices, 
                                   distance_threshold, log_entries)
        
        return tasks
    
    def _build_cooccurrence_matrix(self, log_keys: List[str], 
                                   distance: int) -> Dict[Tuple[str, str], float]:
        """
        构建共现矩阵
        
        Args:
            log_keys: 日志键序列
            distance: 距离
            
        Returns:
            共现概率字典
        """
        from collections import Counter
        
        # 计算频率
        key_freq = Counter(log_keys)
        
        # 计算共现频率
        cooccur_freq = Counter()
        for i in range(len(log_keys)):
            for j in range(i + 1, min(i + distance + 1, len(log_keys))):
                pair = (log_keys[i], log_keys[j])
                cooccur_freq[pair] += 1
        
        # 计算共现概率
        cooccurrence = {}
        for (ki, kj), freq in cooccur_freq.items():
            if key_freq[ki] > 0:
                prob = freq / (distance * key_freq[ki])
                cooccurrence[(ki, kj)] = prob
        
        return cooccurrence
    
    def _cluster_tasks(self, log_keys: List[str],
                      cooccurrence_matrices: Dict[int, Dict[Tuple[str, str], float]],
                      threshold: float,
                      log_entries: List[LogEntry]) -> List[List[LogEntry]]:
        """
        使用聚类方法分离任务
        """
        tasks = []
        current_task = []
        used_indices = set()
        
        # 从第一个日志键开始
        for i, key in enumerate(log_keys):
            if i in used_indices:
                continue
            
            # 尝试扩展任务
            task_indices = [i]
            current_key = key
            
            while True:
                # 查找下一个可能的键
                next_key = None
                max_prob = 0
                
                # 在距离1的共现矩阵中查找
                if 1 in cooccurrence_matrices:
                    for (k1, k2), prob in cooccurrence_matrices[1].items():
                        if k1 == current_key and prob > threshold and prob > max_prob:
                            # 检查这个键是否在后续位置
                            for j in range(task_indices[-1] + 1, len(log_keys)):
                                if log_keys[j] == k2 and j not in used_indices:
                                    next_key = k2
                                    max_prob = prob
                                    task_indices.append(j)
                                    break
                            if next_key:
                                break
                
                if not next_key:
                    break
                
                current_key = next_key
            
            # 创建任务
            if len(task_indices) > 1:
                task = [log_entries[idx] for idx in task_indices]
                tasks.append(task)
                used_indices.update(task_indices)
        
        # 处理未分配的单节点
        for i, entry in enumerate(log_entries):
            if i not in used_indices:
                tasks.append([entry])
        
        return tasks
    
    def build_workflows_from_tasks(self, tasks: List[List[LogEntry]], 
                                   merge_similar: bool = True,
                                   similarity_threshold: float = 0.7) -> List[WorkflowModel]:
        """
        从分离的任务构建多个工作流
        
        Args:
            tasks: 分离后的任务列表
            merge_similar: 是否合并相似的工作流
            similarity_threshold: 相似度阈值（0-1之间）
            
        Returns:
            工作流模型列表
        """
        workflows = []
        
        for i, task in enumerate(tasks):
            log_keys = [entry.log_key for entry in task]
            workflow = self.build_from_sequence(log_keys, f"task_{i}")
            workflows.append(workflow)
        
        # 合并相似的工作流
        if merge_similar and len(workflows) > 1:
            workflows = self._merge_similar_workflows(workflows, similarity_threshold)
        
        return workflows
    
    def _merge_similar_workflows(self, workflows: List[WorkflowModel], 
                                 threshold: float = 0.7) -> List[WorkflowModel]:
        """
        合并相似的工作流
        
        Args:
            workflows: 工作流列表
            threshold: 相似度阈值
            
        Returns:
            合并后的工作流列表
        """
        if len(workflows) <= 1:
            return workflows
        
        # 计算工作流之间的相似度
        merged = []
        used = set()
        
        for i, wf1 in enumerate(workflows):
            if i in used:
                continue
            
            # 尝试与后续工作流合并
            merged_wf = wf1
            merged_indices = [i]
            
            for j, wf2 in enumerate(workflows[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = self._calculate_workflow_similarity(wf1, wf2)
                if similarity >= threshold:
                    # 合并工作流
                    merged_wf = self._merge_two_workflows(merged_wf, wf2)
                    merged_indices.append(j)
                    used.add(j)
            
            merged.append(merged_wf)
            used.add(i)
        
        # 更新工作流名称
        for idx, wf in enumerate(merged):
            wf.task_name = f"merged_workflow_{idx}"
        
        return merged
    
    def _calculate_workflow_similarity(self, wf1: WorkflowModel, wf2: WorkflowModel) -> float:
        """
        计算两个工作流的相似度
        
        Args:
            wf1: 工作流1
            wf2: 工作流2
            
        Returns:
            相似度（0-1之间）
        """
        if not wf1.start_node or not wf2.start_node:
            return 0.0
        
        # 计算节点集合的相似度
        keys1 = set(wf1.nodes.keys())
        keys2 = set(wf2.nodes.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        # Jaccard相似度：交集/并集
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        if union == 0:
            return 0.0
        
        node_similarity = intersection / union
        
        # 计算转换关系的相似度
        transitions1 = set()
        transitions2 = set()
        
        for node in wf1.nodes.values():
            for next_node in node.next_nodes:
                transitions1.add((node.log_key, next_node.log_key))
        
        for node in wf2.nodes.values():
            for next_node in node.next_nodes:
                transitions2.add((node.log_key, next_node.log_key))
        
        if transitions1 or transitions2:
            trans_intersection = len(transitions1 & transitions2)
            trans_union = len(transitions1 | transitions2)
            trans_similarity = trans_intersection / trans_union if trans_union > 0 else 0.0
        else:
            trans_similarity = 1.0  # 都没有转换，认为相似
        
        # 综合相似度（节点相似度权重0.4，转换相似度权重0.6）
        similarity = 0.4 * node_similarity + 0.6 * trans_similarity
        
        return similarity
    
    def _merge_two_workflows(self, wf1: WorkflowModel, wf2: WorkflowModel) -> WorkflowModel:
        """
        合并两个工作流
        
        Args:
            wf1: 工作流1
            wf2: 工作流2
            
        Returns:
            合并后的工作流
        """
        merged = WorkflowModel("merged")
        
        # 合并所有节点和转换
        for node in wf1.nodes.values():
            for next_node in node.next_nodes:
                merged.add_transition(node.log_key, next_node.log_key)
        
        for node in wf2.nodes.values():
            for next_node in node.next_nodes:
                merged.add_transition(node.log_key, next_node.log_key)
        
        # 检测循环
        merged.detect_loops()
        
        return merged

