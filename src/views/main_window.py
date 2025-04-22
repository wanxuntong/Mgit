#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QSplitter, QMessageBox, 
                           QStackedWidget, QFileDialog, QMenuBar, QMenu, QAction)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QKeySequence

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, 
                          FluentIcon, SubtitleLabel, setTheme, Theme, 
                          FluentStyleSheet, InfoBar, InfoBarPosition)

# 导入自定义组件
from src.components.editor import MarkdownEditor
from src.components.explorer import FileExplorer
from src.components.preview import MarkdownPreview
from src.components.git_panel import GitPanel
from src.components.status_bar import StatusBar
from src.utils.git_manager import GitManager
from src.utils.config_manager import ConfigManager

class MainWindow(QMainWindow):
    """ 主窗口类 """
    
    repoChanged = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.configManager = ConfigManager()
        
        # 初始化Git管理器为None
        self.gitManager = None
        
        # 窗口设置
        self.setWindowTitle("MGit - Markdown笔记与Git版本控制")
        self.resize(1200, 800)
        
        # 初始化UI
        self.initUI()
        
        # 创建菜单
        self.createMenus()
        
        # 连接信号与槽
        self.connectSignals()
        
        # 设置主题
        theme = self.configManager.get_theme()
        if theme == 'light':
            setTheme(Theme.LIGHT)
        elif theme == 'dark':
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)
        
        # 添加快捷键
        self.setupShortcuts()
        
        # 检查自动保存恢复
        QTimer.singleShot(500, self.checkAutoSaveRecovery)
        
    def initUI(self):
        """ 初始化用户界面 """
        # 创建中心窗口部件
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.centralLayout = QVBoxLayout(self.centralWidget)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建主分割器
        self.mainSplitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧文件浏览器
        self.fileExplorer = FileExplorer(self)
        
        # 创建文档导航器
        from src.components.document_navigator import DocumentNavigator
        self.documentNavigator = DocumentNavigator(self)
        
        # 创建包含文件浏览器和文档导航器的左侧区域
        leftPanel = QWidget()
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧切换分割器
        self.leftSplitter = QSplitter(Qt.Vertical)
        self.leftSplitter.addWidget(self.fileExplorer)
        self.leftSplitter.addWidget(self.documentNavigator)
        self.leftSplitter.setSizes([400, 400])
        
        leftLayout.addWidget(self.leftSplitter)
        
        # 创建中间编辑器和预览区分割器
        self.editorSplitter = QSplitter(Qt.Horizontal)
        
        # 创建Markdown编辑器
        self.editor = MarkdownEditor(self)
        
        # 创建Markdown预览面板
        self.preview = MarkdownPreview(self)
        
        # 创建Git面板
        self.gitPanel = GitPanel(self)
        
        # 添加组件到分割器
        self.editorSplitter.addWidget(self.editor)
        self.editorSplitter.addWidget(self.preview)
        self.editorSplitter.setSizes([600, 600])
        
        # 添加组件到主分割器
        self.mainSplitter.addWidget(leftPanel)
        self.mainSplitter.addWidget(self.editorSplitter)
        self.mainSplitter.addWidget(self.gitPanel)
        self.mainSplitter.setSizes([250, 700, 250])
        
        # 将主分割器添加到中央布局
        self.centralLayout.addWidget(self.mainSplitter)
        
        # 创建并添加状态栏
        self.statusBar = StatusBar(self)
        self.centralLayout.addWidget(self.statusBar)
    
    def createMenus(self):
        """ 创建菜单栏 """
        # 创建菜单栏
        menuBar = self.menuBar()
        
        # 文件菜单
        fileMenu = menuBar.addMenu("文件")
        
        # 新建文件动作
        newFileAction = QAction("新建文件", self)
        newFileAction.setShortcut("Ctrl+N")
        newFileAction.triggered.connect(self.createNewFile)
        fileMenu.addAction(newFileAction)
        
        # 打开文件动作
        openFileAction = QAction("打开文件", self)
        openFileAction.setShortcut("Ctrl+O")
        openFileAction.triggered.connect(self.openFile)
        fileMenu.addAction(openFileAction)
        
        # 保存文件动作
        saveFileAction = QAction("保存文件", self)
        saveFileAction.setShortcut("Ctrl+S")
        saveFileAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveFileAction)
        
        # 另存为文件动作
        saveAsFileAction = QAction("另存为", self)
        saveAsFileAction.setShortcut("Ctrl+Shift+S")
        saveAsFileAction.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveAsFileAction)
        
        # 文件历史记录操作子菜单
        fileHistoryMenu = QMenu("文件版本", self)
        
        # 比较文件与已保存版本
        compareWithSavedAction = QAction("比较未保存与已保存版本", self)
        compareWithSavedAction.setShortcut("Ctrl+K D")
        compareWithSavedAction.triggered.connect(self.compareWithSaved)
        fileHistoryMenu.addAction(compareWithSavedAction)
        
        # 回退到已保存版本
        revertToSavedAction = QAction("回退到已保存版本", self)
        revertToSavedAction.triggered.connect(self.revertToSaved)
        fileHistoryMenu.addAction(revertToSavedAction)
        
        # 比较文件与Git中的版本
        compareWithGitAction = QAction("比较与Git版本", self)
        compareWithGitAction.triggered.connect(self.compareWithGitVersion)
        fileHistoryMenu.addAction(compareWithGitAction)
        
        # 回退到Git版本
        revertToGitAction = QAction("回退到Git版本", self)
        revertToGitAction.triggered.connect(self.revertToGitVersion)
        fileHistoryMenu.addAction(revertToGitAction)
        
        fileMenu.addMenu(fileHistoryMenu)
        
        fileMenu.addSeparator()
        
        # 退出动作
        exitAction = QAction("退出", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        
        # Git菜单
        gitMenu = menuBar.addMenu("Git")
        
        # 打开仓库动作
        openRepoAction = QAction("打开仓库", self)
        openRepoAction.setIcon(FluentIcon.FOLDER.icon())
        openRepoAction.triggered.connect(self.openRepo)
        gitMenu.addAction(openRepoAction)
        
        # 创建仓库动作
        createRepoAction = QAction("创建仓库", self)
        createRepoAction.setIcon(FluentIcon.ADD.icon())
        createRepoAction.triggered.connect(self.createNewRepository)
        gitMenu.addAction(createRepoAction)
        
        # 最近仓库子菜单
        self.recentReposMenu = QMenu("最近仓库", self)
        self.recentReposMenu.setIcon(FluentIcon.HISTORY.icon())
        gitMenu.addMenu(self.recentReposMenu)
        
        # 添加清空历史记录动作
        self.recentReposMenu.addSeparator()
        clearRecentAction = QAction("清空历史记录", self)
        clearRecentAction.triggered.connect(self.clearRecentRepositories)
        self.recentReposMenu.addAction(clearRecentAction)
        
        # 更新最近仓库列表
        self.updateRecentRepositoriesMenu()
        
        # 视图菜单
        viewMenu = menuBar.addMenu("视图")
        
        # 主题子菜单
        themeMenu = QMenu("主题", self)
        themeMenu.setIcon(FluentIcon.BRUSH.icon())
        
        # 主题选项
        lightThemeAction = QAction("浅色", self)
        lightThemeAction.triggered.connect(lambda: self.setTheme("light"))
        
        darkThemeAction = QAction("深色", self)
        darkThemeAction.triggered.connect(lambda: self.setTheme("dark"))
        
        autoThemeAction = QAction("自动", self)
        autoThemeAction.triggered.connect(lambda: self.setTheme("auto"))
        
        themeMenu.addAction(lightThemeAction)
        themeMenu.addAction(darkThemeAction)
        themeMenu.addAction(autoThemeAction)
        
        viewMenu.addMenu(themeMenu)
        
    def updateRecentRepositoriesMenu(self):
        """ 更新最近仓库菜单 """
        # 清空除了最后一项（清空历史记录）外的所有菜单项
        clearAction = None
        if self.recentReposMenu.actions():
            clearAction = self.recentReposMenu.actions()[-1]
            
        self.recentReposMenu.clear()
        
        # 获取最近仓库列表
        recentRepos = self.configManager.get_recent_repositories()
        
        # 添加最近仓库到菜单
        for repo in recentRepos:
            repoName = os.path.basename(repo)
            action = QAction(f"{repoName} ({repo})", self)
            action.triggered.connect(lambda checked, path=repo: self.openRepository(path))
            self.recentReposMenu.addAction(action)
        
        # 如果没有最近仓库，添加提示信息
        if not recentRepos:
            emptyAction = QAction("没有最近打开的仓库", self)
            emptyAction.setEnabled(False)
            self.recentReposMenu.addAction(emptyAction)
            
        # 添加分隔符和清空历史记录动作
        self.recentReposMenu.addSeparator()
        if clearAction:
            self.recentReposMenu.addAction(clearAction)
        else:
            clearRecentAction = QAction("清空历史记录", self)
            clearRecentAction.triggered.connect(self.clearRecentRepositories)
            self.recentReposMenu.addAction(clearRecentAction)
        
    def clearRecentRepositories(self):
        """ 清空最近仓库历史记录 """
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空最近仓库历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.configManager.clear_recent_repositories()
            # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
            
            InfoBar.success(
                title="清空成功",
                content="已清空最近仓库历史记录",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def setTheme(self, theme):
        """ 设置主题 """
        self.configManager.set_theme(theme)
        
        if theme == 'light':
            setTheme(Theme.LIGHT)
            is_dark_mode = False
        elif theme == 'dark':
            setTheme(Theme.DARK)
            is_dark_mode = True
        else:
            setTheme(Theme.AUTO)
            # For AUTO theme, we need to determine the actual current theme
            from qfluentwidgets import isDarkTheme
            is_dark_mode = isDarkTheme()
            
        # Update components with the new theme
        if hasattr(self, 'editor'):
            self.editor.updateTheme(is_dark_mode)
            
        # Force refresh markdown preview if it exists
        if hasattr(self, 'preview') and hasattr(self, 'editor'):
            self.updatePreview()
            
        # Update status bar style if needed
        if hasattr(self, 'statusBar'):
            self.statusBar.updateTheme(is_dark_mode)
    
    def connectSignals(self):
        """ 连接信号与槽 """
        # 编辑器内容改变时，更新预览
        self.editor.textChanged.connect(self.updatePreview)
        
        # 编辑器文档内容变化时，更新导航
        self.editor.documentChanged.connect(self.updateDocumentNavigation)
        
        # 编辑器光标位置变化时，更新导航中的当前项
        self.editor.cursorPositionChanged.connect(self.onCursorPositionChanged)
        
        # 导航项被点击时，将编辑器跳转到对应位置
        self.documentNavigator.headingSelected.connect(self.editor.goToLine)
        
        # 文件浏览器选择文件时，加载文件
        self.fileExplorer.fileSelected.connect(self.loadFile)
        
        # 仓库改变时，通知各组件
        self.repoChanged.connect(self.fileExplorer.setRootPath)
        self.repoChanged.connect(self.gitPanel.setRepository)
        
        # 连接GitPanel的信号
        self.gitPanel.repositoryInitialized.connect(self.onRepositoryInitialized)
        self.gitPanel.repositoryOpened.connect(self.onRepositoryOpened)
        
        # 连接ConfigManager的仓库列表更新信号，实时更新菜单
        self.configManager.recentRepositoriesChanged.connect(self.updateRecentRepositoriesMenu)
        # 同时也通知Git面板更新最近仓库列表
        self.configManager.recentRepositoriesChanged.connect(self.gitPanel.updateRecentRepositories)
        
    def updatePreview(self):
        """ 更新Markdown预览 """
        content = self.editor.toPlainText()
        self.preview.setMarkdown(content)
    
    def createNewFile(self):
        """ 创建新文件 """
        # 这里可以实现新建文件的逻辑
        self.editor.clearText()
        self.statusBar.setCurrentFile("")
    
    def openFile(self):
        """ 打开文件对话框 """
        filePath, _ = QFileDialog.getOpenFileName(
            self, "打开Markdown文件", "", "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if filePath:
            self.loadFile(filePath)
    
    def saveFile(self):
        """ 保存当前文件 
        Returns:
            bool: 是否成功保存
        """
        currentFile = self.statusBar.getCurrentFile()
        
        # 如果没有当前文件，执行另存为操作
        if not currentFile:
            return self.saveFileAs()
            
        try:
            # 设置编辑器当前文件路径
            self.editor.currentFilePath = currentFile
            
            # 使用编辑器的保存方法
            success = self.editor.saveFile()
            
            if success:
                # 更新状态栏
                self.statusBar.setCurrentFile(currentFile)
                
                # 显示成功消息
                InfoBar.success(
                    title="保存成功",
                    content=f"文件已保存: {os.path.basename(currentFile)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            
            return success
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存文件时发生错误: {str(e)}")
            return False
            
    def saveFileAs(self):
        """ 另存为文件 
        Returns:
            bool: 是否成功保存
        """
        currentFile = self.statusBar.getCurrentFile()
        
        # 设置起始目录
        if currentFile:
            self.editor.currentFilePath = currentFile
        
        # 使用编辑器的另存为方法
        success = self.editor.saveAsFile()
        
        if success and self.editor.currentFilePath:
            # 更新状态栏
            self.statusBar.setCurrentFile(self.editor.currentFilePath)
            
            # 显示成功消息
            InfoBar.success(
                title="保存成功",
                content=f"文件已保存: {os.path.basename(self.editor.currentFilePath)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
        return success
    
    def openRepo(self):
        """ 打开仓库对话框 """
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择Git仓库", ""
        )
        if repoPath:
            self.openRepository(repoPath)
    
    def createNewRepository(self):
        """ 创建新的Git仓库 """
        # 选择目录
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择创建仓库的位置", ""
        )
        
        if not repoPath:
            return
            
        # 输入仓库名称
        from PyQt5.QtWidgets import QInputDialog
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
            
            # 打开新创建的仓库
            self.openRepository(fullRepoPath)
            
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
            QMessageBox.critical(self, "错误", f"创建仓库失败: {str(e)}")
        
    def loadFile(self, filePath):
        """ 加载文件到编辑器 """
        if not filePath or not os.path.exists(filePath):
            return
            
        if not filePath.lower().endswith(('.md', '.markdown')):
            InfoBar.warning(
                title="不支持的文件类型",
                content="MGit只支持Markdown文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            with open(filePath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.editor.setPlainText(content)
                self.statusBar.setCurrentFile(filePath)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            
    def openRepository(self, path):
        """ 打开Git仓库 """
        # 检查是否为有效的Git仓库
        try:
            gitManager = GitManager(path)
            if gitManager.isValidRepo():
                self.repoChanged.emit(path)
                self.statusBar.setCurrentRepository(path)
                
                # 添加到最近仓库列表
                self.configManager.add_recent_repository(path)
                # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
                
                return True
            else:
                InfoBar.warning(
                    title="无效仓库",
                    content="所选路径不是有效的Git仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            return False
    
    def onRepositoryInitialized(self, repo_path):
        """ 处理仓库初始化完成事件 """
        self.repoChanged.emit(repo_path)
        self.statusBar.setCurrentRepository(repo_path)
        
        # 添加到最近仓库列表
        self.configManager.add_recent_repository(repo_path)
        # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
    
    def onRepositoryOpened(self, repo_path):
        """ 处理仓库打开事件 """
        # 简单的防止重复更新的逻辑
        # 检查这个仓库是否已经是最近的第一个仓库
        recent_repos = self.configManager.get_recent_repositories()
        if recent_repos and recent_repos[0] == repo_path:
            # 如果已经是最近的第一个仓库，只更新UI即可，不需要触发一次完整的添加流程
            self.repoChanged.emit(repo_path)
            self.statusBar.setCurrentRepository(repo_path)
            return
            
        # 添加到最近仓库列表并更新UI
        self.configManager.add_recent_repository(repo_path)
        # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
        
        # 更新UI
        self.repoChanged.emit(repo_path)
        self.statusBar.setCurrentRepository(repo_path)
        
    def updateDocumentNavigation(self, document_text):
        """ 更新文档导航 """
        self.documentNavigator.parseDocument(document_text)
        
    def onCursorPositionChanged(self, line_number):
        """ 处理光标位置变化 """
        # 在这里可以更新状态栏显示当前行列信息
        pass 

    def compareWithSaved(self):
        """ 比较当前未保存的内容与已保存的文件版本 """
        currentFile = self.statusBar.getCurrentFile()
        if not currentFile or not os.path.exists(currentFile):
            InfoBar.warning(
                title="无法比较",
                content="没有已保存的文件可以比较",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            # 获取当前编辑器内容
            current_content = self.editor.toPlainText()
            
            # 获取已保存的文件内容
            with open(currentFile, 'r', encoding='utf-8') as f:
                saved_content = f.read()
                
            # 如果内容相同，无需比较
            if current_content == saved_content:
                InfoBar.info(
                    title="内容相同",
                    content="当前内容与已保存文件相同",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建临时文件保存当前内容
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
            try:
                temp_path = temp_file.name
                temp_file.close()
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(current_content)
                
                # 调用外部diff工具或内部比较
                self.showDiffWindow(temp_path, currentFile, "当前未保存版本", "已保存版本")
            finally:
                # 确保删除临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "比较失败", f"比较文件失败: {str(e)}")
            
    def revertToSaved(self):
        """ 放弃更改，回退到已保存的版本 """
        currentFile = self.statusBar.getCurrentFile()
        if not currentFile or not os.path.exists(currentFile):
            InfoBar.warning(
                title="无法回退",
                content="没有已保存的文件可以回退",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            # 重新加载文件
            with open(currentFile, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查内容是否相同
            if content == self.editor.toPlainText():
                InfoBar.info(
                    title="无需回退",
                    content="当前内容没有修改，无需回退",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 确认是否回退
            reply = QMessageBox.question(
                self, "确认回退", 
                "确定要放弃所有未保存的更改，回退到已保存的版本吗？此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 设置编辑器内容
            self.editor.setPlainText(content)
            
            # 设置当前文件路径并标记为未修改
            self.editor.currentFilePath = currentFile
            self.editor.editor.document().setModified(False)
            
            InfoBar.success(
                title="回退成功",
                content="已成功回退到已保存版本",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "回退失败", f"回退到已保存版本失败: {str(e)}")
            
    def compareWithGitVersion(self):
        """ 比较当前文件与Git版本 """
        currentFile = self.statusBar.getCurrentFile()
        if not currentFile or not os.path.exists(currentFile):
            InfoBar.warning(
                title="无法比较",
                content="没有可比较的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            # 检查是否在Git仓库中
            repo_path = self.statusBar.getCurrentRepository()
            if not repo_path:
                InfoBar.warning(
                    title="未关联Git仓库",
                    content="当前文件不在Git仓库中，无法与Git版本比较",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建临时Git管理器
            gitManager = GitManager(repo_path)
            
            # 检查文件是否在Git跟踪中
            relative_path = os.path.relpath(currentFile, repo_path)
            if not gitManager.isFileTracked(relative_path):
                InfoBar.warning(
                    title="文件未跟踪",
                    content="当前文件未被Git跟踪，无法与Git版本比较",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 获取不同版本选择
            versions = gitManager.getFileCommitHistory(relative_path, max_count=10)
            if not versions:
                InfoBar.warning(
                    title="无历史版本",
                    content="找不到文件的历史版本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建版本选择对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QListWidgetItem
            
            dialog = QDialog(self)
            dialog.setWindowTitle("选择Git版本进行比较")
            layout = QVBoxLayout(dialog)
            
            # 列表显示可用版本
            versionList = QListWidget()
            for commit in versions:
                item = QListWidgetItem(f"{commit['hash'][:7]} - {commit['date']} - {commit['message']}")
                item.setData(Qt.UserRole, commit)
                versionList.addItem(item)
                
            layout.addWidget(versionList)
            
            # 添加确定和取消按钮
            buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttonBox.accepted.connect(dialog.accept)
            buttonBox.rejected.connect(dialog.reject)
            layout.addWidget(buttonBox)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted and versionList.currentItem():
                selected_commit = versionList.currentItem().data(Qt.UserRole)
                
                # 获取选中版本的文件内容
                git_content = gitManager.getFileContentAtCommit(relative_path, selected_commit['hash'])
                
                # 创建临时文件保存Git版本内容
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
                
                try:
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(git_content)
                    
                    # 调用diff工具比较
                    self.showDiffWindow(
                        currentFile, temp_path, 
                        "当前版本", 
                        f"Git版本 ({selected_commit['hash'][:7]} - {selected_commit['date']})"
                    )
                finally:
                    # 确保删除临时文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
        except Exception as e:
            QMessageBox.critical(self, "比较失败", f"比较文件失败: {str(e)}")
            
    def showDiffWindow(self, file1, file2, label1="文件1", label2="文件2"):
        """ 显示文件差异窗口 """
        try:
            # 导入所需模块
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QSplitter, QLabel
            from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor
            
            # 创建对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("文件比较")
            dialog.resize(900, 600)
            layout = QVBoxLayout(dialog)
            
            # 创建分割器
            splitter = QSplitter(Qt.Horizontal)
            
            # 左侧文件
            leftWidget = QWidget()
            leftLayout = QVBoxLayout(leftWidget)
            leftLayout.setContentsMargins(0, 0, 0, 0)
            
            leftLabel = QLabel(label1)
            leftLabel.setAlignment(Qt.AlignCenter)
            leftLayout.addWidget(leftLabel)
            
            leftText = QTextEdit()
            leftText.setReadOnly(True)
            with open(file1, 'r', encoding='utf-8') as f:
                leftText.setPlainText(f.read())
            leftLayout.addWidget(leftText)
            
            # 右侧文件
            rightWidget = QWidget()
            rightLayout = QVBoxLayout(rightWidget)
            rightLayout.setContentsMargins(0, 0, 0, 0)
            
            rightLabel = QLabel(label2)
            rightLabel.setAlignment(Qt.AlignCenter)
            rightLayout.addWidget(rightLabel)
            
            rightText = QTextEdit()
            rightText.setReadOnly(True)
            with open(file2, 'r', encoding='utf-8') as f:
                rightText.setPlainText(f.read())
            rightLayout.addWidget(rightText)
            
            # 添加到分割器
            splitter.addWidget(leftWidget)
            splitter.addWidget(rightWidget)
            
            # 高亮差异
            self.highlightDiff(leftText, rightText)
            
            layout.addWidget(splitter)
            
            # 显示对话框
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "显示比较失败", f"显示文件比较失败: {str(e)}")
            
    def highlightDiff(self, textEdit1, textEdit2):
        """ 高亮两个文本编辑器之间的差异 """
        text1 = textEdit1.toPlainText().splitlines()
        text2 = textEdit2.toPlainText().splitlines()
        
        # 简单差异比较，使用difflib
        import difflib
        matcher = difflib.SequenceMatcher(None, text1, text2)
        
        # 高亮格式
        addFormat = QTextCharFormat()
        addFormat.setBackground(QColor(200, 255, 200))  # 浅绿色，表示添加
        
        removeFormat = QTextCharFormat()
        removeFormat.setBackground(QColor(255, 200, 200))  # 浅红色，表示删除
        
        # 应用高亮
        cursor1 = textEdit1.textCursor()
        cursor1.setPosition(0)
        
        cursor2 = textEdit2.textCursor()
        cursor2.setPosition(0)
        
        # 追踪位置
        pos1 = 0
        pos2 = 0
        
        # 处理每个不同块
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            # 移动到差异位置并高亮
            if tag == 'replace' or tag == 'delete':
                # 高亮左侧的删除部分
                for i in range(i1, i2):
                    lineLen = len(text1[i]) if i < len(text1) else 0
                    cursor1.setPosition(pos1)
                    cursor1.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, lineLen)
                    cursor1.mergeCharFormat(removeFormat)
                    pos1 += lineLen + 1  # +1 for newline
            else:
                # 跳过相同部分或右侧插入的部分
                for i in range(i1, i2):
                    lineLen = len(text1[i]) if i < len(text1) else 0
                    pos1 += lineLen + 1  # +1 for newline
                    
            if tag == 'replace' or tag == 'insert':
                # 高亮右侧的添加部分
                for j in range(j1, j2):
                    lineLen = len(text2[j]) if j < len(text2) else 0
                    cursor2.setPosition(pos2)
                    cursor2.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, lineLen)
                    cursor2.mergeCharFormat(addFormat)
                    pos2 += lineLen + 1  # +1 for newline
            else:
                # 跳过相同部分或左侧删除的部分
                for j in range(j1, j2):
                    lineLen = len(text2[j]) if j < len(text2) else 0
                    pos2 += lineLen + 1  # +1 for newline 

    def setupShortcuts(self):
        """ 设置全局快捷键 """
        from PyQt5.QtWidgets import QShortcut
        
        # 保存快捷键
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveShortcut.activated.connect(self.saveFile)
        
        # 另存为快捷键
        saveAsShortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        saveAsShortcut.activated.connect(self.saveFileAs)
        
        # 比较文件快捷键
        compareShortcut = QShortcut(QKeySequence("Ctrl+K,D"), self)
        compareShortcut.activated.connect(self.compareWithSaved)

    def revertToGitVersion(self):
        """ 回退文件到指定Git版本 """
        currentFile = self.statusBar.getCurrentFile()
        if not currentFile or not os.path.exists(currentFile):
            InfoBar.warning(
                title="无法回退",
                content="没有当前文件可以回退",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        try:
            # 检查是否在Git仓库中
            repo_path = self.statusBar.getCurrentRepository()
            if not repo_path:
                InfoBar.warning(
                    title="未关联Git仓库",
                    content="当前文件不在Git仓库中，无法回退到Git版本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建临时Git管理器
            gitManager = GitManager(repo_path)
            
            # 检查文件是否在Git跟踪中
            relative_path = os.path.relpath(currentFile, repo_path)
            if not gitManager.isFileTracked(relative_path):
                InfoBar.warning(
                    title="文件未跟踪",
                    content="当前文件未被Git跟踪，无法回退到Git版本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 获取不同版本选择
            versions = gitManager.getFileCommitHistory(relative_path, max_count=10)
            if not versions:
                InfoBar.warning(
                    title="无历史版本",
                    content="找不到文件的历史版本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 创建版本选择对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QListWidgetItem
            
            dialog = QDialog(self)
            dialog.setWindowTitle("选择要回退到的Git版本")
            layout = QVBoxLayout(dialog)
            
            # 列表显示可用版本
            versionList = QListWidget()
            for commit in versions:
                item = QListWidgetItem(f"{commit['hash'][:7]} - {commit['date']} - {commit['message']}")
                item.setData(Qt.UserRole, commit)
                versionList.addItem(item)
                
            layout.addWidget(versionList)
            
            # 添加确定和取消按钮
            buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttonBox.accepted.connect(dialog.accept)
            buttonBox.rejected.connect(dialog.reject)
            layout.addWidget(buttonBox)
            
            # 显示对话框
            if dialog.exec_() == QDialog.Accepted and versionList.currentItem():
                selected_commit = versionList.currentItem().data(Qt.UserRole)
                
                # 确认是否回退
                reply = QMessageBox.question(
                    self, "确认回退", 
                    f"确定要回退到 {selected_commit['hash'][:7]} - {selected_commit['date']} 的版本吗？\n"
                    f"此操作会覆盖当前文件的内容，且未保存的更改将丢失。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                    
                # 回退文件到选中的版本
                if gitManager.revertFileToCommit(relative_path, selected_commit['hash']):
                    # 重新加载文件到编辑器
                    with open(currentFile, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.editor.setPlainText(content)
                        
                    # 标记为已修改，以便用户可以选择重新保存
                    self.editor.document().setModified(True)
                    
                    InfoBar.success(
                        title="回退成功",
                        content=f"已成功回退到 {selected_commit['hash'][:7]} 的版本",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title="回退失败",
                        content="回退到Git版本失败，请检查文件权限和状态",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    
        except Exception as e:
            QMessageBox.critical(self, "回退失败", f"回退到Git版本失败: {str(e)}") 

    def checkAutoSaveRecovery(self):
        """ 检查是否有自动保存文件需要恢复 """
        if hasattr(self, 'editor') and hasattr(self.editor, 'recoverFromAutoSave'):
            recovered = self.editor.recoverFromAutoSave()
            if recovered:
                InfoBar.success(
                    title="恢复成功",
                    content="已从自动保存文件恢复内容",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                ) 

    def closeEvent(self, event):
        """ 在关闭窗口前检查是否有未保存的更改 """
        if hasattr(self, 'editor') and hasattr(self.editor, 'editor') and self.editor.editor.document().isModified():
            reply = QMessageBox.question(
                self, "保存更改", 
                "文档有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # 尝试保存
                saved = self.saveFile()
                if not saved:
                    # 如果保存失败且用户取消了另存为，则取消关闭
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                # 取消关闭
                event.ignore()
                return
        
        # 停止自动保存定时器
        if hasattr(self, 'editor') and hasattr(self.editor, 'autoSaveTimer'):
            self.editor.autoSaveTimer.stop()
            
        # 移除自动保存文件
        if hasattr(self, 'editor') and hasattr(self.editor, 'autoSavePath'):
            try:
                import os
                if os.path.exists(self.editor.autoSavePath):
                    os.remove(self.editor.autoSavePath)
            except:
                pass
        
        # 接受关闭事件
        event.accept() 