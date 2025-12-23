import os
import atexit

def cleanup():
    """清理函数"""
    # 程序退出时的清理操作
    pass

# 注册清理函数
atexit.register(cleanup)