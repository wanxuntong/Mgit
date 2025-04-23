#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
import requests
import base64
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import urllib3

# 导入日志工具
from src.utils.logger import info, warning, error, debug

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入PyGithub
try:
    from github import Github, Auth
    from github.GithubException import BadCredentialsException, UnknownObjectException
    PYGITHUB_AVAILABLE = True
except ImportError:
    PYGITHUB_AVAILABLE = False

class AccountManager(QObject):
    """ GitHub/GitLab账号管理类 """
    
    # 定义信号，当账号列表更新时触发
    accountsChanged = pyqtSignal()
    
    def __init__(self, accounts_file=None):
        """ 初始化账号管理器
        Args:
            accounts_file: 账号配置文件路径，默认为用户目录下的.mgit/accounts.json
        """
        super().__init__()
        
        if accounts_file is None:
            # 默认配置文件位置
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, '.mgit')
            
            # 确保目录存在
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            self.accounts_file = os.path.join(config_dir, 'accounts.json')
        else:
            self.accounts_file = accounts_file
            
        # 默认账号配置
        self.accounts = {
            'github': [],
            'gitlab': []
        }
        
        # 加载账号配置
        self.load_accounts()
        
    def load_accounts(self):
        """ 加载账号配置 """
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    loaded_accounts = json.load(f)
                    # 更新配置，但保留默认值
                    self.accounts.update(loaded_accounts)
        except Exception as e:
            print(f"加载账号配置文件失败: {str(e)}")
        
    def save_accounts(self):
        """ 保存账号配置 """
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=4)
                
            # 发出信号通知账号列表已更新
            self.accountsChanged.emit()
        except Exception as e:
            print(f"保存账号配置文件失败: {str(e)}")
            
    def add_github_account(self, username, token, name=None):
        """ 添加GitHub账号
        Args:
            username: GitHub用户名
            token: GitHub访问令牌
            name: 账号别名，默认为用户名
        Returns:
            bool: 是否添加成功
        """
        # 验证账号
        if not self.verify_github_account(username, token):
            return False
            
        # 如果未提供别名，使用用户名
        if name is None:
            name = username
            
        # 检查是否已存在该账号
        for account in self.accounts['github']:
            if account['username'] == username:
                # 更新已有账号
                account['token'] = token
                account['name'] = name
                self.save_accounts()
                return True
                
        # 添加新账号
        self.accounts['github'].append({
            'username': username,
            'token': token,
            'name': name
        })
        
        # 保存更改
        self.save_accounts()
        return True
        
    def add_gitlab_account(self, url, token, name=None):
        """ 添加GitLab账号
        Args:
            url: GitLab实例URL
            token: GitLab访问令牌
            name: 账号别名，默认为从URL中提取
        Returns:
            bool: 是否添加成功
        """
        # 验证账号
        username = self.verify_gitlab_account(url, token)
        if not username:
            return False
            
        # 如果未提供别名，从URL中提取或使用用户名
        if name is None:
            from urllib.parse import urlparse
            name = urlparse(url).netloc.split('.')[0]
            if name == "gitlab":
                name = username
                
        # 检查是否已存在该账号
        for account in self.accounts['gitlab']:
            if account['url'] == url and account['username'] == username:
                # 更新已有账号
                account['token'] = token
                account['name'] = name
                self.save_accounts()
                return True
                
        # 添加新账号
        self.accounts['gitlab'].append({
            'url': url,
            'username': username,
            'token': token,
            'name': name
        })
        
        # 保存更改
        self.save_accounts()
        return True
        
    def add_github_account_oauth(self, code, client_id, client_secret, name=None):
        """ 通过OAuth方式添加GitHub账号
        Args:
            code: 从GitHub OAuth回调中获取的授权码
            client_id: GitHub OAuth应用的Client ID
            client_secret: GitHub OAuth应用的Client Secret
            name: 账号别名，默认为用户名
        Returns:
            bool: 是否添加成功
        """
        try:
            # 使用授权码获取访问令牌
            response = requests.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code
                },
                headers={'Accept': 'application/json'},
                verify=False  # 禁用SSL证书验证
            )
            
            if response.status_code != 200:
                print(f"获取GitHub访问令牌失败: {response.status_code} - {response.text}")
                return False
                
            # 解析响应获取访问令牌
            data = response.json()
            if 'access_token' not in data:
                print(f"GitHub OAuth响应中未找到访问令牌: {data}")
                return False
                
            token = data['access_token']
            
            # 获取用户信息
            user_response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'Bearer {token}'},
                verify=False  # 禁用SSL证书验证
            )
            
            if user_response.status_code != 200:
                print(f"获取GitHub用户信息失败: {user_response.status_code} - {user_response.text}")
                return False
                
            user_data = user_response.json()
            username = user_data['login']
            
            # 如果未提供别名，使用用户名
            if name is None:
                name = username
                
            # 检查是否已存在该账号
            for account in self.accounts['github']:
                if account['username'] == username:
                    # 更新已有账号
                    account['token'] = token
                    account['name'] = name
                    self.save_accounts()
                    return True
                    
            # 添加新账号
            self.accounts['github'].append({
                'username': username,
                'token': token,
                'name': name
            })
            
            # 保存更改
            self.save_accounts()
            return True
        except Exception as e:
            print(f"通过OAuth添加GitHub账号时出错: {str(e)}")
            return False
        
    def add_gitlab_account_oauth(self, code, redirect_uri, client_id, client_secret, gitlab_url, name=None):
        """ 通过OAuth方式添加GitLab账号
        Args:
            code: 从GitLab OAuth回调中获取的授权码
            redirect_uri: OAuth回调URL
            client_id: GitLab OAuth应用的Client ID
            client_secret: GitLab OAuth应用的Client Secret
            gitlab_url: GitLab实例URL
            name: 账号别名，默认从URL中提取
        Returns:
            bool: 是否添加成功
        """
        try:
            # 确保URL格式正确
            if not gitlab_url.endswith('/'):
                gitlab_url += '/'
                
            # 使用授权码获取访问令牌
            response = requests.post(
                f'{gitlab_url}oauth/token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri
                },
                verify=False  # 禁用SSL证书验证
            )
            
            if response.status_code != 200:
                print(f"获取GitLab访问令牌失败: {response.status_code} - {response.text}")
                return False
                
            # 解析响应获取访问令牌
            data = response.json()
            if 'access_token' not in data:
                print(f"GitLab OAuth响应中未找到访问令牌: {data}")
                return False
                
            token = data['access_token']
            
            # 获取用户信息
            user_response = requests.get(
                f'{gitlab_url}api/v4/user',
                headers={'Authorization': f'Bearer {token}'},
                verify=False  # 禁用SSL证书验证
            )
            
            if user_response.status_code != 200:
                print(f"获取GitLab用户信息失败: {user_response.status_code} - {user_response.text}")
                return False
                
            user_data = user_response.json()
            username = user_data['username']
            
            # 如果未提供别名，从URL中提取或使用用户名
            if name is None:
                from urllib.parse import urlparse
                name = urlparse(gitlab_url).netloc.split('.')[0]
                if name == "gitlab":
                    name = username
                    
            # 检查是否已存在该账号
            for account in self.accounts['gitlab']:
                if account['url'] == gitlab_url and account['username'] == username:
                    # 更新已有账号
                    account['token'] = token
                    account['name'] = name
                    self.save_accounts()
                    return True
                    
            # 添加新账号
            self.accounts['gitlab'].append({
                'url': gitlab_url,
                'username': username,
                'token': token,
                'name': name
            })
            
            # 保存更改
            self.save_accounts()
            return True
        except Exception as e:
            print(f"通过OAuth添加GitLab账号时出错: {str(e)}")
            return False
        
    def verify_github_account(self, username, token):
        """ 验证GitHub账号
        Args:
            username: GitHub用户名
            token: GitHub访问令牌
        Returns:
            bool: 账号是否有效
        """
        try:
            if PYGITHUB_AVAILABLE:
                # 使用PyGithub验证
                auth = Auth.Token(token)
                g = Github(auth=auth, verify=False)  # 禁用SSL证书验证
                user = g.get_user()
                # 验证返回的用户名是否与提供的用户名匹配
                result = user.login == username
                g.close()
                return result
            else:
                # 使用requests验证（备选方案）
                # 注意：GitHub API现在支持多种token格式，尝试不同的认证方式
                headers = {}
                
                # 尝试Bearer token格式
                if not token.startswith('ghp_') and not token.startswith('github_pat_'):
                    headers['Authorization'] = f'Bearer {token}'
                else:
                    # 使用传统的token格式
                    headers['Authorization'] = f'token {token}'
                
                response = requests.get(
                    'https://api.github.com/user',
                    headers=headers,
                    verify=False  # 禁用SSL证书验证
                )
                
                if response.status_code == 200:
                    # 验证返回的用户名是否与提供的用户名匹配
                    data = response.json()
                    return data['login'] == username
                    
                # 如果认证失败，输出详细信息以便调试
                print(f"GitHub认证失败: 状态码 {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            print(f"GitHub账号验证出错: {str(e)}")
            return False
            
    def verify_gitlab_account(self, url, token):
        """ 验证GitLab账号
        Args:
            url: GitLab实例URL
            token: GitLab访问令牌
        Returns:
            str or False: 如果账号有效返回用户名，否则返回False
        """
        try:
            # 确保URL格式正确
            if not url.endswith('/'):
                url += '/'
                
            # 尝试多种认证方式
            # 1. 使用Private-Token
            headers_private = {'Private-Token': token}
            response = requests.get(
                f'{url}api/v4/user',
                headers=headers_private,
                verify=False  # 禁用SSL证书验证
            )
            
            if response.status_code == 200:
                # 获取并返回用户名
                data = response.json()
                return data['username']
                
            # 2. 如果Private-Token认证失败，尝试使用OAuth2 Bearer token
            if response.status_code == 401:
                headers_oauth = {'Authorization': f'Bearer {token}'}
                response = requests.get(
                    f'{url}api/v4/user',
                    headers=headers_oauth,
                    verify=False  # 禁用SSL证书验证
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['username']
            
            # 认证失败，输出详细信息以便调试
            print(f"GitLab认证失败: URL: {url}, 状态码: {response.status_code}, 响应: {response.text}")
            return False
        except Exception as e:
            print(f"GitLab账号验证出错: {str(e)}")
            return False
            
    def remove_github_account(self, username):
        """ 移除GitHub账号
        Args:
            username: GitHub用户名
        Returns:
            bool: 是否移除成功
        """
        for i, account in enumerate(self.accounts['github']):
            if account['username'] == username:
                self.accounts['github'].pop(i)
                self.save_accounts()
                return True
        return False
        
    def remove_gitlab_account(self, url, username):
        """ 移除GitLab账号
        Args:
            url: GitLab实例URL
            username: GitLab用户名
        Returns:
            bool: 是否移除成功
        """
        for i, account in enumerate(self.accounts['gitlab']):
            if account['url'] == url and account['username'] == username:
                self.accounts['gitlab'].pop(i)
                self.save_accounts()
                return True
        return False
        
    def get_github_accounts(self):
        """ 获取所有GitHub账号
        Returns:
            list: GitHub账号列表
        """
        return self.accounts['github']
        
    def get_gitlab_accounts(self):
        """ 获取所有GitLab账号
        Returns:
            list: GitLab账号列表
        """
        return self.accounts['gitlab']
        
    def create_github_repository(self, username, token, repo_name, description="", private=False):
        """ 在GitHub上创建新仓库
        Args:
            username: GitHub用户名
            token: GitHub访问令牌
            repo_name: 仓库名称
            description: 仓库描述，默认为空
            private: 是否为私有仓库，默认为False
        Returns:
            dict or False: 如果创建成功，返回仓库信息，否则返回False
        """
        try:
            debug(f"尝试为用户 {username} 创建GitHub仓库: {repo_name}")
            if PYGITHUB_AVAILABLE:
                # 使用PyGithub创建仓库
                auth = Auth.Token(token)
                g = Github(auth=auth, verify=False)  # 禁用SSL证书验证
                user = g.get_user()
                
                # 验证用户身份
                authenticated_username = user.login
                if authenticated_username != username:
                    warning(f"警告：授权用户 ({authenticated_username}) 与请求的用户 ({username}) 不匹配")
                
                # 创建仓库，不进行自动初始化
                repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    auto_init=False  # 不自动初始化，改为在本地初始化后推送
                )
                
                # 打印仓库URL以便调试
                debug(f"GitHub仓库创建成功: {repo.clone_url}")
                
                # 转换为字典
                result = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "clone_url": repo.clone_url.rstrip('/'),  # 去除末尾斜杠
                    "ssh_url": repo.ssh_url.rstrip('/'),      # 去除末尾斜杠
                    "html_url": repo.html_url.rstrip('/')     # 去除末尾斜杠
                }
                
                g.close()
                return result
            else:
                # 使用requests创建仓库（备选方案）
                # 准备请求数据
                data = {
                    "name": repo_name,
                    "description": description,
                    "private": private,
                    "auto_init": False  # 不自动初始化，改为在本地初始化后推送
                }
                
                # 发送创建仓库请求
                response = requests.post(
                    'https://api.github.com/user/repos',
                    headers={'Authorization': f'token {token}'},
                    json=data,
                    verify=False  # 禁用SSL证书验证
                )
                
                if response.status_code in [201, 200]:  # 创建成功
                    info(f"使用REST API创建GitHub仓库成功: {repo_name}")
                    return response.json()
                else:
                    error(f"创建GitHub仓库失败: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            error(f"创建GitHub仓库时发生错误: {str(e)}")
            return False
            
    def create_gitlab_repository(self, url, token, repo_name, description="", visibility="public"):
        """ 在GitLab上创建新仓库
        Args:
            url: GitLab实例URL
            token: GitLab访问令牌
            repo_name: 仓库名称
            description: 仓库描述，默认为空
            visibility: 仓库可见性，可选值：'private', 'internal', 'public'，默认为'public'
        Returns:
            dict or False: 如果创建成功，返回仓库信息，否则返回False
        """
        try:
            # 确保URL格式正确
            if not url.endswith('/'):
                url += '/'
                
            # 准备请求数据
            data = {
                "name": repo_name,
                "description": description,
                "visibility": visibility,
                "initialize_with_readme": False  # 不自动初始化，改为在本地初始化后推送
            }
            
            # 发送创建仓库请求
            response = requests.post(
                f'{url}api/v4/projects',
                headers={'Private-Token': token},
                json=data,
                verify=False  # 禁用SSL证书验证
            )
            
            if response.status_code in [201, 200]:  # 创建成功
                info(f"创建GitLab仓库成功: {repo_name}")
                return response.json()
            else:
                error(f"创建GitLab仓库失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            error(f"创建GitLab仓库时发生错误: {str(e)}")
            return False 