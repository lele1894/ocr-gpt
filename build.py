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
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'PIL':
                import PIL
                safe_print(f"✓ {module} installed")
            elif module == 'requests':
                import requests
                safe_print(f"✓ {module} installed")
            elif module == 'pyautogui':
                import pyautogui
                safe_print(f"✓ {module} installed")
            elif module == 'keyboard':
                import keyboard
                safe_print(f"✓ {module} installed")
        except ImportError:
            safe_print(f"✗ {module} not installed")
            missing_modules.append(module)
    
    if missing_modules:
        safe_print(f"Installing missing modules: {missing_modules}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            safe_print("Dependencies installed from requirements.txt")
        except subprocess.CalledProcessError:
            # If requirements.txt install fails, try installing individually
            for module in missing_modules:
                try:
                    safe_print(f"Installing {module}...")
                    pip_module = module.replace('PIL', 'Pillow')  # PIL is installed as Pillow
                    subprocess.run([sys.executable, "-m", "pip", "install", pip_module], check=True)
                    safe_print(f"✓ {module} installed successfully")
                except subprocess.CalledProcessError:
                    safe_print(f"✗ Failed to install {module}")
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
    
    # PyInstaller command arguments - using standard approach
    cmd = [
        'pyinstaller',
        '--onefile',                    # Package into single file
        '--windowed',                   # No console window
        '--name=OCR-GPT',              # Output filename
        '--clean',                      # Clean temp files
        '--noconfirm',                 # No confirmation for overwrite
        '--icon=ai.ico',               # Set icon
        '--version-file=version_info.txt',  # Version info
        # Hidden imports for required modules
        '--hidden-import=keyboard',
        '--hidden-import=pyautogui', 
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=urllib3.util',
        '--hidden-import=urllib3.connection',
        '--hidden-import=ssl',
        '--hidden-import=_ssl',
        '--hidden-import=hashlib',
        '--hidden-import=certifi',
        '--hidden-import=encodings',
        '--hidden-import=encodings.idna',
        '--hidden-import=encodings.utf_8',
        '--hidden-import=encodings.latin_1',
        '--hidden-import=codecs',
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
        # Don't exclude SSL modules as they're essential
        '--strip',  # Remove debug info from executable
        '--noupx',  # Don't use UPX compression
        # Add data files
        '--add-data=ai.png;.',
        '--add-data=ai.ico;.',
        # Main program file
        'text_search.py'
    ]
    
    # In GitHub Actions, use onedir mode to ensure proper DLL handling
    if 'GITHUB_ACTIONS' in os.environ:
        # Replace --onefile with --onedir in the command
        cmd[2] = '--onedir'  # Change from --onefile to --onedir
        safe_print("Running in GitHub Actions, using --onedir mode")
        
        # Add SSL-related imports for GitHub Actions environment
        cmd.extend([
            '--hidden-import=_hashlib',
            '--collect-all=ssl',
            '--collect-all=_ssl'
        ])
    else:
        safe_print("Running in local environment, using --onefile mode")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        safe_print("✓ Build successful!")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"✗ Build failed: {e}")
        safe_print(f"Error output: {e.stderr}")
        safe_print(f"Standard output: {e.stdout}")
        return False

def post_build():
    """打包后处理"""
    dist_dir = Path('dist')
    if dist_dir.exists():
        # Check for both possible outputs (onefile vs onedir)
        exe_file = dist_dir / 'OCR-GPT.exe'
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            safe_print(f"✓ Generated file: {exe_file}")
            safe_print(f"✓ File size: {size_mb:.2f} MB")
            # Verify the executable is not corrupted
            verify_exe_file(exe_file)
        else:
            # For onedir mode, check in subdirectory
            exe_dir = dist_dir / 'OCR-GPT'
            exe_file = exe_dir / 'OCR-GPT.exe'
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                safe_print(f"✓ Generated file: {exe_file}")
                safe_print(f"✓ File size: {size_mb:.2f} MB")
                # Verify the executable is not corrupted
                verify_exe_file(exe_file)
            else:
                safe_print("✗ Generated exe file not found")
                # List contents of dist directory
                safe_print("Contents of dist directory:")
                for item in dist_dir.iterdir():
                    size = item.stat().st_size
                    size_mb = size / (1024 * 1024) if size > 1024 * 1024 else size / 1024
                    unit = "MB" if size > 1024 * 1024 else "KB"
                    safe_print(f"  - {item.name} ({size_mb:.2f} {unit})")
    else:
        safe_print("✗ dist directory does not exist")


def verify_exe_file(exe_path):
    """Verify the executable file integrity"""
    try:
        # Check file size and creation time
        stat_info = exe_path.stat()
        size_mb = stat_info.st_size / (1024 * 1024)
        safe_print(f"✓ File size verification: {size_mb:.2f} MB")
        
        # Try to open file stream to check if file is accessible
        with open(exe_path, 'rb') as f:
            f.seek(0)
            safe_print("✓ File accessibility verification: OK")
        
        safe_print("✓ Executable integrity verification passed")
    except Exception as e:
        safe_print(f"✗ Executable verification failed: {str(e)}")

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