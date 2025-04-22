#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from qfluentwidgets import FluentTranslator

# 导入主窗口
from src.views.main_window import MainWindow

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def signal_handler(sig, frame):
    """处理信号中断，如Ctrl+C"""
    if sig == signal.SIGINT:
        print("\nKeyboard interrupt received, shutting down...")
    elif sig == signal.SIGTERM:
        print("\nTermination signal received, shutting down...")
    elif sig == signal.SIGSEGV:
        print("\nSegmentation fault detected, attempting to save work...")
        # 尝试保存工作
        if 'w' in globals() and hasattr(w, 'editor') and hasattr(w.editor, 'document') and w.editor.document().isModified():
            try:
                # 尝试自动保存到临时文件
                import tempfile
                temp_dir = tempfile.gettempdir()
                recovery_file = os.path.join(temp_dir, "mgit_recovery.md")
                with open(recovery_file, 'w', encoding='utf-8') as f:
                    f.write(w.editor.toPlainText())
                print(f"Saved recovery file to: {recovery_file}")
            except:
                pass
    else:
        print(f"\nSignal {sig} received, shutting down...")
        
    QApplication.quit()
    sys.exit(0)

def setup_signal_handling():
    """设置信号处理，捕获常见的中断信号"""
    # SIGINT: 键盘中断（Ctrl+C）
    signal.signal(signal.SIGINT, signal_handler)
    
    # SIGTERM: 终止信号
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 在Windows系统上，有些信号可能不可用
    try:
        # SIGHUP: 终端挂起或控制进程终止
        signal.signal(signal.SIGHUP, signal_handler)
        
        # SIGSEGV: 段错误（可能导致崩溃，但我们尝试优雅处理）
        signal.signal(signal.SIGSEGV, signal_handler)
        
        # SIGABRT: 程序中止
        signal.signal(signal.SIGABRT, signal_handler)
        
        # SIGFPE: 浮点异常
        signal.signal(signal.SIGFPE, signal_handler)
    except (AttributeError, ValueError) as e:
        print(f"Warning: Some signal handlers could not be set: {e}")

def main():
    """ 应用程序入口 """
    # 设置应用信息
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("MGit")
    app.setOrganizationName("MGitTeam")
    
    # 设置翻译器
    translator = FluentTranslator()
    app.installTranslator(translator)
    
    # 启动主窗口
    w = MainWindow()
    w.show()
    
    # 设置信号处理
    setup_signal_handling()
    
    # 运行应用
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main() 