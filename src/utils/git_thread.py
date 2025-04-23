#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.logger import info, error, debug

class GitThread(QThread):
    """Git操作线程类，用于异步执行Git操作"""
    
    # 定义信号
    operationStarted = pyqtSignal(str)  # 操作开始信号，参数为操作名称
    operationFinished = pyqtSignal(bool, str, str)  # 操作完成信号，参数为：成功/失败，操作名称，结果/错误信息
    progressUpdate = pyqtSignal(int, str)  # 进度更新信号，参数为：进度百分比，描述
    
    def __init__(self, parent=None):
        super(GitThread, self).__init__(parent)
        self.operation = None     # 要执行的操作名称
        self.git_manager = None   # GitManager实例
        self.params = {}          # 操作参数
        
    def setup(self, operation, git_manager, **params):
        """设置要执行的操作和参数
        
        Args:
            operation: 操作名称，如'pull', 'push', 'fetch'等
            git_manager: GitManager实例
            **params: 传递给对应方法的参数
        """
        self.operation = operation
        self.git_manager = git_manager
        self.params = params
        
    def run(self):
        """执行Git操作的线程主函数"""
        if not self.operation or not self.git_manager:
            error("Git线程：未设置操作或GitManager")
            self.operationFinished.emit(False, "未知操作", "未设置操作或GitManager")
            return
            
        try:
            # 发送操作开始信号
            debug(f"Git线程：开始执行 {self.operation} 操作")
            self.operationStarted.emit(self.operation)
            
            # 根据操作类型执行不同的方法
            result = None
            if self.operation == 'pull':
                remote_name = self.params.get('remote_name', 'origin')
                branch = self.params.get('branch', None)
                self.git_manager.pull(remote_name, branch)
                result = f"已从 {remote_name} 成功拉取更新"
                
            elif self.operation == 'push':
                remote_name = self.params.get('remote_name', 'origin')
                branch = self.params.get('branch', None)
                set_upstream = self.params.get('set_upstream', False)
                self.git_manager.push(remote_name, branch, set_upstream)
                result = f"已成功推送至 {remote_name}"
                
            elif self.operation == 'fetch':
                remote_name = self.params.get('remote_name', 'origin')
                self.git_manager.fetch(remote_name)
                result = f"已从 {remote_name} 获取最新更改"
                
            elif self.operation == 'commit':
                file_paths = self.params.get('file_paths', [])
                message = self.params.get('message', '提交更改')
                self.git_manager.commit(file_paths, message)
                result = f"已成功提交更改: {message}"
                
            elif self.operation == 'sync':
                remote_name = self.params.get('remote_name', 'origin')
                branch = self.params.get('branch', None)
                self.git_manager.syncWithRemote(remote_name, branch)
                result = f"已与 {remote_name} 同步完成"
                
            elif self.operation == 'init':
                path = self.params.get('path')
                initial_branch = self.params.get('initial_branch', 'main')
                result = self.git_manager.initRepository(path, initial_branch)
                result = f"已在 {path} 初始化仓库"
                
            elif self.operation == 'clone':
                url = self.params.get('url')
                target_path = self.params.get('target_path')
                branch = self.params.get('branch')
                depth = self.params.get('depth')
                recursive = self.params.get('recursive', False)
                result = self.git_manager.cloneRepository(url, target_path, branch, depth, recursive)
                result = f"已克隆仓库至 {target_path}"
                
            else:
                # 未知操作
                error(f"Git线程：未知操作 {self.operation}")
                self.operationFinished.emit(False, self.operation, f"未知的Git操作: {self.operation}")
                return
                
            # 操作成功完成
            info(f"Git线程：{self.operation} 操作成功完成")
            self.operationFinished.emit(True, self.operation, result)
            
        except Exception as e:
            # 操作失败
            error_msg = str(e)
            error(f"Git线程：{self.operation} 操作失败 - {error_msg}")
            self.operationFinished.emit(False, self.operation, error_msg) 