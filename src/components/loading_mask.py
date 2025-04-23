#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QProgressBar, QFrame
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QPainter, QFont
from qfluentwidgets import SmoothScrollArea, isDarkTheme, FluentIcon, InfoBar, InfoBarPosition, SpinBox, ProgressRing

class LoadingMask(QWidget):
    """加载遮罩组件，用于在Git操作时虚化UI并显示提示"""
    
    def __init__(self, parent=None):
        super(LoadingMask, self).__init__(parent)
        
        # 设置无边框、透明背景的窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置最高层级，确保显示在所有元素之上
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 初始化UI
        self.initUI()
        
        # 隐藏窗口
        self.hide()
        
    def initUI(self):
        """初始化UI"""
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 创建提示面板
        self.tipPanel = QFrame(self)
        self.tipPanel.setObjectName("loadingTipPanel")
        self.tipPanel.setFixedSize(300, 150)  # 减小提示框尺寸
        
        # 设置样式
        self.tipPanel.setStyleSheet("""
            QFrame#loadingTipPanel {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 1px solid rgba(200, 200, 200, 0.5);
            }
        """)
        
        # 提示面板布局
        tipLayout = QVBoxLayout(self.tipPanel)
        tipLayout.setContentsMargins(15, 15, 15, 15)  # 减小内边距
        tipLayout.setSpacing(10)  # 减小间距
        tipLayout.setAlignment(Qt.AlignCenter)
        
        # 添加加载图标（使用ProgressRing）
        self.progressRing = ProgressRing(self)
        self.progressRing.setFixedSize(35, 35)  # 减小进度环尺寸
        tipLayout.addWidget(self.progressRing, 0, Qt.AlignCenter)
        
        # 添加操作标题标签
        self.titleLabel = QLabel(self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))  # 调整字体大小
        tipLayout.addWidget(self.titleLabel)
        
        # 添加操作描述标签
        self.descLabel = QLabel(self)
        self.descLabel.setAlignment(Qt.AlignCenter)
        self.descLabel.setFont(QFont("Microsoft YaHei", 9))  # 调整字体大小
        self.descLabel.setWordWrap(True)
        tipLayout.addWidget(self.descLabel)
        
        # 添加进度条
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setFixedHeight(5)
        self.progressBar.hide()  # 默认隐藏进度条
        tipLayout.addWidget(self.progressBar)
        
        # 将提示面板添加到主布局
        layout.addWidget(self.tipPanel, 0, Qt.AlignCenter)
        
    def paintEvent(self, event):
        """绘制背景遮罩"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置半透明背景
        bg_color = QColor(0, 0, 0, 120)  # 黑色，透明度120/255
        painter.fillRect(self.rect(), bg_color)
        
    def showLoading(self, title, description=""):
        """显示加载状态
        
        Args:
            title: 操作标题
            description: 操作描述
        """
        # 更新标题和描述
        self.titleLabel.setText(title)
        self.descLabel.setText(description)
        
        # 调整大小和位置
        if self.parent():
            self.resize(self.parent().size())
            self.move(0, 0)
            
            # 提升控件到顶层
            self.raise_()
            self.activateWindow()
        
        # 显示窗口
        self.show()
        self.progressRing.show()
        self.progressRing.setVisible(True)
        # 启动进度环动画，使用正确的API
        self.progressRing.resume()
        
    def hideLoading(self):
        """隐藏加载状态"""
        # 停止进度环动画，使用正确的API
        self.progressRing.pause()
        self.hide()
        
    def updateProgress(self, value, desc=None):
        """更新进度
        
        Args:
            value: 进度值（0-100）
            desc: 新的描述文本（可选）
        """
        if value >= 0:
            self.progressBar.show()
            self.progressBar.setValue(value)
            
        if desc:
            self.descLabel.setText(desc)
            
    def resizeEvent(self, event):
        """调整大小时，确保遮罩覆盖整个父窗口"""
        if self.parent():
            self.resize(self.parent().size())
        
        super(LoadingMask, self).resizeEvent(event) 