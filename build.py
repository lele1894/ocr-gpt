#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR-GPT 打包脚本
使用 PyInstaller 将 Python 程序打包为 exe 文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 删除 .spec 文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"删除文件: {spec_file}")
        spec_file.unlink()

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 检查其他依赖
    required_modules = ['requests', 'pyautogui', 'keyboard', 'PIL']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} 已安装")
        except ImportError:
            print(f"✗ {module} 未安装")
            return False
    return True

def create_version_file():
    """创建版本信息文件"""
    version_content = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '080404b0',
        [StringStruct('CompanyName', 'OCR-GPT Team'),
        StringStruct('FileDescription', 'OCR-GPT 文本识别助手'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', 'OCR-GPT'),
        StringStruct('LegalCopyright', 'Copyright © 2024'),
        StringStruct('OriginalFilename', 'OCR-GPT.exe'),
        StringStruct('ProductName', 'OCR-GPT'),
        StringStruct('ProductVersion', '1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)"""
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)
    print("✓ 版本信息文件已创建")

def build_exe():
    """构建 exe 文件"""
    print("开始打包...")
    
    # PyInstaller 命令参数
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包成单个文件
        '--windowed',                   # 不显示控制台窗口
        '--name=OCR-GPT',              # 指定输出文件名
        '--clean',                      # 清理临时文件
        '--noconfirm',                 # 不要确认覆盖
        '--icon=ai.ico',               # 设置图标
        '--version-file=version_info.txt',  # 版本信息
        # 隐藏导入的模块
        '--hidden-import=keyboard',
        '--hidden-import=pyautogui', 
        '--hidden-import=requests',
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.messagebox',
        # 排除不需要的模块以减小体积
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        # 添加数据文件
        '--add-data=ai.png;.',
        '--add-data=ai.ico;.',
        '--add-data=config_manager.py;.',
        # 主程序文件
        'text_search.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ 打包成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        print("错误输出:", e.stderr)
        return False

def post_build():
    """打包后处理"""
    dist_dir = Path('dist')
    if dist_dir.exists():
        exe_file = dist_dir / 'OCR-GPT.exe'
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"✓ 生成的文件: {exe_file}")
            print(f"✓ 文件大小: {size_mb:.2f} MB")
            
            # 创建使用说明
            readme_content = """# OCR-GPT 使用说明

## 功能介绍
OCR-GPT 是一个基于 GPT 的文本助手，提供截图 OCR 和智能问答功能。

## 主要功能
- 截图识别文本（快捷键 Alt+1）
- GPT 智能问答
- 文本编辑和自定义提问
- 窗口置顶设置
- 自定义 API 配置

## 使用方法
1. 双击运行 OCR-GPT.exe
2. 首次使用需要在"设置"中配置 API 密钥
3. 按 Alt+1 进行截图识别
4. 在文本框中输入问题，点击"提问"或按回车键

## API 配置
### 百度 OCR（可选）
- 访问：https://ai.baidu.com
- 获取 API Key 和 Secret Key

### GPT API（必需）
- 推荐：https://free.v36.cm
- 获取 API Key

## 注意事项
- 首次运行可能需要安装字体
- 杀毒软件可能误报，请添加信任
- 需要网络连接以使用 API 服务

## 技术支持
如有问题请访问项目主页或提交 Issue。
"""
            
            readme_file = dist_dir / '使用说明.md'
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"✓ 使用说明已创建: {readme_file}")
        else:
            print("✗ 未找到生成的 exe 文件")
    else:
        print("✗ dist 目录不存在")

def main():
    """主函数"""
    print("=" * 50)
    print("OCR-GPT 打包工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("✗ 依赖检查失败，请先安装所需依赖")
        return
    
    # 清理构建目录
    clean_build_dirs()
    
    # 创建版本文件
    create_version_file()
    
    # 开始打包
    if build_exe():
        post_build()
        print("\n✓ 打包完成! 请查看 dist 目录")
    else:
        print("\n✗ 打包失败")

if __name__ == '__main__':
    main()