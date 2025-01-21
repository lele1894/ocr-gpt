# OCR-GPT

一个基于 GPT 的文本助手，支持截图 OCR 和智能问答。

## 功能特点

- 快捷键截图识别文本（Alt+1）
- GPT 智能问答
- 支持文本编辑和自定义提问
- 界面简洁，操作便捷
- 支持自定义 API 配置
- 支持窗口置顶设置
- 支持回车快捷提问

## 使用说明

1. 运行程序后，按 Alt+1 可以截图识别文本
2. 直接在文本框中编辑或输入问题
3. 按回车或点击"提问"按钮获取 AI 回答
4. 点击"设置"按钮配置 API
5. 点击"置顶"可以让窗口保持在最上层

## API 配置

1. 百度 OCR（可选）：
   - 访问[百度 AI 开放平台](https://ai.baidu.com)
   - 注册账号并创建应用
   - 选择"文字识别"服务
   - 获取 API Key 和 Secret Key

2. GPT API：
   - 访问 [API 服务](https://free.v36.cm)
   - 注册账号获取 API Key
   - 默认 API 地址：https://free.v36.cm/v1/chat/completions

## 开发环境

- Python 3.8+
- customtkinter
- requests
- pyautogui
- keyboard
- Pillow

## 安装使用

1. 下载发布版本的 exe 文件
2. 直接运行即可使用
3. 首次使用请配置 API Key
4. 可在主界面设置窗口置顶

## 开发说明
bash
安装依赖
pip install -r requirements.txt
运行程序
python text_search.py

## License

MIT License
