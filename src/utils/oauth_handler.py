#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import webbrowser
import threading
import urllib3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调的HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求，提取授权码并传递给回调函数"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 发送HTTP响应
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if parsed_path.path == '/github/callback' and 'code' in query_params:
            # GitHub OAuth回调
            code = query_params['code'][0]
            response_html = """
            <html>
            <head><title>认证成功</title></head>
            <body>
                <h1>GitHub认证成功</h1>
                <p>授权已完成，你可以关闭此窗口并返回应用。</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            self.wfile.write(response_html.encode('utf-8'))
            
            # 将授权码传递给处理函数
            if hasattr(self.server, 'github_callback') and self.server.github_callback:
                self.server.github_callback(code)
                
        elif parsed_path.path == '/gitlab/callback' and 'code' in query_params:
            # GitLab OAuth回调
            code = query_params['code'][0]
            response_html = """
            <html>
            <head><title>认证成功</title></head>
            <body>
                <h1>GitLab认证成功</h1>
                <p>授权已完成，你可以关闭此窗口并返回应用。</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            self.wfile.write(response_html.encode('utf-8'))
            
            # 将授权码传递给处理函数
            if hasattr(self.server, 'gitlab_callback') and self.server.gitlab_callback:
                self.server.gitlab_callback(code)
                
        else:
            # 无效的回调
            response_html = """
            <html>
            <head><title>认证失败</title></head>
            <body>
                <h1>认证失败</h1>
                <p>无效的回调请求或缺少授权码。</p>
                <script>setTimeout(function() { window.close(); }, 3000);</script>
            </body>
            </html>
            """
            self.wfile.write(response_html.encode('utf-8'))

class OAuthHandler(QObject):
    """OAuth授权流程处理器"""
    
    # 定义信号
    githubAuthSuccess = pyqtSignal(str)  # 参数：授权码
    githubAuthFailed = pyqtSignal(str)   # 参数：错误信息
    gitlabAuthSuccess = pyqtSignal(str)  # 参数：授权码
    gitlabAuthFailed = pyqtSignal(str)   # 参数：错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None
        self.server_thread = None
        self.host = "localhost"
        self.port = 8000
        
        # GitHub OAuth配置
        self.github_client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
        self.github_redirect_uri = f"http://{self.host}:{self.port}/github/callback"
        
        # GitLab OAuth配置
        self.gitlab_client_id = os.environ.get("GITLAB_CLIENT_ID", "")
        self.gitlab_client_secret = os.environ.get("GITLAB_CLIENT_SECRET", "")
        self.gitlab_redirect_uri = f"http://{self.host}:{self.port}/gitlab/callback"
        
    def start_server(self):
        """启动本地HTTP服务器监听OAuth回调"""
        if self.server:
            return
            
        try:
            self.server = HTTPServer((self.host, self.port), OAuthCallbackHandler)
            
            # 设置回调函数
            self.server.github_callback = self._handle_github_code
            self.server.gitlab_callback = self._handle_gitlab_code
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            return True
        except Exception as e:
            print(f"启动OAuth回调服务器失败: {str(e)}")
            return False
            
    def stop_server(self):
        """停止HTTP服务器"""
        if self.server:
            self.server.shutdown()
            self.server = None
            self.server_thread = None
    
    def start_github_auth(self):
        """开始GitHub OAuth认证流程"""
        if not self.github_client_id:
            self.githubAuthFailed.emit("缺少GitHub Client ID配置")
            return False
            
        # 启动服务器（如果未启动）
        if not self.server and not self.start_server():
            self.githubAuthFailed.emit("无法启动OAuth回调服务器")
            return False
            
        # 构建GitHub OAuth授权URL
        auth_url = (
            "https://github.com/login/oauth/authorize"
            f"?client_id={self.github_client_id}"
            f"&redirect_uri={self.github_redirect_uri}"
            "&scope=repo"
        )
        
        # 打开浏览器进行授权
        webbrowser.open(auth_url)
        return True
        
    def start_gitlab_auth(self, gitlab_url):
        """开始GitLab OAuth认证流程
        Args:
            gitlab_url: GitLab实例URL
        """
        if not self.gitlab_client_id:
            self.gitlabAuthFailed.emit("缺少GitLab Client ID配置")
            return False
            
        # 确保URL格式正确
        if not gitlab_url.endswith('/'):
            gitlab_url += '/'
            
        # 启动服务器（如果未启动）
        if not self.server and not self.start_server():
            self.gitlabAuthFailed.emit("无法启动OAuth回调服务器")
            return False
            
        # 构建GitLab OAuth授权URL
        auth_url = (
            f"{gitlab_url}oauth/authorize"
            f"?client_id={self.gitlab_client_id}"
            f"&redirect_uri={self.gitlab_redirect_uri}"
            "&response_type=code"
            "&scope=api"
        )
        
        # 打开浏览器进行授权
        webbrowser.open(auth_url)
        return True
    
    def _handle_github_code(self, code):
        """处理GitHub OAuth回调中的授权码"""
        self.githubAuthSuccess.emit(code)
    
    def _handle_gitlab_code(self, code):
        """处理GitLab OAuth回调中的授权码"""
        self.gitlabAuthSuccess.emit(code)

class OAuthBrowserDialog(QDialog):
    """内置浏览器的OAuth授权对话框"""
    
    # 定义信号
    authSuccess = pyqtSignal(str)  # 参数：授权码
    authFailed = pyqtSignal(str)   # 参数：错误信息
    
    def __init__(self, auth_url, redirect_uri_base, parent=None):
        super().__init__(parent)
        self.auth_url = auth_url
        self.redirect_uri_base = redirect_uri_base
        self.code = None
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("账号授权")
        self.resize(800, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 状态标签
        self.statusLabel = QLabel("请在下方登录并授权访问")
        layout.addWidget(self.statusLabel)
        
        # 进度条
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        layout.addWidget(self.progressBar)
        
        # 浏览器视图
        self.webView = QWebEngineView()
        self.webView.load(QUrl(self.auth_url))
        layout.addWidget(self.webView)
        
        # 连接信号
        self.webView.loadProgress.connect(self.progressBar.setValue)
        self.webView.urlChanged.connect(self._check_redirect)
        
        # 按钮区域
        buttonLayout = QHBoxLayout()
        
        self.cancelButton = QPushButton("取消")
        self.cancelButton.clicked.connect(self.reject)
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.cancelButton)
        
        layout.addLayout(buttonLayout)
        
    def _check_redirect(self, url):
        """检查URL是否是重定向URI，并提取授权码"""
        url_str = url.toString()
        
        if url_str.startswith(self.redirect_uri_base):
            query = url.query()
            for param in query.split('&'):
                if param.startswith('code='):
                    self.code = param.split('=')[1]
                    self.authSuccess.emit(self.code)
                    self.accept()
                    break
            
            if not self.code and 'error' in query:
                self.authFailed.emit("授权被拒绝或发生错误")
                self.reject() 