"""
异步任务管理器
支持后台下载任务的队列管理、状态跟踪和进度监控
"""

import asyncio
import uuid
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import threading
from concurrent.futures import ThreadPoolExecutor
import logging


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    total_items: int = 0
    processed_items: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}  # 跟踪正在运行的任务
        self.is_running = False
        self.logger = self._setup_logger()
        
        # 线程池用于执行同步函数
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # WebSocket进度更新回调函数
        self.progress_callback = None
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('task_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            return
            
        self.is_running = True
        # 启动工作线程
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(f"worker-{i+1}"))
            self.worker_tasks.append(worker_task)
            
        self.logger.info(f"任务管理器已启动，工作线程数: {self.max_workers}")
    
    async def stop(self):
        """停止任务管理器"""
        self.is_running = False
        
        # 取消所有工作线程
        for task in self.worker_tasks:
            task.cancel()
        
        # 等待所有工作线程完成
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
        self.worker_tasks.clear()
        self.logger.info("任务管理器已停止")
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        self.logger.info(f"工作线程 {worker_name} 已启动")
        
        while self.is_running:
            try:
                self.logger.info(f"工作线程 {worker_name} 正在等待任务...")
                # 从队列获取任务（移除超时限制，直接等待任务）
                task_data = await self.task_queue.get()
                task_id, task_func, task_type, metadata = task_data
                
                # 更新任务状态为运行中
                task_info = self.tasks.get(task_id)
                if task_info:
                    # 检查任务是否已被取消
                    if task_info.status == TaskStatus.CANCELLED:
                        self.logger.info(f"任务 {task_id} 已被取消，跳过执行")
                        self.task_queue.task_done()
                        continue
                    
                    task_info.status = TaskStatus.RUNNING
                    task_info.started_at = time.time()
                
                self.logger.info(f"工作线程 {worker_name} 开始执行任务 {task_id}")
                
                # 创建任务执行任务
                task_coro = self._execute_task(task_id, task_func, task_info, metadata)
                task = asyncio.create_task(task_coro)
                self.running_tasks[task_id] = task
                
                try:
                    result = await task
                    
                    # 任务完成
                    if task_info:
                        task_info.status = TaskStatus.COMPLETED
                        task_info.completed_at = time.time()
                        # 只有在任务真正完成时才设置进度为100%
                        if task_info.status == TaskStatus.COMPLETED:
                            task_info.progress = 100.0
                            # 只有在任务真正完成时才传递100%的进度
                            progress_to_set = 100.0
                        else:
                            # 对于其他状态，保持当前进度
                            progress_to_set = task_info.progress
                        task_info.result = result
                        # 调用进度更新以触发WebSocket通知
                        self.update_task_progress(task_id, progress_to_set, 
                                                 task_info.processed_items, 
                                                 task_info.total_items)
                        
                except asyncio.CancelledError:
                    # 任务被取消
                    if task_info:
                        task_info.status = TaskStatus.CANCELLED
                        task_info.completed_at = time.time()
                        task_info.error_message = "任务已被用户取消"
                        # 对于取消的任务，保持当前进度
                        self.update_task_progress(task_id, task_info.progress, 
                                                 task_info.processed_items, 
                                                 task_info.total_items)
                    self.logger.info(f"任务 {task_id} 已被取消")
                except Exception as e:
                    # 任务失败
                    if task_info:
                        task_info.status = TaskStatus.FAILED
                        task_info.completed_at = time.time()
                        task_info.error_message = str(e)
                        # 调用进度更新以触发WebSocket通知
                        self.update_task_progress(task_id, task_info.progress, 
                                                 task_info.processed_items, 
                                                 task_info.total_items)
                    self.logger.error(f"任务 {task_id} 执行失败: {e}")
                    
                finally:
                    # 从运行任务字典中移除
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
                    self.task_queue.task_done()
                    self.logger.info(f"工作线程 {worker_name} 完成任务 {task_id}")
                    
            except asyncio.TimeoutError:
                # 队列为空，继续等待
                continue
            except asyncio.CancelledError:
                # 任务被取消
                break
            except Exception as e:
                self.logger.error(f"工作线程 {worker_name} 发生错误: {e}")
                await asyncio.sleep(1)  # 避免频繁错误
    
    def create_task(self, task_type: str, task_func: Callable, **metadata) -> str:
        """创建新任务
        
        Args:
            task_type: 任务类型（如：music_download, playlist_download, artist_download）
            task_func: 任务函数（可以是同步或异步函数）
            **metadata: 任务元数据
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=time.time(),
            metadata=metadata
        )
        
        # 保存任务信息
        self.tasks[task_id] = task_info
        
        # 将任务加入队列（使用同步方式）
        self._add_to_queue_sync(task_id, task_func, task_type, metadata)
        
        self.logger.info(f"创建任务 {task_id}，类型: {task_type}")
        return task_id
    
    def _add_to_queue_sync(self, task_id: str, task_func: Callable, task_type: str, metadata: Dict[str, Any]):
        """将任务添加到队列（同步版本）"""
        # 在事件循环中异步添加任务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，确保使用同一个事件循环
                # 直接在当前事件循环中创建任务
                asyncio.create_task(self._add_to_queue_async(task_id, task_func, task_type, metadata))
            else:
                # 如果事件循环没有运行，使用run_until_complete
                loop.run_until_complete(self._add_to_queue_async(task_id, task_func, task_type, metadata))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._add_to_queue_async(task_id, task_func, task_type, metadata))
    
    async def _add_to_queue_async(self, task_id: str, task_func: Callable, task_type: str, metadata: Dict[str, Any]):
        """将任务添加到队列（异步版本）"""
        await self.task_queue.put((task_id, task_func, task_type, metadata))
        self.logger.info(f"任务 {task_id} 已添加到队列，当前队列大小: {self.task_queue.qsize()}")
    
    async def _execute_task(self, task_id: str, task_func: Callable, task_info: Optional[TaskInfo], metadata: Dict[str, Any]):
        """执行任务"""
        # 执行任务，添加task_id参数
        task_metadata = metadata.copy()
        task_metadata['task_id'] = task_id
        
        if asyncio.iscoroutinefunction(task_func):
            # 异步函数
            result = await task_func(**task_metadata)
        else:
            # 同步函数，在线程池中执行
            import functools
            # 使用functools.partial包装函数调用
            func_call = functools.partial(task_func, **task_metadata)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.thread_pool, func_call
            )
        
        return result
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """获取所有任务信息"""
        return list(self.tasks.values())
    
    def clear_cancelled_tasks(self) -> Dict[str, Any]:
        """清理已取消的任务
        
        Returns:
            清理结果，包含清理的任务数量和详细信息
        """
        try:
            # 找出所有已取消的任务
            cancelled_tasks = []
            for task_id, task_info in list(self.tasks.items()):
                if task_info.status == TaskStatus.CANCELLED:
                    cancelled_tasks.append(task_info)
            
            # 记录清理前的任务数量
            total_before = len(self.tasks)
            
            # 从任务字典中移除已取消的任务
            for task_info in cancelled_tasks:
                if task_info.task_id in self.tasks:
                    del self.tasks[task_info.task_id]
            
            # 记录清理后的任务数量
            total_after = len(self.tasks)
            cleared_count = total_before - total_after
            
            # 构建清理结果
            result = {
                'success': True,
                'cleared_count': cleared_count,
                'total_before': total_before,
                'total_after': total_after,
                'cleared_tasks': [
                    {
                        'task_id': task.task_id,
                        'task_type': task.task_type,
                        'created_at': task.created_at,
                        'cancelled_at': task.completed_at
                    }
                    for task in cancelled_tasks
                ]
            }
            
            self.logger.info(f"清理已取消任务完成: 清理了 {cleared_count} 个任务")
            return result
            
        except Exception as e:
            self.logger.error(f"清理已取消任务失败: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'cleared_count': 0,
                'total_before': len(self.tasks),
                'total_after': len(self.tasks),
                'cleared_tasks': []
            }
    
    def set_progress_callback(self, callback):
        """设置进度更新回调函数"""
        self.progress_callback = callback
    
    def update_task_progress(self, task_id: str, progress: float, processed_items: int = 0, total_items: int = 0):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比（0-100）
            processed_items: 已处理项目数
            total_items: 总项目数
        """
        self.logger.info(f"开始更新任务进度: {task_id}, 进度: {progress}%, 已处理: {processed_items}/{total_items}")
        task_info = self.tasks.get(task_id)
        if task_info:
            # 只有当任务状态是RUNNING或PENDING时才更新进度
            # 对于CANCELLED状态的任务，保持当前进度不变
            if task_info.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                task_info.progress = min(100.0, max(0.0, progress))
                task_info.processed_items = processed_items
                task_info.total_items = total_items
            else:
                # 对于已完成、失败或取消的任务，保持当前进度不变
                self.logger.info(f"任务 {task_id} 状态为 {task_info.status.value}，保持当前进度: {task_info.progress}%")
            
            # 如果进度达到100%且任务正在运行，自动标记为已完成
            if progress >= 100.0 and task_info.status == TaskStatus.RUNNING:
                task_info.status = TaskStatus.COMPLETED
                task_info.completed_at = time.time()
                self.logger.info(f"任务 {task_id} 进度达到100%，自动标记为已完成")
            
            # 如果任务已被取消，确保进度不会自动设置为100%
            if task_info.status == TaskStatus.CANCELLED and progress >= 100.0:
                # 保持当前进度，不自动标记为已完成
                self.logger.info(f"任务 {task_id} 已被取消，保持当前进度: {progress}%")
            
            # 调用进度更新回调函数
            if self.progress_callback:
                self.logger.info(f"准备调用进度更新回调函数: {task_id}")
                try:
                    self.progress_callback(task_id)
                    self.logger.info(f"进度更新回调函数调用成功: {task_id}")
                except Exception as e:
                    self.logger.error(f"进度更新回调函数执行失败: {e}")
            else:
                self.logger.warning(f"进度更新回调函数未设置，无法发送WebSocket更新: {task_id}")
        else:
            self.logger.warning(f"任务不存在，无法更新进度: {task_id}")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        task_info = self.tasks.get(task_id)
        if task_info and task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            # 如果任务正在运行，取消对应的asyncio任务
            if task_id in self.running_tasks:
                running_task = self.running_tasks[task_id]
                running_task.cancel()
                self.logger.info(f"已取消正在运行的任务 {task_id}")
            
            # 如果任务在队列中等待，尝试从队列中移除
            if task_info.status == TaskStatus.PENDING:
                self._remove_from_queue(task_id)
            
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = time.time()
            self.logger.info(f"任务 {task_id} 已取消")
            # 调用进度更新以触发WebSocket通知
            self.update_task_progress(task_id, task_info.progress, 
                                     task_info.processed_items, 
                                     task_info.total_items)
            return True
        return False
    
    def _remove_from_queue(self, task_id: str):
        """从队列中移除指定任务
        
        Args:
            task_id: 要移除的任务ID
        """
        # 由于asyncio.Queue不支持直接移除特定元素，我们需要重新构建队列
        # 创建一个临时队列，只保留未取消的任务
        temp_queue = asyncio.Queue()
        removed = False
        
        # 将队列中所有任务转移到临时队列，跳过要移除的任务
        while not self.task_queue.empty():
            try:
                task_data = self.task_queue.get_nowait()
                current_task_id, task_func, task_type, metadata = task_data
                
                if current_task_id == task_id:
                    # 找到要移除的任务，跳过它
                    self.logger.info(f"从队列中移除了任务 {task_id}")
                    removed = True
                    self.task_queue.task_done()
                else:
                    # 保留其他任务
                    temp_queue.put_nowait(task_data)
                    self.task_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # 将临时队列中的任务移回原队列
        while not temp_queue.empty():
            try:
                task_data = temp_queue.get_nowait()
                self.task_queue.put_nowait(task_data)
                temp_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        if not removed:
            self.logger.info(f"任务 {task_id} 不在队列中或已被移除")
    
    def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """清理已完成的任务（保留最近的任务）
        
        Args:
            max_age_seconds: 最大保留时间（秒）
        """
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task_info in self.tasks.items():
            if task_info.completed_at and (current_time - task_info.completed_at) > max_age_seconds:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            self.logger.info(f"清理了 {len(tasks_to_remove)} 个已完成的任务")


# 全局任务管理器实例
task_manager = TaskManager()


async def init_task_manager():
    """初始化任务管理器"""
    await task_manager.start()


async def shutdown_task_manager():
    """关闭任务管理器"""
    await task_manager.stop()
