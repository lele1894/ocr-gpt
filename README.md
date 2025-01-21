# AI Text Assistant

一个基于 GPT 的文本助手，支持截图 OCR 和智能问答。

## 功能特点

- 快捷键截图识别文本（Alt+1）
- GPT 智能问答
- 支持文本编辑和自定义提问
- 界面简洁，操作便捷
- 支持自定义 API 配置

## 使用说明

1. 运行程序后，按 Alt+1 可以截图识别文本
2. 直接在文本框中编辑或输入问题
3. 按回车或点击"提问"按钮获取 AI 回答
4. 点击设置按钮配置 API

## API 配置

1. 百度 OCR（可选）：
   - 访问[百度 AI 开放平台](https://ai.baidu.com)
   - 注册账号并创建应用
   - 获取 API Key 和 Secret Key

2. GPT API：
   - 访问 [API 服务](https://free.v36.cm)
   - 获取 API Key

## 开发环境

- Python 3.8+
- PyQt5
- requests
- pyautogui
- keyboard

## 安装使用

1. 下载发布版本的 exe 文件
2. 直接运行即可使用
3. 首次使用请配置 API Key

## License

MIT License 