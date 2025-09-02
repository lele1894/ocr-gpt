@echo off
chcp 65001 >nul
echo 开始打包 OCR-GPT...
echo.

python build.py

echo.
echo 打包完成，按任意键退出...
pause >nul