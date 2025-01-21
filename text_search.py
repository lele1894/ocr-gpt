import customtkinter as ctk
import pyautogui
import webbrowser
from PIL import Image, ImageTk
import sys
import io
import base64
import requests
import keyboard
import time
import json
import threading
import os
from config_manager import ConfigManager
import tkinter.ttk as ttk
from tkinter import ttk

class TextRecognizer:
    def __init__(self):
        self.capture_start = None
        self.is_capturing = False
        self.capture_window = None
        self.main_window = None
        
        # 加载配置
        self.config_manager = ConfigManager()
        config = self.config_manager.config
        
        # 百度OCR配置
        self.API_KEY = config['baidu_ocr']['api_key']
        self.SECRET_KEY = config['baidu_ocr']['secret_key']
        self.OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
        self.access_token = self.get_access_token() if self.API_KEY and self.SECRET_KEY else None
        
        # GPT配置
        self.GPT_API_URL = config['gpt']['api_url']
        self.GPT_API_KEY = config['gpt']['api_key']
        
        # 创建主窗口
        self.create_main_window()
        
    def get_access_token(self):
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.API_KEY}&client_secret={self.SECRET_KEY}"
        response = requests.get(url)
        return response.json().get("access_token")
    
    def create_main_window(self):
        """创建主窗口"""
        self.main_window = ctk.CTk()
        self.main_window.title("OCR-GPT")
        self.main_window.geometry("600x400")
        
        # 设置图标
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(application_path, 'ai.png')
        if os.path.exists(icon_path):
            icon = Image.open(icon_path)
            photo = ImageTk.PhotoImage(icon)
            self.main_window.wm_iconphoto(True, photo)
        
        # 创建文本区域
        text_label = ctk.CTkLabel(self.main_window, text="识别文本:", anchor="w")
        text_label.pack(fill="x", padx=10, pady=(10,0))
        
        # 添加边框样式的文本框
        self.text_input = ctk.CTkTextbox(self.main_window, height=100,
                                        border_width=1,  # 添加边框
                                        border_color="#E0E0E0")  # 设置边框颜色
        self.text_input.pack(fill="x", padx=10, pady=5)
        
        # 创建按钮区域
        button_frame = ctk.CTkFrame(self.main_window)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # 左侧按钮
        left_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        left_buttons.pack(side="left")
        
        ask_button = ctk.CTkButton(left_buttons, text="点击提问", command=self.on_ask,
                                  width=100, height=32)
        ask_button.pack(side="left", padx=5)
        
        clear_button = ctk.CTkButton(left_buttons, text="清空回答", 
                                    command=lambda: self.answer_text.delete("1.0", "end"),
                                    width=100, height=32)
        clear_button.pack(side="left", padx=5)
        
        settings_button = ctk.CTkButton(left_buttons, text="设置", command=self.show_settings,
                                      width=100, height=32)
        settings_button.pack(side="left", padx=5)
        
        # 创建回答区域
        answer_label = ctk.CTkLabel(self.main_window, text="AI回答:", anchor="w")
        answer_label.pack(fill="x", padx=10, pady=(10,0))
        
        # 添加边框样式的回答框
        self.answer_text = ctk.CTkTextbox(self.main_window,
                                         border_width=1,  # 添加边框
                                         border_color="#E0E0E0")  # 设置边框颜色
        self.answer_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 修复回车键绑定
        def handle_return(event):
            if not event.state & 0x1:  # 不是 Shift+Enter
                self.on_ask()
                return "break"  # 阻止默认的换行行为
        
        self.text_input.bind("<Return>", handle_return)
        
        # 设置窗口样式
        self.main_window.configure(fg_color="white")
        self.main_window.attributes('-alpha', 1.0)  # 设置透明度
        if sys.platform.startswith('win'):
            # Windows 平台
            self.main_window.wm_attributes('-topmost', True)
            self.main_window.update()
            # 移除标题栏但保留最小化功能
            style = self.main_window.style = ttk.Style()
            style.configure('CustomWindow.TFrame', background='white')
        else:
            # Linux/Mac 平台
            self.main_window.wm_attributes('-type', 'splash')
    
    def show_settings(self):
        """显示设置窗口"""
        settings = ctk.CTkToplevel(self.main_window)
        settings.title("设置")
        settings.geometry("400x500")
        settings.grab_set()
        
        # 添加置顶选项
        top_frame = ctk.CTkFrame(settings)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        top_var = ctk.BooleanVar(value=self.main_window.attributes('-topmost'))
        top_checkbox = ctk.CTkCheckBox(top_frame, text="窗口始终置顶",
                                      variable=top_var,
                                      command=lambda: self.main_window.attributes('-topmost', top_var.get()))
        top_checkbox.pack(pady=5)
        
        # 帮助文本
        help_text = ctk.CTkTextbox(settings, height=150)
        help_text.pack(fill="x", padx=10, pady=5)
        help_text.insert("1.0", """
获取API密钥说明：(alt+1截图快捷键)

1. 百度OCR配置：(不用截图识别文本,可以不用配置)
   • 访问百度AI开放平台：https://ai.baidu.com
   • 注册账号并创建应用
   • 选择"文字识别"服务
   • 获取API Key和Secret Key

2. GPT配置：(去以下地址GitHub获取免费api)
   • 访问API服务：https://free.v36.cm
   • 注册账号获取API Key
   • 默认API地址：https://free.v36.cm/v1/chat/completions
        """)
        help_text.configure(state="disabled")
        
        # OCR设置
        ocr_frame = ctk.CTkFrame(settings)
        ocr_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(ocr_frame, text="百度OCR设置").pack(pady=5)
        
        ocr_key = ctk.CTkEntry(ocr_frame, placeholder_text="API Key")
        ocr_key.pack(fill="x", padx=10, pady=5)
        ocr_key.insert(0, self.API_KEY)
        
        ocr_secret = ctk.CTkEntry(ocr_frame, placeholder_text="Secret Key", show="*")
        ocr_secret.pack(fill="x", padx=10, pady=5)
        ocr_secret.insert(0, self.SECRET_KEY)
        
        # GPT设置
        gpt_frame = ctk.CTkFrame(settings)
        gpt_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(gpt_frame, text="GPT设置").pack(pady=5)
        
        gpt_url = ctk.CTkEntry(gpt_frame, placeholder_text="API URL")
        gpt_url.pack(fill="x", padx=10, pady=5)
        gpt_url.insert(0, self.GPT_API_URL)
        
        gpt_key = ctk.CTkEntry(gpt_frame, placeholder_text="API Key", show="*")
        gpt_key.pack(fill="x", padx=10, pady=5)
        gpt_key.insert(0, self.GPT_API_KEY)
        
        def save_settings():
            try:
                # 保存设置
                self.API_KEY = ocr_key.get()
                self.SECRET_KEY = ocr_secret.get()
                self.access_token = self.get_access_token() if self.API_KEY and self.SECRET_KEY else None
                
                self.GPT_API_URL = gpt_url.get()
                self.GPT_API_KEY = gpt_key.get()
                
                config = {
                    'baidu_ocr': {
                        'api_key': self.API_KEY,
                        'secret_key': self.SECRET_KEY
                    },
                    'gpt': {
                        'api_url': self.GPT_API_URL,
                        'api_key': self.GPT_API_KEY
                    },
                    'window': {
                        'topmost': top_var.get()  # 保存置顶设置
                    }
                }
                
                if self.config_manager.save_config(config):
                    settings.destroy()
                    self.show_message("设置已保存")
                else:
                    self.show_message("保存失败")
            except Exception as e:
                self.show_message(f"保存出错: {str(e)}")
        
        save_btn = ctk.CTkButton(settings, text="保存", command=save_settings)
        save_btn.pack(pady=10)
        
        # 使窗口居中
        settings.update_idletasks()
        x = self.main_window.winfo_x() + (self.main_window.winfo_width() - settings.winfo_width()) // 2
        y = self.main_window.winfo_y() + (self.main_window.winfo_height() - settings.winfo_height()) // 2
        settings.geometry(f"+{x}+{y}")
    
    def show_message(self, message):
        """显示消息提示"""
        msg = ctk.CTkToplevel(self.main_window)
        msg.geometry("300x100")
        msg.title("提示")
        
        ctk.CTkLabel(msg, text=message).pack(expand=True)
        
        msg.update_idletasks()
        x = self.main_window.winfo_x() + (self.main_window.winfo_width() - msg.winfo_width()) // 2
        y = self.main_window.winfo_y() + (self.main_window.winfo_height() - msg.winfo_height()) // 2
        msg.geometry(f"+{x}+{y}")
        
        msg.after(2000, msg.destroy)
    
    def on_ask(self):
        """处理提问"""
        thread = threading.Thread(target=self._do_api_request)
        thread.daemon = True
        thread.start()
    
    def _do_api_request(self):
        """在新线程中处理API请求"""
        try:
            current_text = self.text_input.get("1.0", "end").strip()
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个用中文回答问题的AI助手"
                    },
                    {
                        "role": "user",
                        "content": current_text
                    }
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                self.GPT_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.GPT_API_KEY}"
                },
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    answer = result['choices'][0]['message']['content']
                    if answer:
                        self.main_window.after(0, self._update_answer, answer)
                        return
            
            self.main_window.after(0, self.show_message, "获取回答失败")
            
        except Exception as e:
            self.main_window.after(0, self.show_message, f"请求错误: {str(e)}")
    
    def _update_answer(self, answer):
        """更新答案"""
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", answer)
    
    def start_capture(self):
        """开始截图"""
        if not self.capture_window:
            self.capture_window = ctk.CTk()
            self.capture_window.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
            self.capture_window.configure(fg_color="black")
            
            def on_press(event):
                self.capture_start = (event.x, event.y)
                self.is_capturing = True
            
            def on_move(event):
                if self.is_capturing:
                    self.capture_window.update()
            
            def on_release(event):
                if self.is_capturing:
                    self.is_capturing = False
                    x1, y1 = self.capture_start
                    x2, y2 = event.x, event.y
                    self.capture_window.withdraw()
                    self.capture_and_recognize(x1, y1, x2, y2)
            
            self.capture_window.bind("<Button-1>", on_press)
            self.capture_window.bind("<B1-Motion>", on_move)
            self.capture_window.bind("<ButtonRelease-1>", on_release)
            self.capture_window.bind("<Escape>", lambda e: self.capture_window.withdraw())
        
        self.capture_window.deiconify()
    
    def capture_and_recognize(self, x1, y1, x2, y2):
        """处理文字识别"""
        try:
            # 确保坐标正确
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # 截图
            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            
            # 转换图片为base64
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 调用百度OCR API
            params = {"access_token": self.access_token}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {"image": img_base64}
            
            response = requests.post(self.OCR_URL, params=params, headers=headers, data=data)
            result = response.json()
            
            if 'words_result' in result:
                text = ' '.join([word['words'] for word in result['words_result']])
                if text:
                    self.text_input.delete("1.0", "end")
                    self.text_input.insert("1.0", text)
                    self.main_window.deiconify()
                    self.main_window.lift()
                    return
            
            self.show_message("识别失败")
            
        except Exception as e:
            self.show_message(f"识别错误: {str(e)}")
    
    def quit_application(self):
        """完全退出应用程序"""
        keyboard.unhook_all()
        self.main_window.quit()

def main():
    ctk.set_appearance_mode("light")
    app = TextRecognizer()
    
    # 注册快捷键
    def check_hotkey():
        if keyboard.is_pressed('alt+1'):
            app.start_capture()
        app.main_window.after(100, check_hotkey)
    
    app.main_window.after(100, check_hotkey)
    app.main_window.mainloop()

if __name__ == '__main__':
    main() 