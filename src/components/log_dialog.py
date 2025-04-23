#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QTextEdit, QFileDialog, QMessageBox,
                           QTabWidget, QWidget, QListWidget, QListWidgetItem,
                           QFormLayout, QComboBox, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QDate, QTime
from PyQt5.QtGui import QIcon, QTextCursor
from qfluentwidgets import (PrimaryPushButton, InfoBar, InfoBarPosition, 
                          FluentIcon, ComboBox, ToolTipFilter)

from src.utils.logger import (get_log_file_path, get_log_dir, export_log, 
                            get_all_log_files, get_recent_logs, info, show_error_message)

class LogDialog(QDialog):
    """日志查看和导出对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("日志管理")
        self.resize(800, 600)
        
        # 主布局
        mainLayout = QVBoxLayout(self)
        
        # 日志信息区
        infoLayout = QHBoxLayout()
        self.logPathLabel = QLabel(f"日志文件: {get_log_file_path()}")
        self.refreshButton = QPushButton("刷新")
        self.refreshButton.clicked.connect(self.refreshLogContent)
        
        infoLayout.addWidget(self.logPathLabel)
        infoLayout.addStretch(1)
        infoLayout.addWidget(self.refreshButton)
        
        mainLayout.addLayout(infoLayout)
        
        # 日志内容区域
        self.logTextEdit = QTextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setLineWrapMode(QTextEdit.NoWrap)  # 禁用自动换行
        mainLayout.addWidget(self.logTextEdit)
        
        # 筛选区域
        filterLayout = QHBoxLayout()
        
        # 日志级别过滤
        filterLayout.addWidget(QLabel("筛选级别:"))
        self.levelCombo = ComboBox()
        self.levelCombo.addItems(["全部", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.levelCombo.currentTextChanged.connect(self.applyFilter)
        filterLayout.addWidget(self.levelCombo)
        
        # 关键词过滤
        filterLayout.addWidget(QLabel("关键词:"))
        self.keywordEdit = QTextEdit()
        self.keywordEdit.setMaximumHeight(28)
        self.keywordEdit.textChanged.connect(self.applyFilter)
        filterLayout.addWidget(self.keywordEdit)
        
        # 日期范围过滤
        filterLayout.addWidget(QLabel("日期:"))
        self.dateCombo = ComboBox()
        self.dateCombo.addItems(["全部时间", "今天", "昨天", "最近三天", "最近一周"])
        self.dateCombo.currentTextChanged.connect(self.applyFilter)
        filterLayout.addWidget(self.dateCombo)
        
        mainLayout.addLayout(filterLayout)
        
        # 按钮区域
        buttonLayout = QHBoxLayout()
        
        self.exportButton = PrimaryPushButton("导出日志")
        self.exportButton.clicked.connect(self.exportLog)
        
        self.clearFilterButton = QPushButton("清除筛选")
        self.clearFilterButton.clicked.connect(self.clearFilter)
        
        self.closeButton = QPushButton("关闭")
        self.closeButton.clicked.connect(self.reject)
        
        buttonLayout.addWidget(self.exportButton)
        buttonLayout.addWidget(self.clearFilterButton)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.closeButton)
        
        mainLayout.addLayout(buttonLayout)
        
        # 加载日志内容
        self.refreshLogContent()
        
    def refreshLogContent(self):
        """刷新日志内容"""
        self.logTextEdit.clear()
        
        try:
            # 获取最近日志内容
            log_content = get_recent_logs(1000)  # 获取最近1000行
            self.logTextEdit.setPlainText(log_content)
            
            # 滚动到底部
            cursor = self.logTextEdit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.logTextEdit.setTextCursor(cursor)
            
            # 记录原始内容用于筛选
            self.original_content = log_content
            
            # 应用当前筛选
            self.applyFilter()
            
        except Exception as e:
            self.logTextEdit.setPlainText(f"读取日志失败: {str(e)}")
            
    def applyFilter(self):
        """应用筛选条件"""
        if not hasattr(self, 'original_content'):
            return
            
        # 获取筛选条件
        level = self.levelCombo.currentText()
        keyword = self.keywordEdit.toPlainText().strip()
        date_range = self.dateCombo.currentText()
        
        # 如果所有筛选都是默认值，则显示原始内容
        if level == "全部" and not keyword and date_range == "全部时间":
            self.logTextEdit.setPlainText(self.original_content)
            return
            
        # 分行处理
        filtered_lines = []
        for line in self.original_content.split('\n'):
            # 跳过空行
            if not line.strip():
                continue
                
            # 级别筛选
            if level != "全部" and level not in line:
                continue
                
            # 关键词筛选
            if keyword and keyword not in line:
                continue
                
            # 日期筛选
            if date_range != "全部时间":
                try:
                    # 提取日期部分 (假设格式为 "YYYY-MM-DD HH:MM:SS")
                    date_str = line.split(' - ')[0].strip()
                    log_date = QDateTime.fromString(date_str, "yyyy-MM-dd HH:mm:ss").date()
                    today = QDate.currentDate()
                    
                    if date_range == "今天" and log_date != today:
                        continue
                    elif date_range == "昨天" and log_date != today.addDays(-1):
                        continue
                    elif date_range == "最近三天" and log_date < today.addDays(-3):
                        continue
                    elif date_range == "最近一周" and log_date < today.addDays(-7):
                        continue
                except:
                    # 如果日期解析失败，保留该行
                    pass
                    
            # 通过所有筛选，添加该行
            filtered_lines.append(line)
            
        # 更新显示
        self.logTextEdit.setPlainText('\n'.join(filtered_lines))
        
    def clearFilter(self):
        """清除所有筛选条件"""
        self.levelCombo.setCurrentText("全部")
        self.keywordEdit.clear()
        self.dateCombo.setCurrentText("全部时间")
        
        # 显示原始内容
        if hasattr(self, 'original_content'):
            self.logTextEdit.setPlainText(self.original_content)
        
    def exportLog(self):
        """导出日志文件"""
        options = QFileDialog.Options()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"mgit_log_{timestamp}.log"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志文件", default_name,
            "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)", options=options
        )
        
        if file_path:
            # 检查是否应该导出筛选后的日志
            filtered_text = self.logTextEdit.toPlainText()
            if filtered_text != self.original_content and filtered_text.strip():
                reply = QMessageBox.question(
                    self, "导出确认", 
                    "是否导出筛选后的日志内容？\n选择\"否\"将导出完整日志文件。",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    # 导出筛选后的内容
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(filtered_text)
                        info(f"筛选后的日志导出成功: {file_path}")
                        InfoBar.success(
                            title="成功",
                            content=f"筛选后的日志已导出到: {file_path}",
                            parent=self,
                            position=InfoBarPosition.TOP,
                            duration=3000
                        )
                        return
                    except Exception as e:
                        show_error_message(self, "导出失败", "导出筛选日志失败", e)
                        return
            
            # 导出完整日志文件
            result = export_log(file_path)
            if result:
                InfoBar.success(
                    title="成功",
                    content=f"日志已导出到: {file_path}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
            else:
                show_error_message(self, "导出失败", "导出日志失败，请检查文件权限")
                
# 测试代码
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = LogDialog()
    dialog.exec_() 