#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import time
import tempfile
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_log_dir():
    """获取日志目录，确保其存在"""
    try:
        # 首先尝试使用用户主目录
        home_dir = str(Path.home())
        log_dir = os.path.join(home_dir, '.mgit', 'logs')
    except Exception:
        # 如果无法获取主目录，使用临时目录
        log_dir = os.path.join(tempfile.gettempdir(), 'mgit', 'logs')
    
    # 确保目录存在
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            # 如果创建失败，回退到临时目录
            log_dir = os.path.join(tempfile.gettempdir(), 'mgit', 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
    
    return log_dir

class Logger:
    """应用日志记录器，提供统一的日志记录接口"""
    
    # 单例模式
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, app_name="MGit", log_level=logging.INFO):
        # 避免重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        self.app_name = app_name
        
        # 使用获取日志目录的函数
        self.log_dir = get_log_dir()
        
        # 设置日志文件路径
        self.log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}.log")
        
        # 创建日志记录器
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(log_level)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # 添加文件处理器（滚动日志，最多保留5个日志文件，每个最大5MB）
        file_handler = RotatingFileHandler(
            self.log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # 清除已有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # 记录启动日志
        self.logger.info(f"====== {self.app_name} 日志系统启动 ======")
        self.logger.info(f"日志文件路径: {self.log_file}")
    
    def debug(self, message):
        """记录调试级别日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录信息级别日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录警告级别日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录错误级别日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录严重级别日志"""
        self.logger.critical(message)
    
    def exception(self, message):
        """记录异常日志，包含堆栈信息"""
        self.logger.exception(message)
        
    def get_log_file_path(self):
        """获取当前日志文件路径"""
        return self.log_file
        
    def get_log_dir(self):
        """获取日志目录路径"""
        return self.log_dir
        
    def export_log(self, target_path=None):
        """导出日志文件到指定路径
        Args:
            target_path: 目标路径，如果为None则返回当前日志文件路径
        Returns:
            str: 导出的日志文件路径
        """
        if target_path is None:
            # 创建导出目录（如果需要）
            export_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if not os.path.exists(export_dir):
                export_dir = os.path.expanduser("~")
                
            # 生成唯一文件名，包含时间戳
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(export_dir, f"{self.app_name.lower()}_log_{timestamp}.log")
        
        try:
            import shutil
            # 复制当前日志文件到目标路径
            shutil.copy2(self.log_file, target_path)
            self.logger.info(f"日志导出成功: {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"日志导出失败: {str(e)}")
            return None
            
    def get_all_log_files(self):
        """获取所有日志文件路径列表
        Returns:
            list: 日志文件路径列表
        """
        log_files = []
        try:
            # 获取主日志文件
            if os.path.exists(self.log_file):
                log_files.append(self.log_file)
            
            # 获取备份日志文件
            base_name = os.path.basename(self.log_file)
            for i in range(1, 6):  # 默认最多5个备份
                backup_file = f"{self.log_file}.{i}"
                if os.path.exists(backup_file):
                    log_files.append(backup_file)
        except Exception as e:
            self.logger.error(f"获取日志文件列表失败: {str(e)}")
            
        return log_files
            
    def get_recent_logs(self, lines=100):
        """获取最近的日志内容
        Args:
            lines: 要读取的行数
        Returns:
            str: 日志内容
        """
        try:
            if not os.path.exists(self.log_file):
                return "日志文件不存在"
                
            # 使用 tail 方式读取最后N行
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 读取所有行并保留最后 lines 行
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"读取日志失败: {str(e)}"

# 创建全局日志记录器实例
log = Logger()

# 方便导入的别名
debug = log.debug
info = log.info
warning = log.warning
error = log.error
critical = log.critical
exception = log.exception

# 导出相关函数
get_log_file_path = log.get_log_file_path
get_log_dir = log.get_log_dir
export_log = log.export_log
get_all_log_files = log.get_all_log_files
get_recent_logs = log.get_recent_logs

# 设置全局异常处理器
def setup_exception_logging():
    """设置全局异常处理器，捕获未处理的异常并记录到日志"""
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        # 保留标准错误处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        # 记录到日志
        import traceback
        log_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log.critical(f"未捕获的异常:\n{log_message}")
    
    # 设置全局异常处理器
    sys.excepthook = handle_exception
    
def show_error_message(parent, title, message, e=None):
    """显示错误消息对话框并记录到日志
    
    Args:
        parent: 父窗口
        title: 错误标题
        message: 错误消息
        e: 异常对象（可选）
    """
    from PyQt5.QtWidgets import QMessageBox
    
    # 构建完整错误消息
    full_message = message
    if e:
        full_message = f"{message}: {str(e)}"
    
    # 记录到日志
    log.error(f"UI错误 - {title}: {full_message}")
    
    # 显示对话框
    QMessageBox.critical(parent, title, full_message)
    
    return full_message 