#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                           QLabel, QHBoxLayout, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor
from qfluentwidgets import (ScrollArea, TitleLabel, CardWidget, FluentIcon,
                           TransparentToolButton, SearchLineEdit)

class DocumentHeadingItem(QTreeWidgetItem):
    """ 文档标题项 """
    
    def __init__(self, parent=None, level=1, title="", line_number=0):
        super().__init__(parent)
        self.level = level
        self.title = title
        self.line_number = line_number
        
        # 设置显示文本
        self.setText(0, title)
        
        # 根据级别设置不同的字体样式
        font = QFont()
        if level == 1:
            font.setPointSize(12)
            font.setBold(True)
        elif level == 2:
            font.setPointSize(11)
            font.setBold(True)
        else:
            font.setPointSize(10)
            
        self.setFont(0, font)
        
        # 根据标题级别设置缩进
        # 注意：此处不需要设置缩进，QTreeWidget已在父级组件中设置了整体缩进
        # 若某处代码尝试调用item.setIndentation()，需要修改该处代码
        
    def setIndentation(self, indent):
        """实现一个空的setIndentation方法，以防止某处代码尝试调用此方法"""
        # 此方法不做任何事情，因为QTreeWidget已经处理了缩进
        pass


class DocumentNavigator(QWidget):
    """ 文档导航器组件 """
    
    headingSelected = pyqtSignal(int)  # 当用户选择标题时，发出信号，参数为行号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题和搜索区域
        headerCard = CardWidget(self)
        headerLayout = QVBoxLayout(headerCard)
        headerLayout.setContentsMargins(10, 5, 10, 5)
        
        # 标题栏
        titleBarLayout = QHBoxLayout()
        
        self.titleLabel = TitleLabel("文档导航")
        titleBarLayout.addWidget(self.titleLabel)
        
        # 刷新按钮
        self.refreshBtn = TransparentToolButton(FluentIcon.SYNC)
        self.refreshBtn.setToolTip("刷新导航")
        titleBarLayout.addWidget(self.refreshBtn)
        
        # 展开按钮
        self.expandBtn = TransparentToolButton(FluentIcon.CHEVRON_DOWN_MED)
        self.expandBtn.setToolTip("展开全部")
        titleBarLayout.addWidget(self.expandBtn)
        
        # 收起按钮
        self.collapseBtn = TransparentToolButton(FluentIcon.UP)
        self.collapseBtn.setToolTip("收起全部")
        titleBarLayout.addWidget(self.collapseBtn)
        
        headerLayout.addLayout(titleBarLayout)
        
        # 搜索框
        self.searchBox = SearchLineEdit()
        self.searchBox.setPlaceholderText("搜索标题...")
        headerLayout.addWidget(self.searchBox)
        
        layout.addWidget(headerCard)
        
        # 标题树
        self.headingTree = QTreeWidget()
        self.headingTree.setHeaderHidden(True)
        self.headingTree.setColumnCount(1)
        self.headingTree.setIndentation(15)
        self.headingTree.setAnimated(True)
        self.headingTree.setExpandsOnDoubleClick(True)
        
        # 滚动区域
        scrollArea = ScrollArea()
        scrollArea.setWidget(self.headingTree)
        scrollArea.setWidgetResizable(True)
        
        layout.addWidget(scrollArea)
        
        # 连接信号
        self.headingTree.itemClicked.connect(self.onHeadingClicked)
        self.refreshBtn.clicked.connect(self.refreshNavigator)
        self.expandBtn.clicked.connect(self.expandAll)
        self.collapseBtn.clicked.connect(self.collapseAll)
        self.searchBox.textChanged.connect(self.filterHeadings)
        
        # 初始化标题树
        self.refreshNavigator()
        
    def refreshNavigator(self):
        """ 刷新导航器 """
        # 此方法会由外部调用并传入当前文档内容
        pass
        
    def expandAll(self):
        """ 展开所有标题 """
        self.headingTree.expandAll()
        
    def collapseAll(self):
        """ 收起所有标题 """
        self.headingTree.collapseAll()
        
    def onHeadingClicked(self, item, column):
        """ 处理标题点击事件 """
        heading_item = item
        if isinstance(heading_item, DocumentHeadingItem):
            self.headingSelected.emit(heading_item.line_number)
            
    def parseDocument(self, document_text):
        """ 解析文档内容，提取标题结构 """
        self.headingTree.clear()
        
        if not document_text:
            return
            
        # 遍历每一行寻找标题
        lines = document_text.split('\n')
        parent_items = {0: self.headingTree, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        
        for line_number, line in enumerate(lines):
            # 匹配标题行 (# 标题)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # 创建标题项
                if level == 1:
                    # 一级标题，加入根节点
                    item = DocumentHeadingItem(None, level, title, line_number)
                    self.headingTree.addTopLevelItem(item)
                    parent_items[1] = item
                    # 清空低于当前级别的父项
                    for i in range(2, 7):
                        parent_items[i] = None
                else:
                    # 寻找上一级父项
                    parent_level = level - 1
                    while parent_level > 0 and parent_items[parent_level] is None:
                        parent_level -= 1
                    
                    if parent_level > 0 and parent_items[parent_level]:
                        item = DocumentHeadingItem(parent_items[parent_level], level, title, line_number)
                    else:
                        # 如果没有找到合适的父项，添加到根
                        item = DocumentHeadingItem(None, level, title, line_number)
                        self.headingTree.addTopLevelItem(item)
                    
                    # 更新当前级别的父项
                    parent_items[level] = item
                    # 清空低于当前级别的父项
                    for i in range(level + 1, 7):
                        parent_items[i] = None
        
        # 展开所有标题
        self.headingTree.expandAll()
        
    def filterHeadings(self, text):
        """ 根据搜索文本过滤标题 """
        if not text:
            # 如果搜索框为空，显示所有项
            for i in range(self.headingTree.topLevelItemCount()):
                self.setItemVisibility(self.headingTree.topLevelItem(i), True)
            return
            
        # 遍历所有项，检查标题是否包含搜索文本
        for i in range(self.headingTree.topLevelItemCount()):
            top_item = self.headingTree.topLevelItem(i)
            has_visible_child = self.searchItem(top_item, text.lower())
            self.setItemVisibility(top_item, has_visible_child)
                
    def searchItem(self, item, search_text):
        """ 递归搜索项目及其子项 """
        visible = False
        
        # 检查当前项
        if search_text in item.text(0).lower():
            self.setItemVisibility(item, True)
            visible = True
        else:
            # 检查所有子项
            for i in range(item.childCount()):
                if self.searchItem(item.child(i), search_text):
                    visible = True
            
            # 如果有匹配的子项，显示当前项，否则隐藏
            self.setItemVisibility(item, visible)
            
        return visible
        
    def setItemVisibility(self, item, visible):
        """ 设置项目的可见性 """
        item.setHidden(not visible)
        
    def goToLine(self, line_number):
        """ 根据行号查找并选中对应的标题 """
        # 在实际应用中，Editor会调用这个方法滚动到对应位置
        pass 