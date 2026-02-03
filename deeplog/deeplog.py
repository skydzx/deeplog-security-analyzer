"""
DeepLog主类
整合所有组件
"""

from typing import List, Optional, Dict, Tuple
from .parser import LogParser, LogEntry
from .trainer import DeepLogTrainer
from .detector import DeepLogDetector
from .models import LogKeyModel, ParameterValueModel
from .workflow import WorkflowBuilder, WorkflowModel
from .incremental_learner import IncrementalLearner
from .exceptions import (
    DeepLogError, ValidationError, ConfigurationError, FileSystemError,
    safe_execute, handle_error
)
import os


class DeepLog:
    """
    DeepLog主类
    提供统一的接口进行训练和检测
    """
    
    def __init__(self, window_size: int = 10, top_g: int = 5,
                 lstm_layers: int = 2, lstm_units: int = 64):
        """
        初始化DeepLog

        Args:
            window_size: 历史窗口大小
            top_g: top-g个候选键被视为正常
            lstm_layers: LSTM层数
            lstm_units: 每层LSTM单元数

        Raises:
            ConfigurationError: 参数配置无效
        """
        # 参数验证
        if not isinstance(window_size, int) or window_size <= 0:
            raise ConfigurationError(
                f"window_size必须是正整数，当前值: {window_size}",
                parameter="window_size",
                current_value=window_size,
                valid_range="正整数，通常3-20"
            )

        if not isinstance(top_g, int) or top_g <= 0:
            raise ConfigurationError(
                f"top_g必须是正整数，当前值: {top_g}",
                parameter="top_g",
                current_value=top_g,
                valid_range="正整数，通常1-10"
            )

        if not isinstance(lstm_layers, int) or lstm_layers <= 0:
            raise ConfigurationError(
                f"lstm_layers必须是正整数，当前值: {lstm_layers}",
                parameter="lstm_layers",
                current_value=lstm_layers,
                valid_range="正整数，通常1-3"
            )

        if not isinstance(lstm_units, int) or lstm_units <= 0:
            raise ConfigurationError(
                f"lstm_units必须是正整数，当前值: {lstm_units}",
                parameter="lstm_units",
                current_value=lstm_units,
                valid_range="正整数，通常32-512"
            )

        self.window_size = window_size
        self.top_g = top_g
        self.lstm_layers = lstm_layers
        self.lstm_units = lstm_units

        try:
            self.parser = LogParser()
            self.trainer = DeepLogTrainer(window_size, lstm_layers, lstm_units)
        except Exception as e:
            raise DeepLogError(
                f"初始化组件失败: {e}",
                error_code="INITIALIZATION_ERROR",
                suggestion="检查依赖项是否正确安装"
            )

        self.log_key_model: Optional[LogKeyModel] = None
        self.parameter_models: Dict[str, ParameterValueModel] = {}
        self.detector: Optional[DeepLogDetector] = None
        self.workflow_builder: Optional[WorkflowBuilder] = None
        self.incremental_learner: Optional[IncrementalLearner] = None
        self.workflows: List[WorkflowModel] = []
    
    def train(self, log_lines: List[str],
             timestamps: Optional[List] = None,
             train_key_model: bool = True,
             train_param_models: bool = True,
             epochs: int = 10,
             batch_size: int = 32):
        """
        训练DeepLog模型

        Args:
            log_lines: 正常日志行列表
            timestamps: 时间戳列表（可选）
            train_key_model: 是否训练日志键模型
            train_param_models: 是否训练参数值模型
            epochs: 训练轮数
            batch_size: 批次大小

        Raises:
            ValidationError: 输入数据无效
            TrainingError: 训练过程出错
        """
        # 输入验证
        if not isinstance(log_lines, list):
            raise ValidationError(
                f"log_lines必须是列表，当前类型: {type(log_lines)}",
                field="log_lines",
                expected_type="list"
            )

        if len(log_lines) == 0:
            raise ValidationError(
                "log_lines不能为空列表",
                field="log_lines"
            )

        if timestamps is not None:
            if not isinstance(timestamps, list):
                raise ValidationError(
                    f"timestamps必须是列表或None，当前类型: {type(timestamps)}",
                    field="timestamps",
                    expected_type="list or None"
                )
            if len(timestamps) != len(log_lines):
                raise ValidationError(
                    f"timestamps长度({len(timestamps)})必须与log_lines长度({len(log_lines)})相同",
                    field="timestamps"
                )

        # 解析日志
        try:
            log_entries = safe_execute(
                self.parser.parse_batch,
                log_lines, timestamps,
                error_context="解析日志数据"
            )
        except Exception as e:
            raise ParsingError(
                f"日志解析失败: {e}",
                suggestion="检查日志格式是否正确"
            )

        if len(log_entries) == 0:
            raise ValidationError(
                "没有有效的日志条目，请检查日志格式",
                field="log_lines",
                suggestion="确保日志行是非空的字符串"
            )

        # 训练日志键模型
        if train_key_model:
            print("训练日志键异常检测模型...")
            try:
                self.log_key_model = safe_execute(
                    self.trainer.train_log_key_model,
                    log_entries, epochs, batch_size,
                    error_context="训练日志键模型"
                )
                print(f"日志键模型训练完成，词汇表大小: {self.log_key_model.vocab_size}")
            except Exception as e:
                raise TrainingError(
                    f"日志键模型训练失败: {e}",
                    stage="log_key_training",
                    model_type="LogKeyModel"
                )

        # 训练参数值模型
        if train_param_models:
            print("训练参数值异常检测模型...")
            try:
                self.parameter_models = safe_execute(
                    self.trainer.train_parameter_models,
                    log_entries, epochs, batch_size,
                    error_context="训练参数值模型"
                )
                print(f"参数值模型训练完成，共{len(self.parameter_models)}个模型")
            except Exception as e:
                print(f"参数值模型训练跳过: {str(e)[:100]}...")
                print("提示: 参数值模型需要同一日志键有足够的重复出现（至少window_size+1次）")
                self.parameter_models = {}

        # 创建检测器
        if self.log_key_model:
            try:
                self.detector = DeepLogDetector(
                    self.log_key_model, self.parameter_models, self.top_g
                )

                # 初始化工作流构建器
                self.workflow_builder = WorkflowBuilder(self.log_key_model)

                # 初始化增量学习器
                self.incremental_learner = IncrementalLearner(
                    self.log_key_model, self.window_size
                )
            except Exception as e:
                raise DeepLogError(
                    f"创建检测器失败: {e}",
                    error_code="DETECTOR_INITIALIZATION_ERROR",
                    suggestion="检查模型是否正确训练"
                )
    
    def detect(self, log_line: str, timestamp=None) -> Tuple[bool, str, Dict]:
        """
        检测单条日志是否异常

        Args:
            log_line: 日志行
            timestamp: 时间戳（可选）

        Returns:
            (是否异常, 异常类型, 详细信息)

        Raises:
            ValidationError: 输入参数无效
            DeepLogError: 模型未训练或检测失败
        """
        if self.detector is None:
            raise DeepLogError(
                "模型未训练，请先调用train()方法",
                error_code="MODEL_NOT_TRAINED",
                suggestion="调用train()方法训练模型后再进行检测"
            )

        if not isinstance(log_line, str):
            raise ValidationError(
                f"log_line必须是字符串，当前类型: {type(log_line)}",
                field="log_line",
                expected_type="str"
            )

        if log_line.strip() == "":
            raise ValidationError(
                "log_line不能为空字符串",
                field="log_line"
            )

        # 解析日志
        try:
            log_entry = safe_execute(
                self.parser.parse,
                log_line, timestamp,
                error_context="解析检测日志"
            )
        except Exception as e:
            raise ParsingError(
                f"日志解析失败: {e}",
                line_content=log_line,
                suggestion="检查日志格式是否与训练数据一致"
            )

        # 检测异常
        try:
            return safe_execute(
                self.detector.detect,
                log_entry,
                error_context="异常检测"
            )
        except Exception as e:
            raise PredictionError(
                f"异常检测失败: {e}",
                model_type="DeepLogDetector"
            )
    
    def detect_batch(self, log_lines: List[str], 
                    timestamps: Optional[List] = None) -> List[Tuple[bool, str, Dict]]:
        """
        批量检测日志
        
        Args:
            log_lines: 日志行列表
            timestamps: 时间戳列表（可选）
            
        Returns:
            检测结果列表
        """
        results = []
        for i, line in enumerate(log_lines):
            timestamp = timestamps[i] if timestamps else None
            result = self.detect(line, timestamp)
            results.append(result)
        return results
    
    def update_model(self, log_line: str, is_false_positive: bool = False):
        """
        在线更新模型（增量学习）
        
        Args:
            log_line: 日志行
            is_false_positive: 是否为假阳性（正常但被误判为异常）
        """
        if self.incremental_learner is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        if is_false_positive:
            self.incremental_learner.add_false_positive(log_line)
            # 当缓冲区积累足够样本时自动更新
            if len(self.incremental_learner.update_buffer) >= self.incremental_learner.batch_size:
                self.incremental_learner.update_model(epochs=1)
    
    def build_workflows(self, log_lines: List[str], 
                      method: str = "lstm",
                      timestamps: Optional[List] = None,
                      merge_similar: bool = True,
                      similarity_threshold: float = 0.7) -> List[WorkflowModel]:
        """
        构建工作流模型
        
        Args:
            log_lines: 日志行列表
            method: 任务分离方法 ("lstm" 或 "clustering")
            timestamps: 时间戳列表（可选）
            merge_similar: 是否合并相似的工作流（默认True）
            similarity_threshold: 相似度阈值（0-1之间，默认0.7）
            
        Returns:
            工作流模型列表
        """
        if self.workflow_builder is None:
            raise ValueError("模型未训练，请先调用train()方法")
        
        # 解析日志
        log_entries = self.parser.parse_batch(log_lines, timestamps)
        
        # 分离任务
        if method == "lstm":
            tasks = self.workflow_builder.separate_tasks_using_lstm(log_entries, self.window_size)
        elif method == "clustering":
            tasks = self.workflow_builder.separate_tasks_using_clustering(log_entries)
        else:
            raise ValueError(f"未知的方法: {method}")
        
        # 构建工作流（自动合并相似的）
        self.workflows = self.workflow_builder.build_workflows_from_tasks(
            tasks, merge_similar=merge_similar, similarity_threshold=similarity_threshold
        )
        
        return self.workflows
    
    def diagnose_anomaly(self, log_line: str, 
                        timestamp=None) -> Tuple[bool, str, Optional[WorkflowModel], Optional[str]]:
        """
        诊断异常（使用工作流模型）
        
        Args:
            log_line: 日志行
            timestamp: 时间戳（可选）
            
        Returns:
            (是否异常, 异常类型, 相关工作流, 诊断信息)
        """
        # 先检测异常
        is_anomaly, anomaly_type, details = self.detect(log_line, timestamp)
        
        if not is_anomaly:
            return is_anomaly, anomaly_type, None, None
        
        # 解析日志
        entry = self.parser.parse(log_line, timestamp)
        
        if not self.workflows:
            return is_anomaly, anomaly_type, None, "未构建工作流模型，无法进行详细诊断"
        
        # 查找最相关的工作流（包含该日志键的工作流）
        best_workflow = None
        best_match = None
        best_error = None
        best_expected = None
        
        for workflow in self.workflows:
            path, error, expected = workflow.get_execution_path([entry.log_key])
            
            # 如果这个工作流包含该日志键，优先使用
            if entry.log_key in workflow.nodes:
                best_workflow = workflow
                best_error = error
                best_expected = expected
                break
            
            # 记录第一个有错误信息的工作流
            if error and best_error is None:
                best_workflow = workflow
                best_error = error
                best_expected = expected
        
        # 如果没找到包含该键的工作流，使用第一个
        if best_workflow is None:
            best_workflow = self.workflows[0]
            path, best_error, best_expected = best_workflow.get_execution_path([entry.log_key])
        
        # 构建详细的诊断信息
        diagnosis_parts = []
        
        if best_error:
            diagnosis_parts.append(best_error)
        
        if best_expected:
            diagnosis_parts.append(f"期望的后续步骤: {', '.join(best_expected)}")
        
        # 添加工作流信息
        if best_workflow:
            workflow_info = f"相关工作流: {best_workflow.task_name} (包含 {len(best_workflow.nodes)} 个步骤)"
            diagnosis_parts.append(workflow_info)
        
        diagnosis = " | ".join(diagnosis_parts) if diagnosis_parts else "工作流执行正常"
        
        return is_anomaly, anomaly_type, best_workflow, diagnosis
    
    def save(self, model_dir: str):
        """
        保存模型

        Args:
            model_dir: 模型保存目录

        Raises:
            FileSystemError: 保存失败
            DeepLogError: 没有可保存的模型
        """
        if not isinstance(model_dir, str):
            raise ValidationError(
                f"model_dir必须是字符串，当前类型: {type(model_dir)}",
                field="model_dir",
                expected_type="str"
            )

        if not self.log_key_model and not self.parameter_models:
            raise DeepLogError(
                "没有可保存的模型",
                error_code="NO_MODEL_TO_SAVE",
                suggestion="先训练模型后再保存"
            )

        try:
            os.makedirs(model_dir, exist_ok=True)
        except Exception as e:
            raise FileSystemError(
                f"创建模型目录失败: {e}",
                file_path=model_dir,
                operation="create_directory"
            )

        # 保存日志键模型
        if self.log_key_model:
            try:
                model_path = os.path.join(model_dir, 'log_key_model')
                safe_execute(
                    self.log_key_model.save,
                    model_path,
                    error_context=f"保存日志键模型到 {model_path}"
                )
            except Exception as e:
                raise FileSystemError(
                    f"保存日志键模型失败: {e}",
                    file_path=os.path.join(model_dir, 'log_key_model'),
                    operation="save"
                )

        # 保存参数值模型
        for log_key, model in self.parameter_models.items():
            try:
                # 清理日志键中的特殊字符作为文件名
                safe_key = "".join(c for c in log_key if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_key = safe_key.replace(' ', '_')[:50]  # 限制长度
                model_path = os.path.join(model_dir, f'param_model_{safe_key}')

                safe_execute(
                    model.save,
                    model_path,
                    error_context=f"保存参数模型 {log_key}"
                )
            except Exception as e:
                raise FileSystemError(
                    f"保存参数模型失败 ({log_key}): {e}",
                    file_path=os.path.join(model_dir, f'param_model_{safe_key}'),
                    operation="save"
                )

    def load(self, model_dir: str):
        """
        加载模型

        Args:
            model_dir: 模型目录

        Raises:
            FileSystemError: 加载失败
            ValidationError: 模型目录无效
        """
        if not isinstance(model_dir, str):
            raise ValidationError(
                f"model_dir必须是字符串，当前类型: {type(model_dir)}",
                field="model_dir",
                expected_type="str"
            )

        if not os.path.exists(model_dir):
            raise FileSystemError(
                f"模型目录不存在: {model_dir}",
                file_path=model_dir,
                operation="check_existence"
            )

        if not os.path.isdir(model_dir):
            raise ValidationError(
                f"model_dir必须是目录，当前是文件: {model_dir}",
                field="model_dir"
            )

        # 加载日志键模型
        log_key_path = os.path.join(model_dir, 'log_key_model')
        config_file = log_key_path + '.config.pkl'

        if os.path.exists(config_file):
            try:
                self.log_key_model = LogKeyModel(1, self.window_size, self.lstm_layers, self.lstm_units)
                safe_execute(
                    self.log_key_model.load,
                    log_key_path,
                    error_context=f"加载日志键模型从 {log_key_path}"
                )
            except Exception as e:
                raise FileSystemError(
                    f"加载日志键模型失败: {e}",
                    file_path=log_key_path,
                    operation="load"
                )

        # 加载参数值模型
        # 这里简化处理，实际应该保存模型列表
        # TODO: 改进模型加载逻辑

        # 创建检测器
        if self.log_key_model:
            try:
                self.detector = DeepLogDetector(
                    self.log_key_model, self.parameter_models, self.top_g
                )
            except Exception as e:
                raise DeepLogError(
                    f"创建检测器失败: {e}",
                    error_code="DETECTOR_CREATION_ERROR",
                    suggestion="检查加载的模型是否完整"
                )

