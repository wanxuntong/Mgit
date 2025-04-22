#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

class ConfigManager(QObject):
    """ 配置管理类，用于保存和加载配置 """
    
    # 定义信号，当最近仓库列表更新时触发
    recentRepositoriesChanged = pyqtSignal()
    
    def __init__(self, config_file=None):
        """ 初始化配置管理器 
        Args:
            config_file: 配置文件路径，默认为用户目录下的.mgit/config.json
        """
        super().__init__()
        
        if config_file is None:
            # 默认配置文件位置
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, '.mgit')
            
            # 确保目录存在
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            self.config_file = os.path.join(config_dir, 'config.json')
        else:
            self.config_file = config_file
            
        # 默认配置
        self.config = {
            'recent_repositories': [],
            'theme': 'auto',
            'max_recent_count': 10
        }
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """ 加载配置 """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 更新配置，但保留默认值
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
        
    def save_config(self):
        """ 保存配置 """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            
    def add_recent_repository(self, repo_path):
        """ 添加最近使用的仓库 
        Args:
            repo_path: 仓库路径
        """
        # 确保路径格式一致
        repo_path = os.path.normpath(repo_path)
        
        # 如果已经是第一个仓库，不做任何操作
        if self.config['recent_repositories'] and self.config['recent_repositories'][0] == repo_path:
            return
            
        # 检查是否已经在列表中
        if repo_path in self.config['recent_repositories']:
            # 如果已经存在，移除旧的
            self.config['recent_repositories'].remove(repo_path)
            
        # 添加到列表开头
        self.config['recent_repositories'].insert(0, repo_path)
        
        # 限制数量
        max_count = self.config['max_recent_count']
        if len(self.config['recent_repositories']) > max_count:
            self.config['recent_repositories'] = self.config['recent_repositories'][:max_count]
            
        # 保存配置
        self.save_config()
        
        # 发出信号通知仓库列表已更新
        self.recentRepositoriesChanged.emit()
        
    def get_recent_repositories(self):
        """ 获取最近使用的仓库列表 
        Returns:
            list: 仓库路径列表
        """
        # 过滤掉不存在的仓库
        valid_repos = [repo for repo in self.config['recent_repositories'] 
                      if os.path.exists(repo) and os.path.exists(os.path.join(repo, '.git'))]
        
        # 更新配置
        if len(valid_repos) != len(self.config['recent_repositories']):
            self.config['recent_repositories'] = valid_repos
            self.save_config()
            # 如果有无效仓库被过滤，发出信号
            self.recentRepositoriesChanged.emit()
            
        return valid_repos
        
    def clear_recent_repositories(self):
        """ 清空最近使用的仓库列表 """
        self.config['recent_repositories'] = []
        self.save_config()
        
        # 发出信号通知仓库列表已清空
        self.recentRepositoriesChanged.emit()
        
    def set_theme(self, theme):
        """ 设置主题 
        Args:
            theme: 主题名称，可选值：'light', 'dark', 'auto'
        """
        self.config['theme'] = theme
        self.save_config()
        
    def get_theme(self):
        """ 获取主题 
        Returns:
            str: 主题名称
        """
        return self.config['theme'] 