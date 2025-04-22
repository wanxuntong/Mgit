#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
                           QCheckBox, QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
                           QFileDialog, QComboBox, QToolBar, QAction, QSizePolicy, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QCursor
from qfluentwidgets import (LineEdit, PrimaryToolButton, FluentIcon, TitleLabel, 
                          PrimaryPushButton, InfoBar, InfoBarPosition, ComboBox,
                          CardWidget, ToolButton, TransparentToolButton, ToolTipFilter,
                          ToolTipPosition)
from src.utils.git_manager import GitManager
from src.utils.config_manager import ConfigManager

class GitPanel(QWidget):
    """ Git面板组件 """
    
    # 信号
    repositoryInitialized = pyqtSignal(str)
    repositoryOpened = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gitManager = None
        self.configManager = ConfigManager()
        self.recentReposList = []
        self.initUI()
        
        # 初始加载最近仓库列表
        self.updateRecentRepositories()
        
        # 禁用一些初始按钮
        self.commitBtn.setEnabled(False)
        self.pushBtn.setEnabled(False)
        self.pullBtn.setEnabled(False)
        self.fetchBtn.setEnabled(False)
        self.stashBtn.setEnabled(False)
        self.branchBtn.setEnabled(False)
        self.remoteBtn.setEnabled(False)
        self.branchCombo.setEnabled(False)
        self.syncBtn.setEnabled(False)
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题卡片
        titleCard = CardWidget(self)
        titleCardLayout = QVBoxLayout(titleCard)
        titleCardLayout.setContentsMargins(10, 5, 10, 5)
        titleCardLayout.setSpacing(0)
        
        # 标题区域
        titleBarLayout = QHBoxLayout()
        titleBarLayout.setContentsMargins(0, 0, 0, 0)
        
        self.titleLabel = TitleLabel("Git操作")
        titleBarLayout.addWidget(self.titleLabel)
        
        # 添加打开仓库按钮
        self.openBtn = TransparentToolButton(FluentIcon.FOLDER)
        self.openBtn.setToolTip("打开仓库")
        self.openBtn.clicked.connect(self.openRepository)
        titleBarLayout.addWidget(self.openBtn)
        
        # 添加初始化仓库按钮
        self.initRepoBtn = TransparentToolButton(FluentIcon.ADD)
        self.initRepoBtn.setToolTip("创建仓库")
        self.initRepoBtn.clicked.connect(self.initializeRepository)
        titleBarLayout.addWidget(self.initRepoBtn)
        
        # 添加刷新按钮
        self.refreshBtn = TransparentToolButton(FluentIcon.SYNC)
        self.refreshBtn.setToolTip("刷新状态")
        self.refreshBtn.clicked.connect(self.refreshStatus)
        titleBarLayout.addWidget(self.refreshBtn)
        
        titleCardLayout.addLayout(titleBarLayout)
        
        # 状态显示
        self.statusLabel = QLabel("未连接到任何Git仓库")
        titleCardLayout.addWidget(self.statusLabel)
        
        # 最近仓库下拉框
        recentRepoLayout = QHBoxLayout()
        recentRepoLayout.setContentsMargins(0, 5, 0, 0)
        
        recentRepoLabel = QLabel("最近仓库:")
        recentRepoLayout.addWidget(recentRepoLabel)
        
        self.recentRepoCombo = ComboBox()
        self.recentRepoCombo.setPlaceholderText("选择最近打开的仓库")
        self.recentRepoCombo.setMinimumWidth(200)
        self.recentRepoCombo.currentIndexChanged.connect(self.onRecentRepoSelected)
        recentRepoLayout.addWidget(self.recentRepoCombo)
        
        titleCardLayout.addLayout(recentRepoLayout)
        
        # 分支与远程操作区域
        branchRemoteLayout = QHBoxLayout()
        branchRemoteLayout.setContentsMargins(0, 5, 0, 0)
        
        # 分支选择下拉框
        self.branchCombo = ComboBox()
        self.branchCombo.setPlaceholderText("当前分支")
        self.branchCombo.currentIndexChanged.connect(self.onBranchSelected)
        branchRemoteLayout.addWidget(self.branchCombo)
        
        # 分支操作按钮
        self.branchBtn = TransparentToolButton(FluentIcon.MENU)
        self.branchBtn.setToolTip("分支操作")
        self.branchBtn.clicked.connect(self.showBranchMenu)
        branchRemoteLayout.addWidget(self.branchBtn)
        
        # 远程操作按钮
        self.remoteBtn = TransparentToolButton(FluentIcon.LINK)
        self.remoteBtn.setToolTip("远程仓库操作")
        self.remoteBtn.clicked.connect(self.showRemoteMenu)
        branchRemoteLayout.addWidget(self.remoteBtn)
        
        titleCardLayout.addLayout(branchRemoteLayout)
        
        # 添加组件到布局
        layout.addWidget(titleCard)
        
        # 外部仓库卡片（新增）
        externalCard = CardWidget(self)
        externalCardLayout = QVBoxLayout(externalCard)
        externalCardLayout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        externalCardLayout.addWidget(QLabel("外部仓库操作"))
        
        # 按钮布局
        externalBtnLayout = QHBoxLayout()
        
        # 克隆远程仓库按钮
        self.cloneBtn = PrimaryPushButton("克隆远程仓库")
        self.cloneBtn.setIcon(FluentIcon.COPY.icon())
        self.cloneBtn.clicked.connect(self.cloneExternalRepo)
        externalBtnLayout.addWidget(self.cloneBtn)
        
        # 从GitHub导入按钮
        self.importGitHubBtn = PrimaryPushButton("从GitHub导入")
        self.importGitHubBtn.setIcon(FluentIcon.LINK.icon())
        self.importGitHubBtn.clicked.connect(self.importFromGitHub)
        externalBtnLayout.addWidget(self.importGitHubBtn)
        
        externalCardLayout.addLayout(externalBtnLayout)
        
        # 同步按钮
        self.syncBtn = PrimaryPushButton("同步远程仓库")
        self.syncBtn.setIcon(FluentIcon.SYNC.icon())
        self.syncBtn.clicked.connect(self.syncWithRemote)
        self.syncBtn.setEnabled(False)
        externalCardLayout.addWidget(self.syncBtn)
        
        layout.addWidget(externalCard)
        
        # 操作区卡片
        operationCard = CardWidget(self)
        operationCardLayout = QVBoxLayout(operationCard)
        operationCardLayout.setContentsMargins(10, 10, 10, 10)
        
        # 提交信息输入框
        operationCardLayout.addWidget(QLabel("提交信息:"))
        self.commitMsgEdit = LineEdit()
        self.commitMsgEdit.setPlaceholderText("输入提交信息...")
        operationCardLayout.addWidget(self.commitMsgEdit)
        
        # 变更文件列表
        operationCardLayout.addWidget(QLabel("变更文件:"))
        
        self.changesList = QListWidget()
        self.changesList.setSelectionMode(QListWidget.ExtendedSelection)
        operationCardLayout.addWidget(self.changesList)
        
        # 按钮布局
        btnLayout = QHBoxLayout()
        
        # 提交按钮
        self.commitBtn = PrimaryPushButton("提交")
        self.commitBtn.setIcon(FluentIcon.SAVE.icon())
        self.commitBtn.clicked.connect(self.commitChanges)
        btnLayout.addWidget(self.commitBtn)
        
        # 推送按钮
        self.pushBtn = PrimaryPushButton("推送")
        self.pushBtn.setIcon(FluentIcon.SHARE.icon())
        self.pushBtn.clicked.connect(self.pushChanges)
        btnLayout.addWidget(self.pushBtn)
        
        # 拉取按钮
        self.pullBtn = PrimaryPushButton("拉取")
        self.pullBtn.setIcon(FluentIcon.DOWN.icon())
        self.pullBtn.clicked.connect(self.pullChanges)
        btnLayout.addWidget(self.pullBtn)
        
        operationCardLayout.addLayout(btnLayout)
        
        # 协作操作按钮布局
        collabBtnLayout = QHBoxLayout()
        
        # 抓取按钮
        self.fetchBtn = PrimaryPushButton("抓取")
        self.fetchBtn.setIcon(FluentIcon.SYNC.icon())
        self.fetchBtn.clicked.connect(self.fetchChanges)
        collabBtnLayout.addWidget(self.fetchBtn)
        
        # 存储按钮
        self.stashBtn = PrimaryPushButton("存储")
        self.stashBtn.setIcon(FluentIcon.SAVE.icon())
        self.stashBtn.clicked.connect(self.showStashMenu)
        collabBtnLayout.addWidget(self.stashBtn)
        
        operationCardLayout.addLayout(collabBtnLayout)
        
        layout.addWidget(operationCard)
        
        # 历史记录卡片
        historyCard = CardWidget(self)
        historyCardLayout = QVBoxLayout(historyCard)
        historyCardLayout.setContentsMargins(10, 10, 10, 10)
        
        historyCardLayout.addWidget(QLabel("提交历史:"))
        
        # 历史记录列表
        self.historyList = QListWidget()
        historyCardLayout.addWidget(self.historyList)
        
        layout.addWidget(historyCard)
        
        # 设置拉伸因子
        layout.setStretch(0, 0)  # 标题卡片不拉伸
        layout.setStretch(1, 0)  # 外部仓库卡片不拉伸
        layout.setStretch(2, 1)  # 操作区卡片少量拉伸
        layout.setStretch(3, 2)  # 历史记录卡片大量拉伸
        
    def updateRecentRepositories(self):
        """ 更新最近仓库下拉框 """
        # 保存当前选中的索引
        currentIndex = self.recentRepoCombo.currentIndex()
        
        # 暂时阻断信号以防止循环
        self.recentRepoCombo.blockSignals(True)
        
        try:
            # 清空下拉框
            self.recentRepoCombo.clear()
            self.recentRepoCombo.addItem("选择最近仓库...")
            
            # 重新获取最新的仓库列表（不使用缓存）
            self.recentReposList = self.configManager.get_recent_repositories()
            for repo in self.recentReposList:
                repoName = os.path.basename(repo)
                self.recentRepoCombo.addItem(f"{repoName} ({repo})")
            
            # 如果先前有选择，尝试恢复选中状态
            if currentIndex > 0 and currentIndex <= len(self.recentReposList):
                self.recentRepoCombo.setCurrentIndex(currentIndex)
            else:
                self.recentRepoCombo.setCurrentIndex(0)
        finally:
            # 确保信号一定会被重新启用
            self.recentRepoCombo.blockSignals(False)
    
    def onRecentRepoSelected(self, index):
        """ 处理选择最近仓库 """
        if index <= 0:
            return
            
        # 使用临时变量存储当前索引，避免在更新过程中触发更多事件
        selectedIndex = index
        
        # 先重置下拉框状态，阻断可能的事件循环
        self.recentRepoCombo.blockSignals(True)
        self.recentRepoCombo.setCurrentIndex(0)
        self.recentRepoCombo.blockSignals(False)
            
        # 使用索引从列表中获取仓库路径
        if 0 < selectedIndex <= len(self.recentReposList):
            repoPath = self.recentReposList[selectedIndex-1]
            if repoPath and os.path.exists(repoPath):
                try:
                    self.setRepository(repoPath)
                    # 发送信号前临时阻断更新
                    self.repositoryOpened.emit(repoPath)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            else:
                InfoBar.warning(
                    title="无效仓库路径",
                    content=f"路径 '{repoPath}' 不存在或无效",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
    def openRepository(self):
        """ 打开仓库 """
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择Git仓库", ""
        )
        if repoPath:
            try:
                self.setRepository(repoPath)
                self.repositoryOpened.emit(repoPath)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            
    def setRepository(self, path):
        """ 设置Git仓库路径 """
        if not path or not os.path.exists(path):
            return
            
        try:
            self.gitManager = GitManager(path)
            if self.gitManager.isValidRepo():
                self.statusLabel.setText(f"当前仓库: {os.path.basename(path)}")
                
                # 检查是否有远程仓库，根据结果启用或禁用相关按钮
                remotes = self.gitManager.getRemotes()
                has_remotes = len(remotes) > 0
                
                # 始终启用的按钮
                self.commitBtn.setEnabled(True)
                self.branchBtn.setEnabled(True)
                self.remoteBtn.setEnabled(True)
                self.branchCombo.setEnabled(True)
                self.stashBtn.setEnabled(True)
                
                # 只有当存在远程仓库时才启用的按钮
                self.pushBtn.setEnabled(has_remotes)
                self.pullBtn.setEnabled(has_remotes)
                self.fetchBtn.setEnabled(has_remotes)
                self.syncBtn.setEnabled(has_remotes)
                
                # 如果没有远程仓库，显示提示信息
                if not has_remotes:
                    InfoBar.info(
                        title="没有远程仓库",
                        content="当前仓库没有配置远程仓库，部分功能将被禁用",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                
                self.refreshStatus()
                
                # 更新最近仓库列表
                self.updateRecentRepositories()
            else:
                self.statusLabel.setText("无效的Git仓库")
                self.gitManager = None
                self.commitBtn.setEnabled(False)
                self.pushBtn.setEnabled(False)
                self.pullBtn.setEnabled(False)
                self.fetchBtn.setEnabled(False)
                self.stashBtn.setEnabled(False)
                self.branchBtn.setEnabled(False)
                self.remoteBtn.setEnabled(False)
                self.branchCombo.setEnabled(False)
                self.syncBtn.setEnabled(False)
                
                InfoBar.warning(
                    title="无效仓库",
                    content="所选路径不是有效的Git仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            self.gitManager = None
            self.commitBtn.setEnabled(False)
            self.pushBtn.setEnabled(False)
            self.pullBtn.setEnabled(False)
            self.fetchBtn.setEnabled(False)
            self.stashBtn.setEnabled(False)
            self.branchBtn.setEnabled(False)
            self.remoteBtn.setEnabled(False)
            self.branchCombo.setEnabled(False)
            
    def initializeRepository(self):
        """ 初始化新仓库 """
        # 选择目录
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择创建仓库的位置", ""
        )
        
        if not repoPath:
            return
            
        # 输入仓库名称
        repoName, ok = QInputDialog.getText(
            self, "创建仓库", "请输入仓库名称:"
        )
        
        if not ok or not repoName:
            return
            
        # 完整的仓库路径
        fullRepoPath = os.path.join(repoPath, repoName)
        
        # 检查路径是否已存在
        if os.path.exists(fullRepoPath) and os.listdir(fullRepoPath):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                f"目录 {fullRepoPath} 已存在且不为空，是否继续？\n（不会删除现有文件，但会将此目录初始化为Git仓库）",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        try:
            # 初始化仓库
            GitManager.initRepository(fullRepoPath)
            
            # 设置为当前仓库
            self.setRepository(fullRepoPath)
            
            # 发出信号通知其他组件
            self.repositoryInitialized.emit(fullRepoPath)
            
            InfoBar.success(
                title="创建成功",
                content=f"已成功创建并初始化Git仓库: {repoName}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化仓库失败: {str(e)}")
            
    def refreshStatus(self):
        """ 刷新Git状态 """
        if not self.gitManager:
            return
            
        try:
            # 获取变更文件
            changes = self.gitManager.getChangedFiles()
            
            # 清空列表
            self.changesList.clear()
            
            # 添加变更文件到列表
            for status, path in changes:
                item = QListWidgetItem()
                
                # 创建一个包含复选框的小部件
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 0, 5, 0)
                
                checkbox = QCheckBox()
                checkbox.setChecked(True)
                
                statusLabel = QLabel(status)
                statusLabel.setFixedWidth(80)
                
                pathLabel = QLabel(path)
                
                layout.addWidget(checkbox)
                layout.addWidget(statusLabel)
                layout.addWidget(pathLabel)
                
                item.setSizeHint(widget.sizeHint())
                self.changesList.addItem(item)
                self.changesList.setItemWidget(item, widget)
                
            # 获取最近的提交历史
            commits = self.gitManager.getCommitHistory(5)
            
            # 清空历史列表
            self.historyList.clear()
            
            # 添加提交历史到列表
            for commit in commits:
                item = QListWidgetItem()
                item.setText(f"{commit['hash'][:7]} - {commit['message']}")
                item.setToolTip(f"作者: {commit['author']}\n日期: {commit['date']}\n消息: {commit['message']}")
                self.historyList.addItem(item)
                
            # 更新分支下拉框
            self.updateBranchCombo()
            
            # 检查远程仓库状态并更新UI
            remotes = self.gitManager.getRemotes()
            has_remotes = len(remotes) > 0
            
            # 根据是否有远程仓库来启用或禁用相关按钮
            self.pushBtn.setEnabled(has_remotes)
            self.pullBtn.setEnabled(has_remotes)
            self.fetchBtn.setEnabled(has_remotes)
            self.syncBtn.setEnabled(has_remotes)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新状态失败: {str(e)}")
            
    def updateBranchCombo(self):
        """ 更新分支下拉框 """
        if not self.gitManager:
            return
            
        try:
            # 获取当前分支
            currentBranch = self.gitManager.getCurrentBranch()
            
            # 获取所有分支
            branches = self.gitManager.getBranches()
            
            # 记住选中的索引
            previousIndex = self.branchCombo.currentIndex()
            
            # 清空下拉框
            self.branchCombo.clear()
            
            # 添加分支到下拉框
            for branch in branches:
                self.branchCombo.addItem(branch)
                
            # 选中当前分支
            index = self.branchCombo.findText(currentBranch)
            if index >= 0:
                self.branchCombo.setCurrentIndex(index)
            elif previousIndex >= 0 and previousIndex < self.branchCombo.count():
                self.branchCombo.setCurrentIndex(previousIndex)
                
        except Exception as e:
            print(f"更新分支下拉框失败: {e}")
            
    def onBranchSelected(self, index):
        """ 处理选择分支 """
        if index < 0 or not self.gitManager:
            return
            
        selectedBranch = self.branchCombo.currentText()
        currentBranch = self.gitManager.getCurrentBranch()
        
        if selectedBranch != currentBranch:
            try:
                reply = QMessageBox.question(
                    self, "切换分支", 
                    f"确定要切换到分支 '{selectedBranch}' 吗？\n这将丢弃所有未提交的更改。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.gitManager.checkoutBranch(selectedBranch)
                    self.refreshStatus()
                    
                    InfoBar.success(
                        title="切换分支成功",
                        content=f"已切换到分支 '{selectedBranch}'",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    # 恢复选中当前分支
                    index = self.branchCombo.findText(currentBranch)
                    if index >= 0:
                        self.branchCombo.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换分支失败: {str(e)}")
                
                # 恢复选中当前分支
                index = self.branchCombo.findText(currentBranch)
                if index >= 0:
                    self.branchCombo.setCurrentIndex(index)
                
    def showBranchMenu(self):
        """ 显示分支菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 创建新分支动作
        createBranchAction = menu.addAction("创建新分支")
        createBranchAction.triggered.connect(self.createNewBranch)
        
        # 合并分支动作
        mergeBranchAction = menu.addAction("合并分支")
        mergeBranchAction.triggered.connect(self.mergeBranch)
        
        # 删除分支动作
        deleteBranchAction = menu.addAction("删除分支")
        deleteBranchAction.triggered.connect(self.deleteBranch)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def createNewBranch(self):
        """ 创建新分支 """
        if not self.gitManager:
            return
            
        # 输入分支名称
        branchName, ok = QInputDialog.getText(
            self, "创建分支", "请输入新分支名称:"
        )
        
        if not ok or not branchName:
            return
            
        try:
            # 创建分支
            self.gitManager.createBranch(branchName)
            
            # 询问是否切换到新分支
            reply = QMessageBox.question(
                self, "切换分支", 
                f"是否切换到新创建的分支 '{branchName}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.gitManager.checkoutBranch(branchName)
                
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="创建分支成功",
                content=f"已成功创建分支 '{branchName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建分支失败: {str(e)}")
            
    def mergeBranch(self):
        """ 合并分支 """
        if not self.gitManager:
            return
            
        # 获取所有分支
        branches = self.gitManager.getBranches()
        currentBranch = self.gitManager.getCurrentBranch()
        
        # 从分支列表中移除当前分支
        if currentBranch in branches:
            branches.remove(currentBranch)
            
        if not branches:
            InfoBar.warning(
                title="无可合并分支",
                content="没有其他分支可合并到当前分支",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 选择要合并的分支
        branchName, ok = QInputDialog.getItem(
            self, "合并分支", 
            f"选择要合并到 '{currentBranch}' 的分支:",
            branches, 0, False
        )
        
        if not ok or not branchName:
            return
            
        try:
            # 合并分支
            self.gitManager.mergeBranch(branchName)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="合并分支成功",
                content=f"已成功将 '{branchName}' 合并到 '{currentBranch}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并分支失败: {str(e)}")
            
    def deleteBranch(self):
        """ 删除分支 """
        if not self.gitManager:
            return
            
        # 获取所有分支
        branches = self.gitManager.getBranches()
        currentBranch = self.gitManager.getCurrentBranch()
        
        # 从分支列表中移除当前分支
        if currentBranch in branches:
            branches.remove(currentBranch)
            
        if not branches:
            InfoBar.warning(
                title="无可删除分支",
                content="没有其他分支可删除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 选择要删除的分支
        branchName, ok = QInputDialog.getItem(
            self, "删除分支", 
            "选择要删除的分支:",
            branches, 0, False
        )
        
        if not ok or not branchName:
            return
            
        # 询问是否强制删除
        reply = QMessageBox.question(
            self, "删除分支", 
            f"是否强制删除分支 '{branchName}'?\n强制删除可能导致未合并的更改丢失。",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Cancel:
            return
            
        forceDelete = (reply == QMessageBox.Yes)
        
        try:
            # 删除分支
            self.gitManager.deleteBranch(branchName, forceDelete)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="删除分支成功",
                content=f"已成功删除分支 '{branchName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除分支失败: {str(e)}")
            
    def showRemoteMenu(self):
        """ 显示远程仓库菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 添加远程仓库动作
        addRemoteAction = menu.addAction("添加远程仓库")
        addRemoteAction.triggered.connect(self.addRemote)
        
        # 查看远程仓库动作
        viewRemoteAction = menu.addAction("查看远程仓库")
        viewRemoteAction.triggered.connect(self.viewRemotes)
        
        # 删除远程仓库动作
        removeRemoteAction = menu.addAction("删除远程仓库")
        removeRemoteAction.triggered.connect(self.removeRemote)
        
        # 添加分隔符
        menu.addSeparator()
        
        # 从GitHub导入动作
        importGitHubAction = menu.addAction("从GitHub导入")
        importGitHubAction.triggered.connect(self.importFromGitHub)
        
        # 克隆远程仓库动作
        cloneRepoAction = menu.addAction("克隆远程仓库")
        cloneRepoAction.triggered.connect(self.cloneExternalRepo)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def addRemote(self):
        """ 添加远程仓库 """
        if not self.gitManager:
            return
            
        # 输入远程仓库名称
        remoteName, ok = QInputDialog.getText(
            self, "添加远程仓库", "请输入远程仓库名称 (例如: origin):"
        )
        
        if not ok or not remoteName:
            return
            
        # 检查远程仓库名称是否已存在
        try:
            existing_remotes = self.gitManager.getRemotes()
            if remoteName in existing_remotes:
                reply = QMessageBox.question(
                    self, "远程仓库已存在", 
                    f"远程仓库名称 '{remoteName}' 已存在，是否更新URL?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
        except Exception:
            # 如果获取远程仓库列表失败，继续尝试添加
            pass
            
        # 输入远程仓库URL
        remoteUrl, ok = QInputDialog.getText(
            self, "添加远程仓库", 
            "请输入远程仓库URL (例如: https://github.com/username/repo.git):"
        )
        
        if not ok or not remoteUrl:
            return
            
        try:
            # 尝试清理URL
            remoteUrl = self.gitManager.sanitize_url(remoteUrl)
            
            # 添加或更新远程仓库
            existing_remotes = self.gitManager.getRemotes()
            if remoteName in existing_remotes:
                # 更新已存在的远程仓库URL
                self.gitManager.repo.git.remote('set-url', remoteName, remoteUrl)
                message = f"已更新远程仓库 '{remoteName}' 的URL"
            else:
                # 添加新的远程仓库
                self.gitManager.addRemote(remoteName, remoteUrl)
                message = f"已成功添加远程仓库 '{remoteName}'"
                
            # 刷新状态并更新UI
            self.refreshStatus()
            
            InfoBar.success(
                title="操作成功",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加远程仓库失败: {str(e)}")
            
    def viewRemotes(self):
        """ 查看远程仓库 """
        if not self.gitManager:
            return
            
        try:
            # 获取远程仓库详情
            remotes = self.gitManager.getRemoteDetails()
            
            if not remotes:
                InfoBar.info(
                    title="无远程仓库",
                    content="当前仓库没有配置远程仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 显示远程仓库信息
            remoteInfo = "远程仓库列表:\n\n"
            for remote in remotes:
                remoteInfo += f"名称: {remote['name']}\n"
                remoteInfo += f"URL: {remote['url']}\n\n"
                
            QMessageBox.information(self, "远程仓库信息", remoteInfo)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取远程仓库信息失败: {str(e)}")
            
    def removeRemote(self):
        """ 删除远程仓库 """
        if not self.gitManager:
            return
            
        try:
            # 获取远程仓库详情
            remotes = self.gitManager.getRemoteDetails()
            
            if not remotes:
                InfoBar.info(
                    title="无远程仓库",
                    content="当前仓库没有配置远程仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 获取远程仓库名称列表
            remoteNames = [remote['name'] for remote in remotes]
            
            # 选择要删除的远程仓库
            remoteName, ok = QInputDialog.getItem(
                self, "删除远程仓库", 
                "选择要删除的远程仓库:",
                remoteNames, 0, False
            )
            
            if not ok or not remoteName:
                return
                
            # 确认删除
            reply = QMessageBox.question(
                self, "删除远程仓库", 
                f"确定要删除远程仓库 '{remoteName}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 删除远程仓库
            self.gitManager.removeRemote(remoteName)
            
            InfoBar.success(
                title="删除远程仓库成功",
                content=f"已成功删除远程仓库 '{remoteName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除远程仓库失败: {str(e)}")
            
    def showStashMenu(self):
        """ 显示存储菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 创建存储动作
        createStashAction = menu.addAction("存储更改")
        createStashAction.triggered.connect(self.stashChanges)
        
        # 应用存储动作
        applyStashAction = menu.addAction("应用存储")
        applyStashAction.triggered.connect(self.applyStash)
        
        # 查看存储列表动作
        viewStashAction = menu.addAction("查看存储列表")
        viewStashAction.triggered.connect(self.viewStashList)
        
        # 删除存储动作
        dropStashAction = menu.addAction("删除存储")
        dropStashAction.triggered.connect(self.dropStash)
        
        # 清空存储动作
        clearStashAction = menu.addAction("清空所有存储")
        clearStashAction.triggered.connect(self.clearStash)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def stashChanges(self):
        """ 存储更改 """
        if not self.gitManager:
            return
            
        # 输入存储消息
        message, ok = QInputDialog.getText(
            self, "存储更改", "请输入存储描述 (可选):"
        )
        
        if not ok:
            return
            
        try:
            # 存储更改
            self.gitManager.stashChanges(message if message else None)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="存储更改成功",
                content="已成功存储工作区更改",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"存储更改失败: {str(e)}")
            
    def applyStash(self):
        """ 应用存储 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 选择要应用的存储
            stash, ok = QInputDialog.getItem(
                self, "应用存储", 
                "选择要应用的存储:",
                stashes, 0, False
            )
            
            if not ok or not stash:
                return
                
            # 获取存储ID
            stash_id = int(stash.split(':')[0].split('@')[1])
            
            # 应用存储
            self.gitManager.applyStash(stash_id)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="应用存储成功",
                content="已成功应用存储的更改",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用存储失败: {str(e)}")
            
    def viewStashList(self):
        """ 查看存储列表 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 显示存储列表
            stashInfo = "存储列表:\n\n"
            for stash in stashes:
                stashInfo += f"{stash}\n"
                
            QMessageBox.information(self, "存储列表", stashInfo)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取存储列表失败: {str(e)}")
            
    def dropStash(self):
        """ 删除存储 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 选择要删除的存储
            stash, ok = QInputDialog.getItem(
                self, "删除存储", 
                "选择要删除的存储:",
                stashes, 0, False
            )
            
            if not ok or not stash:
                return
                
            # 获取存储ID
            stash_id = int(stash.split(':')[0].split('@')[1])
            
            # 删除存储
            self.gitManager.dropStash(stash_id)
            
            InfoBar.success(
                title="删除存储成功",
                content="已成功删除存储",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除存储失败: {str(e)}")
            
    def clearStash(self):
        """ 清空所有存储 """
        if not self.gitManager:
            return
            
        try:
            # 确认清空
            reply = QMessageBox.question(
                self, "清空存储", 
                "确定要清空所有存储吗? 此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 清空存储
            self.gitManager.clearStash()
            
            InfoBar.success(
                title="清空存储成功",
                content="已成功清空所有存储",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空存储失败: {str(e)}")
            
    def commitChanges(self):
        """ 提交更改 """
        if not self.gitManager:
            return
            
        # 获取提交信息
        message = self.commitMsgEdit.text().strip()
        if not message:
            InfoBar.warning(
                title="提交失败",
                content="请输入提交信息",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 获取选中的文件
        filesToCommit = []
        for i in range(self.changesList.count()):
            item = self.changesList.item(i)
            widget = self.changesList.itemWidget(item)
            checkbox = widget.layout().itemAt(0).widget()
            pathLabel = widget.layout().itemAt(2).widget()
            
            if checkbox.isChecked():
                filesToCommit.append(pathLabel.text())
                
        if not filesToCommit:
            InfoBar.warning(
                title="提交失败",
                content="请选择要提交的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            # 提交更改
            self.gitManager.commit(filesToCommit, message)
            
            # 刷新状态
            self.refreshStatus()
            
            # 清空提交信息
            self.commitMsgEdit.clear()
            
            InfoBar.success(
                title="提交成功",
                content=f"已成功提交 {len(filesToCommit)} 个文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"提交失败: {str(e)}")
            
    def pushChanges(self):
        """ 推送更改 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("推送"):
            return
            
        try:
            # 获取当前分支
            currentBranch = self.gitManager.getCurrentBranch()
            
            # 获取远程仓库列表
            remotes = self.gitManager.getRemotes()
            
            remote_name = None
            # 如果有多个远程仓库，让用户选择
            if len(remotes) > 1:
                remote_items = [remote for remote in remotes]
                remote_name, ok = QInputDialog.getItem(
                    self, "选择远程仓库", 
                    "请选择要推送到的远程仓库:",
                    remote_items, 0, False
                )
                
                if not ok or not remote_name:
                    return
            else:
                remote_name = remotes[0]
                
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认推送", 
                f"确定要将 {currentBranch} 分支推送到远程仓库 {remote_name} 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 推送更改到指定远程仓库
                self.gitManager.push(remote_name, currentBranch)
                
                InfoBar.success(
                    title="推送成功",
                    content=f"已成功将 {currentBranch} 分支推送到远程仓库 {remote_name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(self, "推送失败", error_msg)
            
    def pullChanges(self):
        """ 拉取更改 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("拉取"):
            return
            
        try:
            # 获取当前分支
            currentBranch = self.gitManager.getCurrentBranch()
            
            # 获取远程仓库列表
            remotes = self.gitManager.getRemotes()
            
            remote_name = None
            # 如果有多个远程仓库，让用户选择
            if len(remotes) > 1:
                remote_items = [remote for remote in remotes]
                remote_name, ok = QInputDialog.getItem(
                    self, "选择远程仓库", 
                    "请选择要拉取的远程仓库:",
                    remote_items, 0, False
                )
                
                if not ok or not remote_name:
                    return
            else:
                remote_name = remotes[0]
                
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认拉取", 
                f"确定要从远程仓库 {remote_name} 拉取 {currentBranch} 分支的更改吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 拉取更改
                self.gitManager.pull(remote_name, currentBranch)
                
                # 刷新状态
                self.refreshStatus()
                
                InfoBar.success(
                    title="拉取成功",
                    content=f"已成功从远程仓库 {remote_name} 拉取 {currentBranch} 分支的更改",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(self, "拉取失败", error_msg)
            
    def ensureRemoteExists(self, operation_name="操作"):
        """ 确保远程仓库存在，如果不存在则提示用户添加 
        Args:
            operation_name: 操作名称，用于错误提示
        Returns:
            bool: 是否存在远程仓库
        """
        if not self.gitManager:
            return False
            
        try:
            remotes = self.gitManager.getRemotes()
            if not remotes:
                reply = QMessageBox.question(
                    self, f"无法{operation_name}", 
                    f"当前仓库没有配置远程仓库，无法{operation_name}。\n是否现在添加远程仓库?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.addRemote()
                return False
            return True
        except Exception:
            return False
            
    def fetchChanges(self):
        """ 抓取更改 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("抓取"):
            return
            
        try:
            # 获取远程仓库列表
            remotes = self.gitManager.getRemotes()
            
            remote_name = None
            # 如果有多个远程仓库，让用户选择
            if len(remotes) > 1:
                remote_items = [remote for remote in remotes]
                remote_name, ok = QInputDialog.getItem(
                    self, "选择远程仓库", 
                    "请选择要抓取的远程仓库:",
                    remote_items, 0, False
                )
                
                if not ok or not remote_name:
                    return
            else:
                remote_name = remotes[0]
                
            # 抓取更改
            self.gitManager.fetch(remote_name)
            
            InfoBar.success(
                title="抓取成功",
                content=f"已成功从远程仓库 {remote_name} 抓取更改",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "抓取失败", str(e))

    def importFromGitHub(self):
        """ 从GitHub导入仓库 """
        if not self.gitManager:
            return
            
        # 输入GitHub仓库URL或快捷方式
        url, ok = QInputDialog.getText(
            self, "从GitHub导入", 
            "请输入GitHub仓库URL或快捷方式:\n" +
            "(例如: https://github.com/username/repo.git)\n" +
            "(或输入: username/repo)"
        )
        
        if not ok or not url:
            return
            
        # 处理快捷方式
        if not url.startswith("http") and "/" in url and not url.startswith("git@"):
            # 将username/repo转换为完整URL
            if url.count("/") == 1:  # 确保只有一个斜杠
                url = f"https://github.com/{url}.git"
        
        # 确保URL格式正确（移除可能导致问题的部分）
        if ":" in url and not url.startswith("git@"):
            # 检查是否有不正确的端口指定
            parts = url.split(":")
            if len(parts) > 1 and not parts[0].endswith("//"):
                # 修正格式为标准https URL
                domain_parts = parts[0].split("//")
                if len(domain_parts) > 1:
                    protocol = domain_parts[0] + "//"
                    domain = domain_parts[1]
                    url = protocol + domain + "/" + "/".join(parts[1:])
                    # 移除URL中可能的端口指定
                    url = url.replace(":github.com", "github.com")
        
        # 询问是否作为远程仓库添加
        reply = QMessageBox.question(
            self, "添加方式", 
            "如何添加该仓库?\n\n选择'是'将其添加为远程仓库\n选择'否'直接拉取并合并内容",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
            
        as_remote = (reply == QMessageBox.Yes)
        
        # 如果作为远程仓库添加，询问远程仓库名称
        remote_name = "origin"
        if as_remote:
            name, ok = QInputDialog.getText(
                self, "远程仓库名称", 
                "请输入远程仓库名称:",
                text="origin"
            )
            if ok and name:
                remote_name = name
            
        try:
            # 导入外部仓库
            self.gitManager.importExternalRepo(url, as_remote, remote_name)
            
            # 如果添加为远程仓库，询问是否拉取
            if as_remote:
                reply = QMessageBox.question(
                    self, "拉取更改", 
                    f"是否立即从远程仓库 '{remote_name}' 拉取更改?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.gitManager.pull(remote_name)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="导入成功",
                content=f"已成功从GitHub导入仓库" + (" 并添加为远程仓库" if as_remote else ""),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"从GitHub导入失败: {str(e)}")
            
    def cloneExternalRepo(self):
        """ 克隆外部仓库 """
        # 输入仓库URL或快捷方式
        url, ok = QInputDialog.getText(
            self, "克隆远程仓库", 
            "请输入远程仓库URL或快捷方式:\n" +
            "(例如: https://github.com/username/repo.git)\n" +
            "(或输入GitHub快捷方式: username/repo)"
        )
        
        if not ok or not url:
            return
            
        # 处理快捷方式
        if not url.startswith("http") and "/" in url and not url.startswith("git@"):
            # 将username/repo转换为完整URL
            if url.count("/") == 1:  # 确保只有一个斜杠
                url = f"https://github.com/{url}.git"
                
        # 确保URL格式正确（移除可能导致问题的部分）
        if ":" in url and not url.startswith("git@"):
            # 检查是否有不正确的端口指定
            parts = url.split(":")
            if len(parts) > 1 and not parts[0].endswith("//"):
                # 修正格式为标准https URL
                domain_parts = parts[0].split("//")
                if len(domain_parts) > 1:
                    protocol = domain_parts[0] + "//"
                    domain = domain_parts[1]
                    url = protocol + domain + "/" + "/".join(parts[1:])
                    # 移除URL中可能的端口指定
                    url = url.replace(":github.com", "github.com")
        
        # 选择目标路径
        target_path = QFileDialog.getExistingDirectory(
            self, "选择克隆目标位置", ""
        )
        
        if not target_path:
            return
            
        # 输入仓库名称
        repo_name, ok = QInputDialog.getText(
            self, "仓库名称", 
            "请输入本地仓库名称(留空使用默认名称):"
        )
        
        if not ok:
            return
            
        # 如果用户输入了仓库名称，使用该名称创建目标路径
        if repo_name:
            target_path = os.path.join(target_path, repo_name)
        else:
            # 从URL中提取仓库名称
            repo_name = os.path.basename(url)
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_path = os.path.join(target_path, repo_name)
            
        # 如果目标路径已存在，确认是否覆盖
        if os.path.exists(target_path) and os.listdir(target_path):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                f"目录 {target_path} 已存在且不为空，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
        # 确认是否克隆指定分支
        branch = None
        reply = QMessageBox.question(
            self, "克隆分支", 
            "是否克隆特定分支？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            branch_name, ok = QInputDialog.getText(
                self, "分支名称", 
                "请输入要克隆的分支名称:"
            )
            
            if ok and branch_name:
                branch = branch_name
                
        # 是否递归克隆子模块
        recursive = False
        reply = QMessageBox.question(
            self, "递归克隆", 
            "是否递归克隆子模块？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            recursive = True
            
        try:
            # 克隆仓库
            GitManager.cloneRepository(url, target_path, branch, recursive=recursive)
            
            # 询问是否打开该仓库
            reply = QMessageBox.question(
                self, "打开仓库", 
                f"仓库已成功克隆到 {target_path}，是否立即打开？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.setRepository(target_path)
                self.repositoryOpened.emit(target_path)
            
            InfoBar.success(
                title="克隆成功",
                content=f"已成功克隆仓库到 {target_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"克隆仓库失败: {str(e)}")

    def syncWithRemote(self):
        """ 同步远程仓库 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("同步"):
            return
            
        try:
            # 获取当前分支
            currentBranch = self.gitManager.getCurrentBranch()
            
            # 获取远程仓库列表
            remotes = self.gitManager.getRemotes()
            
            remote_name = None
            # 如果有多个远程仓库，让用户选择
            if len(remotes) > 1:
                remote_items = [remote for remote in remotes]
                remote_name, ok = QInputDialog.getItem(
                    self, "选择远程仓库", 
                    "请选择要同步的远程仓库:",
                    remote_items, 0, False
                )
                
                if not ok or not remote_name:
                    return
            else:
                remote_name = remotes[0]
                
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认同步", 
                f"确定要与远程仓库 {remote_name} 同步 {currentBranch} 分支吗?\n" +
                "这将执行 fetch+pull+push 操作。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 执行同步步骤
                # 1. 首先抓取
                self.gitManager.fetch(remote_name)
                
                # 2. 拉取更改
                self.gitManager.pull(remote_name, currentBranch)
                
                # 3. 推送更改
                self.gitManager.push(remote_name, currentBranch)
                
                # 刷新状态
                self.refreshStatus()
                
                InfoBar.success(
                    title="同步成功",
                    content=f"已成功与远程仓库 {remote_name} 同步 {currentBranch} 分支",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            QMessageBox.critical(self, "同步失败", str(e)) 