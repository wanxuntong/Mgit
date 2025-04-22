#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - Markdown笔记与Git版本控制
启动脚本
"""

import sys
import os

# 确保当前目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 启动应用
    from src.main import main
    main() 