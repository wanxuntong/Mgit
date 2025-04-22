#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QFileSystemModel,
                           QMenu, QAction, QInputDialog, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QModelIndex
from PyQt5.QtGui import QIcon, QCursor
from qfluentwidgets import (PushButton, SearchLineEdit, FluentIcon, InfoBar,
                          InfoBarPosition, ToolButton, PrimaryToolButton)

class FileExplorer(QWidget):
    """ 文件浏览器组件 """
    
    # 信号
    fileSelected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建搜索框
        self.searchBox = SearchLineEdit(self)
        self.searchBox.setPlaceholderText("搜索文件...")
        self.searchBox.textChanged.connect(self.filterFiles)
        
        # 创建工具栏
        toolbarLayout = QVBoxLayout()
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        
        # 添加新建文件按钮
        self.newFileBtn = PrimaryToolButton(FluentIcon.ADD)
        self.newFileBtn.setToolTip("新建文件")
        self.newFileBtn.clicked.connect(self.createNewFile)
        
        # 添加刷新按钮
        self.refreshBtn = PrimaryToolButton(FluentIcon.SYNC)
        self.refreshBtn.setToolTip("刷新")
        self.refreshBtn.clicked.connect(self.refreshFiles)
        
        # 布置工具栏按钮，改为横向布局
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.newFileBtn)
        btnLayout.addWidget(self.refreshBtn)
        btnLayout.setSpacing(4)
        btnLayout.addStretch(1)  # 添加弹性空间，使按钮靠左对齐
        toolbarLayout.addLayout(btnLayout)
        
        # 创建文件系统模型
        self.fileModel = QFileSystemModel()
        self.fileModel.setNameFilters(["*.md", "*.markdown"])
        self.fileModel.setNameFilterDisables(False)
        
        # 创建树视图
        self.treeView = QTreeView()
        self.treeView.setModel(self.fileModel)
        self.treeView.setHeaderHidden(True)
        self.treeView.hideColumn(1)  # 隐藏大小列
        self.treeView.hideColumn(2)  # 隐藏类型列
        self.treeView.hideColumn(3)  # 隐藏修改日期列
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.showContextMenu)
        self.treeView.doubleClicked.connect(self.onFileDoubleClicked)
        
        # 添加组件到布局
        layout.addWidget(self.searchBox)
        layout.addLayout(toolbarLayout)
        layout.addWidget(self.treeView)
        
        # 当前根路径
        self.rootPath = ""
        
    def setRootPath(self, path):
        """ 设置根路径 """
        if not path or not os.path.exists(path):
            return
            
        self.rootPath = path
        self.fileModel.setRootPath(path)
        self.treeView.setRootIndex(self.fileModel.index(path))
        
    def filterFiles(self, text):
        """ 根据输入筛选文件 """
        if not text:
            self.fileModel.setNameFilters(["*.md", "*.markdown"])
        else:
            self.fileModel.setNameFilters([f"*{text}*.md", f"*{text}*.markdown"])
            
    def createNewFile(self):
        """ 创建新的Markdown文件 """
        if not self.rootPath:
            InfoBar.warning(
                title="未打开仓库",
                content="请先打开一个仓库",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        filename, ok = QInputDialog.getText(
            self, "新建Markdown文件", "文件名:", 
            text="新文档.md"
        )
        
        if ok and filename:
            # 确保文件名以.md结尾
            if not filename.lower().endswith(('.md', '.markdown')):
                filename += ".md"
                
            # 创建文件路径
            filePath = os.path.join(self.rootPath, filename)
            
            # 检查文件是否已存在
            if os.path.exists(filePath):
                InfoBar.warning(
                    title="文件已存在",
                    content=f"文件 {filename} 已存在",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建空文件
            try:
                with open(filePath, 'w', encoding='utf-8') as f:
                    f.write("# " + os.path.splitext(filename)[0] + "\n\n")
                    
                # 定位到新文件
                newIndex = self.fileModel.index(filePath)
                self.treeView.setCurrentIndex(newIndex)
                self.fileSelected.emit(filePath)
                
                InfoBar.success(
                    title="文件已创建",
                    content=f"文件 {filename} 已成功创建",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件失败: {str(e)}")
                
    def refreshFiles(self):
        """ 刷新文件列表 """
        if self.rootPath:
            self.fileModel.setRootPath(self.rootPath)
            
    def showContextMenu(self, position):
        """ 显示上下文菜单 """
        index = self.treeView.indexAt(position)
        if not index.isValid():
            return
            
        filePath = self.fileModel.filePath(index)
        
        # 创建上下文菜单
        menu = QMenu(self)
        
        # 打开操作
        openAction = QAction("打开", self)
        openAction.triggered.connect(lambda: self.fileSelected.emit(filePath))
        menu.addAction(openAction)
        
        # 重命名操作
        renameAction = QAction("重命名", self)
        renameAction.triggered.connect(lambda: self.renameFile(index))
        menu.addAction(renameAction)
        
        # 删除操作
        deleteAction = QAction("删除", self)
        deleteAction.triggered.connect(lambda: self.deleteFile(index))
        menu.addAction(deleteAction)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def renameFile(self, index):
        """ 重命名文件 """
        if not index.isValid():
            return
            
        oldPath = self.fileModel.filePath(index)
        oldName = os.path.basename(oldPath)
        
        newName, ok = QInputDialog.getText(
            self, "重命名文件", "新文件名:", 
            text=oldName
        )
        
        if ok and newName and newName != oldName:
            # 确保文件名以.md结尾
            if not newName.lower().endswith(('.md', '.markdown')):
                newName += ".md"
                
            # 创建新文件路径
            dirPath = os.path.dirname(oldPath)
            newPath = os.path.join(dirPath, newName)
            
            # 检查新文件名是否已存在
            if os.path.exists(newPath):
                InfoBar.warning(
                    title="文件已存在",
                    content=f"文件 {newName} 已存在",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 重命名文件
            try:
                os.rename(oldPath, newPath)
                InfoBar.success(
                    title="文件已重命名",
                    content=f"文件已重命名为 {newName}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名文件失败: {str(e)}")
                
    def deleteFile(self, index):
        """ 删除文件 """
        if not index.isValid():
            return
            
        filePath = self.fileModel.filePath(index)
        fileName = os.path.basename(filePath)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除文件 {fileName} 吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(filePath)
                InfoBar.success(
                    title="文件已删除",
                    content=f"文件 {fileName} 已成功删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")
                
    def onFileDoubleClicked(self, index):
        """ 处理文件双击事件 """
        if not index.isValid():
            return
            
        filePath = self.fileModel.filePath(index)
        
        # 如果是目录，展开/折叠
        if self.fileModel.isDir(index):
            if self.treeView.isExpanded(index):
                self.treeView.collapse(index)
            else:
                self.treeView.expand(index)
        # 如果是文件，发出信号
        else:
            self.fileSelected.emit(filePath) 