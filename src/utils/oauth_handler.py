#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import webbrowser
import threading
import urllib3
import socket
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 导入日志模块
from src.utils.logger import info, warning, error, debug

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调请求的HTTP处理器"""
    
    def log_message(self, format, *args):
        """覆盖默认日志，使用自定义日志器"""
        debug(f"OAuthCallback: {format % args}")
        
    def _send_response(self, msg, status=200):
        """发送HTTP响应"""
        try:
            self.send_response(status)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            # 确保使用UTF-8编码，并处理任何编码错误
            if isinstance(msg, str):
                msg = msg.encode('utf-8', errors='xmlcharrefreplace')
            self.wfile.write(msg)
        except Exception as e:
            error(f"发送HTTP响应时出错: {str(e)}")
        
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query = parse_qs(parsed_path.query)
            
            if path == '/github/callback':
                # 处理GitHub回调
                if 'code' in query:
                    code = query['code'][0]
                    self.server.github_callback(code)
                    # 显示成功页面
                    self._send_response('''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitHub OAuth 成功</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                            h1 { color: #2c974b; }
                            p { font-size: 16px; }
                        </style>
                    </head>
                    <body>
                        <h1>GitHub 授权成功</h1>
                        <p>授权已完成，您可以关闭此页面并返回应用。</p>
                    </body>
                    </html>
                    ''')
                else:
                    # 显示错误页面
                    error_message = query.get('error_description', ['未知错误'])[0]
                    self._send_response(f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitHub OAuth 失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #cb2431; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>GitHub 授权失败</h1>
                        <p>错误信息: {error_message}</p>
                        <p>请关闭此页面并重试。</p>
                    </body>
                    </html>
                    ''', 400)
                    
            elif path == '/gitlab/callback':
                # 处理GitLab回调
                if 'code' in query:
                    code = query['code'][0]
                    self.server.gitlab_callback(code)
                    # 显示成功页面
                    self._send_response('''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitLab OAuth 成功</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                            h1 { color: #fc6d26; }
                            p { font-size: 16px; }
                        </style>
                    </head>
                    <body>
                        <h1>GitLab 授权成功</h1>
                        <p>授权已完成，您可以关闭此页面并返回应用。</p>
                    </body>
                    </html>
                    ''')
                else:
                    # 显示错误页面
                    error_message = query.get('error_description', ['未知错误'])[0]
                    self._send_response(f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitLab OAuth 失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #db3b21; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>GitLab 授权失败</h1>
                        <p>错误信息: {error_message}</p>
                        <p>请关闭此页面并重试。</p>
                    </body>
                    </html>
                    ''', 400)
            else:
                # 未知路径
                self._send_response('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                    <title>无效请求</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #24292e; }
                        p { font-size: 16px; }
                    </style>
                </head>
                <body>
                    <h1>无效请求</h1>
                    <p>请关闭此页面并返回应用。</p>
                </body>
                </html>
                ''', 404)
        except Exception as e:
            error(f"OAuth回调处理异常: {str(e)}")
            self._send_response(f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                <title>服务器错误</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    h1 {{ color: #cb2431; }}
                    p {{ font-size: 16px; }}
                </style>
            </head>
            <body>
                <h1>服务器错误</h1>
                <p>处理请求时发生错误: {str(e)}</p>
                <p>请关闭此页面并重试。</p>
            </body>
            </html>
            ''', 500)

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
        
        # 尝试多个端口，防止端口占用
        self.available_ports = [8000, 8080, 9000, 9090, 10000, 10800]
        self.port = self.available_ports[0]  # 默认使用第一个端口
        
        # GitHub OAuth配置
        self.github_client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
        self.github_redirect_uri = f"http://{self.host}:{self.port}/github/callback"
        
        # GitLab OAuth配置
        self.gitlab_client_id = os.environ.get("GITLAB_CLIENT_ID", "")
        self.gitlab_client_secret = os.environ.get("GITLAB_CLIENT_SECRET", "")
        self.gitlab_redirect_uri = f"http://{self.host}:{self.port}/gitlab/callback"
        
    def find_available_port(self):
        """查找可用的端口"""
        debug(f"正在搜索可用端口...")
        # 首先尝试默认端口
        for port in self.available_ports:
            try:
                # 尝试绑定端口
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((self.host, port))
                    info(f"找到可用端口: {port}")
                    return port
            except OSError as e:
                warning(f"端口 {port} 不可用: {e}")
        
        # 如果所有预定义端口都不可用，尝试随机端口
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, 0))  # 系统分配随机端口
                _, port = s.getsockname()
                info(f"使用随机分配的端口: {port}")
                return port
        except OSError as e:
            error(f"无法绑定任何端口: {str(e)}")
            return None
        
    def update_redirect_uris(self):
        """更新重定向URI，匹配当前使用的端口"""
        self.github_redirect_uri = f"http://{self.host}:{self.port}/github/callback"
        self.gitlab_redirect_uri = f"http://{self.host}:{self.port}/gitlab/callback"
        info(f"更新GitHub重定向URI: {self.github_redirect_uri}")
        info(f"更新GitLab重定向URI: {self.gitlab_redirect_uri}")
        
    def start_server(self):
        """启动本地HTTP服务器监听OAuth回调"""
        if self.server:
            info("OAuth服务器已运行")
            return True
            
        try:
            # 查找可用端口
            self.port = self.find_available_port()
            if not self.port:
                error("无法找到可用端口来启动OAuth服务器")
                if parent := self.parent():
                    QMessageBox.critical(
                        parent,
                        "端口绑定错误",
                        "无法找到可用端口来启动OAuth服务器。\n请检查您的网络设置或尝试重启应用。"
                    )
                return False
                
            # 更新重定向URI
            self.update_redirect_uris()
            
            # 创建HTTP服务器
            info(f"正在启动OAuth回调服务器，地址: {self.host}:{self.port}")
            
            try:
                self.server = HTTPServer((self.host, self.port), OAuthCallbackHandler)
                # 设置SO_REUSEADDR选项
                self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception as server_error:
                error(f"创建HTTP服务器失败: {str(server_error)}")
                
                # 尝试使用不同的设置
                try:
                    info("尝试使用备选配置启动服务器...")
                    # 改用0.0.0.0绑定所有接口
                    self.server = HTTPServer(("0.0.0.0", self.port), OAuthCallbackHandler)
                    self.host = "localhost"  # 保持URL中使用localhost
                    self.update_redirect_uris()  # 更新重定向URI
                    info(f"服务器绑定在0.0.0.0:{self.port}，但URL使用{self.host}")
                except Exception as alt_error:
                    error(f"备选配置也失败: {str(alt_error)}")
                    raise
            
            # 设置回调函数
            self.server.github_callback = self._handle_github_code
            self.server.gitlab_callback = self._handle_gitlab_code
            
            # 在单独的线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # 等待确认服务器已启动
            time.sleep(0.5)
            info(f"OAuth回调服务器已启动，监听地址: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            error(f"启动OAuth回调服务器失败: {str(e)}")
            
            # 显示详细错误信息
            if hasattr(sys, '_MEIPASS'):
                error(f"在PyInstaller环境中运行，临时目录: {sys._MEIPASS}")
            error(f"当前工作目录: {os.getcwd()}")
            
            # 尝试诊断网络问题
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(1)
                result = test_socket.connect_ex((self.host, self.port))
                test_socket.close()
                error(f"端口测试结果: {result} (0表示端口开放，非0表示有问题)")
            except Exception as socket_error:
                error(f"Socket测试出错: {str(socket_error)}")
                
            # 在非调试环境弹出错误窗口
            if parent := self.parent():
                QMessageBox.critical(
                    parent,
                    "OAuth服务器错误",
                    f"无法启动OAuth回调服务器:\n{str(e)}\n\n请检查网络连接和防火墙设置，或尝试重启应用。"
                )
            return False
            
    def stop_server(self):
        """停止HTTP服务器"""
        if self.server:
            info("正在停止OAuth回调服务器")
            try:
                self.server.shutdown()
                self.server = None
                self.server_thread = None
                info("OAuth回调服务器已停止")
            except Exception as e:
                error(f"停止OAuth服务器时出错: {str(e)}")
    
    def start_github_auth(self):
        """开始GitHub OAuth认证流程"""
        if not self.github_client_id:
            warning("缺少GitHub Client ID配置")
            self.githubAuthFailed.emit("缺少GitHub Client ID配置")
            return False
            
        # 启动服务器（如果未启动）
        if not self.server and not self.start_server():
            error("无法启动OAuth回调服务器，GitHub认证失败")
            self.githubAuthFailed.emit("无法启动OAuth回调服务器")
            return False
            
        # 构建GitHub OAuth授权URL
        auth_url = (
            "https://github.com/login/oauth/authorize"
            f"?client_id={self.github_client_id}"
            f"&redirect_uri={self.github_redirect_uri}"
            "&scope=repo"
        )
        
        info(f"开始GitHub OAuth认证流程，授权URL: {auth_url}")
        
        # 打开浏览器进行授权
        try:
            webbrowser.open(auth_url)
            info("已打开浏览器进行GitHub认证")
            return True
        except Exception as e:
            error(f"打开浏览器失败: {str(e)}")
            self.githubAuthFailed.emit(f"打开浏览器失败: {str(e)}")
            return False
        
    def start_gitlab_auth(self, gitlab_url):
        """开始GitLab OAuth认证流程
        Args:
            gitlab_url: GitLab实例URL
        """
        if not self.gitlab_client_id:
            warning("缺少GitLab Client ID配置")
            self.gitlabAuthFailed.emit("缺少GitLab Client ID配置")
            return False
            
        # 确保URL格式正确
        if not gitlab_url.endswith('/'):
            gitlab_url += '/'
            
        # 启动服务器（如果未启动）
        if not self.server and not self.start_server():
            error("无法启动OAuth回调服务器，GitLab认证失败")
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
        
        info(f"开始GitLab OAuth认证流程，授权URL: {auth_url}")
        
        # 打开浏览器进行授权
        try:
            webbrowser.open(auth_url)
            info("已打开浏览器进行GitLab认证")
            return True
        except Exception as e:
            error(f"打开浏览器失败: {str(e)}")
            self.gitlabAuthFailed.emit(f"打开浏览器失败: {str(e)}")
            return False
    
    def _handle_github_code(self, code):
        """处理GitHub OAuth回调中的授权码"""
        info(f"收到GitHub授权码，长度: {len(code)}")
        try:
            # 确保编码正确
            if isinstance(code, bytes):
                try:
                    code = code.decode('utf-8')
                except UnicodeDecodeError:
                    code = code.decode('utf-8', errors='replace')
                    warning("GitHub授权码包含无法解码的字符，已替换")
                    
            self.githubAuthSuccess.emit(code)
            
            # 尝试安全地关闭服务器
            try:
                self.stop_server()
            except Exception as shutdown_error:
                warning(f"关闭OAuth服务器时出现非致命错误: {str(shutdown_error)}")
        except Exception as e:
            error(f"处理GitHub授权码时出错: {str(e)}")
            self.githubAuthFailed.emit(f"处理授权码时出错: {str(e)}")
    
    def _handle_gitlab_code(self, code):
        """处理GitLab OAuth回调中的授权码"""
        info(f"收到GitLab授权码，长度: {len(code)}")
        try:
            # 确保编码正确
            if isinstance(code, bytes):
                try:
                    code = code.decode('utf-8')
                except UnicodeDecodeError:
                    code = code.decode('utf-8', errors='replace')
                    warning("GitLab授权码包含无法解码的字符，已替换")
                    
            self.gitlabAuthSuccess.emit(code)
            
            # 尝试安全地关闭服务器
            try:
                self.stop_server()
            except Exception as shutdown_error:
                warning(f"关闭OAuth服务器时出现非致命错误: {str(shutdown_error)}")
        except Exception as e:
            error(f"处理GitLab授权码时出错: {str(e)}")
            self.gitlabAuthFailed.emit(f"处理授权码时出错: {str(e)}")

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