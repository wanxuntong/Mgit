#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - Markdown笔记与Git版本控制
启动脚本
"""

import sys
import os
import subprocess
import platform
import time
from pathlib import Path
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass
# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# 确保当前目录在Python路径中
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# 导入日志模块
from src.utils.logger import info, warning, error, debug, critical

def check_git():
    """检查Git是否已安装并可用"""
    try:
        version = subprocess.check_output(["git", "--version"], 
                                        stderr=subprocess.DEVNULL, 
                                        universal_newlines=True)
        info(f"Git检查通过: {version.strip()}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        warning("未检测到Git，应用需要Git才能正常运行")
        return False

def install_git():
    """引导用户安装Git"""
    system = platform.system()
    
    if system == "Windows":
        info("Windows系统检测到，将尝试自动安装Git...")
        try:
            # 检查是否可以自动安装
            auto_install = input("是否允许自动下载并安装Git？(y/n): ").lower() == 'y'
            
            if auto_install:
                # 下载Git安装程序
                import urllib.request
                import tempfile
                
                info("正在下载Git安装程序...")
                
                # 检测系统架构，选择合适的安装包
                if platform.machine().endswith('64'):
                    download_url = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/Git-2.41.0-64-bit.exe"
                else:
                    download_url = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/Git-2.41.0-32-bit.exe"
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
                temp_file.close()
                installer_path = temp_file.name
                
                # 下载安装程序
                urllib.request.urlretrieve(download_url, installer_path)
                
                info("下载完成，正在安装Git...")
                info("请按照安装向导完成安装...")
                
                # 运行安装程序
                # 使用静默安装参数 /VERYSILENT 可以实现无界面安装，但有些用户可能希望自定义安装选项
                subprocess.run([installer_path])
                
                info("请等待Git安装完成...")
                
                # 等待安装并检测安装结果
                for _ in range(30):  # 等待最多30秒
                    time.sleep(1)
                    if check_git():
                        info("Git安装成功!")
                        try:
                            os.remove(installer_path)  # 删除安装程序
                        except:
                            pass
                        return True
                
                warning("自动安装可能未完成，请确认Git安装状态")
                try:
                    os.remove(installer_path)  # 尝试删除安装程序
                except:
                    pass
                    
                if check_git():
                    return True
                
            # 如果用户选择手动安装或自动安装失败
            info("请按照以下步骤手动安装Git:")
            info("1. 访问 https://git-scm.com/download/win 下载Git安装程序")
            info("2. 运行安装程序并按照向导完成安装")
            info("3. 安装完成后重启此应用")
        except Exception as e:
            error(f"自动安装Git失败: {str(e)}")
            info("请按照以下步骤手动安装Git:")
            info("1. 访问 https://git-scm.com/download/win 下载Git安装程序")
            info("2. 运行安装程序并按照向导完成安装")
            info("3. 安装完成后重启此应用")
    elif system == "Darwin":  # macOS
        info("请按照以下步骤安装Git:")
        info("1. 打开终端，输入 'xcode-select --install' 并按Enter")
        info("2. 按照弹出的提示安装开发者工具（包含Git）")
        info("3. 安装完成后重启此应用")
    elif system == "Linux":
        distro = ""
        try:
            # 尝试获取Linux发行版
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except:
            pass
        
        if distro in ["ubuntu", "debian", "mint"]:
            info("请在终端中执行:")
            info("sudo apt update && sudo apt install git")
        elif distro in ["fedora", "rhel", "centos"]:
            info("请在终端中执行:")
            info("sudo dnf install git")
        elif distro in ["arch", "manjaro"]:
            info("请在终端中执行:")
            info("sudo pacman -S git")
        else:
            info("请使用您的软件包管理器安装Git")
        
        info("安装完成后重启此应用")
    else:
        info("请访问 https://git-scm.com/downloads 下载适合您系统的Git安装程序")
        info("安装完成后重启此应用")
    
    user_input = input("是否已完成Git安装？(y/n): ")
    return user_input.lower() == 'y'

def check_git_config():
    """检查Git的基础配置，确保user.name和user.email已设置"""
    if not check_git():
        return False
        
    try:
        # 检查user.name
        name_output = subprocess.check_output(
            ["git", "config", "--get", "user.name"], 
            stderr=subprocess.DEVNULL, 
            universal_newlines=True
        ).strip()
        
        # 检查user.email
        email_output = subprocess.check_output(
            ["git", "config", "--get", "user.email"], 
            stderr=subprocess.DEVNULL, 
            universal_newlines=True
        ).strip()
        
        if name_output and email_output:
            info(f"Git配置检查通过: user.name={name_output}, user.email={email_output}")
            return True
        else:
            warning("Git配置不完整，需要设置用户名和邮箱")
            return False
    except subprocess.SubprocessError:
        warning("Git配置未设置，需要配置用户名和邮箱")
        return False

def setup_git_config():
    """设置Git的基础配置"""
    info("Git需要设置用户名和邮箱才能正常使用")
    info("这些信息仅用于记录提交者，不会被用于其他用途")
    
    try:
        # 获取用户名
        name = input("请输入您的名字 (如: 张三): ")
        if not name:
            warning("用户名不能为空")
            return False
        
        # 获取邮箱
        email = input("请输入您的邮箱 (如: email@example.com): ")
        if not email or '@' not in email:
            warning("邮箱格式不正确")
            return False
        
        # 设置Git配置
        subprocess.check_call(["git", "config", "--global", "user.name", name])
        subprocess.check_call(["git", "config", "--global", "user.email", email])
        
        info("Git配置成功设置!")
        return True
    except subprocess.SubprocessError as e:
        error(f"Git配置设置失败: {str(e)}")
        return False

def check_environment():
    """检查并设置运行环境"""
    info("正在检查Git环境...")
    
    # 检查Git
    git_available = check_git()
    if not git_available:
        if not install_git():
            error("请安装Git后再运行此应用")
            sys.exit(1)
    
    # 检查Git配置
    git_config_valid = check_git_config()
    if not git_config_valid:
        if not setup_git_config():
            warning("请完成Git配置后再运行此应用")
            warning("您可以通过以下命令手动配置:")
            warning("git config --global user.name \"您的名字\"")
            warning("git config --global user.email \"您的邮箱\"")
            sys.exit(1)
    
    info("Git环境检查完成")
    info("-" * 50)

if __name__ == "__main__":
    # 检查环境
    check_environment()
    
    # 启动应用
    info("正在启动MGit应用...")
    from src.main import main
    main() 