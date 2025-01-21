import os
import sys
import atexit

def cleanup():
    """清理函数"""
    # 确保所有子进程被终止
    if hasattr(os, 'killpg'):
        os.killpg(os.getpgid(0), 9)
    else:
        os._exit(0)

# 注册清理函数
atexit.register(cleanup) 