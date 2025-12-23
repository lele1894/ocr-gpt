#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR-GPT Build Script
Use PyInstaller to package Python program into exe file
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Set environment variable for GitHub Actions
if 'GITHUB_ACTIONS' in os.environ:
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def safe_print(text):
    """Safe print function for different environments"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-only output in problematic environments
        print(text.encode('ascii', 'replace').decode('ascii'))

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            safe_print(f"Cleaning directory: {dir_name}")
            shutil.rmtree(dir_name)
    
    # Delete .spec files
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        safe_print(f"Deleting file: {spec_file}")
        spec_file.unlink()

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import PyInstaller
        safe_print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        safe_print("PyInstaller not installed, installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Check other dependencies
    required_modules = ['requests', 'pyautogui', 'keyboard', 'PIL']
    for module in required_modules:
        try:
            __import__(module)
            safe_print(f"✓ {module} installed")
        except ImportError:
            safe_print(f"✗ {module} not installed")
            return False
    return True

def create_version_file():
    """Create version info file"""
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
        StringStruct('FileDescription', 'OCR-GPT Text Recognition Assistant'),
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
    safe_print("✓ Version info file created")

def build_exe():
    """Build exe file"""
    safe_print("Starting build process...")
    
    # PyInstaller command arguments
    cmd = [
        'pyinstaller',
        '--onefile',                    # Package into single file
        '--windowed',                   # No console window
        '--name=OCR-GPT',              # Output filename
        '--clean',                      # Clean temp files
        '--noconfirm',                 # No confirmation for overwrite
        '--icon=ai.ico',               # Set icon
        '--version-file=version_info.txt',  # Version info
        # Hidden imports
        '--hidden-import=keyboard',
        '--hidden-import=pyautogui', 
        '--hidden-import=requests',
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.messagebox',
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=sklearn',
        '--exclude-module=seaborn',
        '--exclude-module=plotly',
        '--exclude-module=bokeh',
        '--exclude-module=sqlite3',  # 通常不需要的模块
        '--exclude-module=ssl',      # 如果不需要SSL可排除
        '--exclude-module=urllib3.contrib.pyopenssl',  # 减小体积
        '--strip',  # 从可执行文件中移除调试信息
        '--noupx',  # 不使用UPX压缩（如果可用）

        # Add data files
        '--add-data=ai.png;.',
        '--add-data=ai.ico;.',
        '--add-data=config_manager.py;.',
        # Main program file
        'text_search.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        safe_print("✓ Build successful!")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"✗ Build failed: {e}")
        safe_print(f"Error output: {e.stderr}")
        return False

def post_build():
    """打包后处理"""
    dist_dir = Path('dist')
    if dist_dir.exists():
        exe_file = dist_dir / 'OCR-GPT.exe'
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            safe_print(f"✓ Generated file: {exe_file}")
            safe_print(f"✓ File size: {size_mb:.2f} MB")
            
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
            safe_print(f"✓ Usage instructions created: {readme_file}")
        else:
            safe_print("✗ Generated exe file not found")
    else:
        safe_print("✗ dist directory does not exist")

def main():
    """Main function"""
    safe_print("=" * 50)
    safe_print("OCR-GPT Build Tool")
    safe_print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        safe_print("✗ Dependency check failed, please install required dependencies first")
        return
    
    # Clean build directories
    clean_build_dirs()
    
    # Create version file
    create_version_file()
    
    # Start building
    if build_exe():
        post_build()
        safe_print("\n✓ Build completed! Please check the dist directory")
    else:
        safe_print("\n✗ Build failed")

if __name__ == '__main__':
    main()