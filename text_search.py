import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyautogui
from PIL import Image, ImageTk
import sys
import io
import base64
import requests
import keyboard
import json
import os
from config_manager import ConfigManager
import threading
import urllib3
import warnings
from typing import Optional, Tuple

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TextRecognizer:
    def __init__(self):
        self.capture_start: Optional[Tuple[int, int]] = None
        self.is_capturing = False
        self.capture_window = None
        self.main_window = None
        self.settings_window = None
        self.message_windows = []
        
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
        self.GPT_MODEL = config['gpt']['model']
        
        # 初始化SSL环境
        self._init_ssl_environment()
        
        # 创建主窗口
        self.create_main_window()
        
    def _init_ssl_environment(self):
        """初始化SSL环境以确保HTTPS请求正常工作"""
        try:
            # 确保SSL模块正确加载
            import ssl
            import urllib3
            import certifi
            
            # 禁用SSL警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # 确保证书路径正确
            if hasattr(os, 'environ'):
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
                os.environ['SSL_CERT_FILE'] = certifi.where()
            
        except Exception as e:
            print(f"SSL环境初始化警告: {str(e)}")
            # 即使初始化失败也不影响程序运行
    
    def get_access_token(self):
        """获取百度 API access token"""
        try:
            url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.API_KEY}&client_secret={self.SECRET_KEY}"
            import ssl
            import urllib3
            # 禁用 SSL 警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, verify=False, timeout=10)  # 禁用 SSL 验证
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                self.show_message(f"获取 access_token 失败: {response.text}")
                return None
        except requests.exceptions.SSLError as e:
            self.show_message("SSL 证书验证失败，已禁用证书验证")
            return None
        except requests.exceptions.RequestException as e:
            self.show_message(f"网络请求错误: {str(e)}")
            return None
        except Exception as e:
            self.show_message(f"获取 access_token 时发生错误: {str(e)}")
            return None
        
    def create_main_window(self):
        """创建主窗口"""
        self.main_window = tk.Tk()
        self.main_window.title("OCR-GPT 文本识别与AI问答")
        self.main_window.geometry("600x400")
        
        # 从配置中读取置顶状态
        is_topmost = self.config_manager.config['window']['topmost']
        self.main_window.attributes('-topmost', is_topmost)
        
        # 设置图标
        try:
            if getattr(sys, 'frozen', False):
                # 如果是打包后的 exe
                application_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                # 如果是直接运行 py 文件
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, 'ai.png')
            if os.path.exists(icon_path):
                # 使用 tkinter.PhotoImage（支持 PNG 格式）
                try:
                    photo = tk.PhotoImage(file=icon_path)
                    self.main_window.iconphoto(False, photo)
                    # 保持对图标的引用以防止被垃圾回收
                    self._icon_image = photo
                except tk.TclError:
                    # 如果 PNG 不支持，尝试使用 wm_iconbitmap（仅支持 ICO 格式）
                    try:
                        # 转换为 ICO 格式并保存临时文件
                        icon = Image.open(icon_path)
                        icon = icon.resize((32, 32), Image.Resampling.LANCZOS)
                        ico_path = os.path.join(application_path, 'temp_icon.ico')
                        icon.save(ico_path, format='ICO')
                        self.main_window.iconbitmap(ico_path)
                        # 清理临时文件
                        try:
                            os.remove(ico_path)
                        except:
                            pass
                    except Exception:
                        # 如果都失败了，忽略图标设置
                        pass
        except Exception as e:
            # 图标加载失败不影响程序正常运行，仅记录日志
            print(f"图标加载失败（不影响功能）: {str(e)}")
        
        # 创建文本区域
        text_label = tk.Label(self.main_window, text="识别文本:", anchor="w", font=('Arial', 10))
        text_label.pack(fill="x", padx=10, pady=(10,0))
        
        # 创建文本输入框（使用 ScrolledText）
        self.text_input = scrolledtext.ScrolledText(self.main_window, height=6, 
                                                   wrap=tk.WORD, font=('Arial', 10))
        self.text_input.pack(fill="x", padx=10, pady=5)
        
        # 创建按钮区域
        button_frame = tk.Frame(self.main_window)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # 左侧按钮容器
        self.left_buttons = tk.Frame(button_frame)
        self.left_buttons.pack(side="left")
        
        # 按钮样式配置
        button_style = {'font': ('Arial', 9), 'width': 10, 'height': 1}
        
        ask_button = tk.Button(self.left_buttons, text="点击提问", command=self.on_ask, **button_style)
        ask_button.pack(side="left", padx=5)
        
        clear_button = tk.Button(self.left_buttons, text="清空回答", 
                                command=lambda: self.answer_text.delete("1.0", "end"), **button_style)
        clear_button.pack(side="left", padx=5)
        
        # 添加截图按钮
        capture_button = tk.Button(self.left_buttons, text="截图-Alt+1", command=self.start_capture, **button_style)
        capture_button.pack(side="left", padx=5)
        
        settings_button = tk.Button(self.left_buttons, text="设置", command=self.show_settings, **button_style)
        settings_button.pack(side="left", padx=5)
        
        # 添加置顶选项到按钮区域，使用配置中的状态
        self.top_var = tk.BooleanVar(value=is_topmost)
        top_checkbox = tk.Checkbutton(self.left_buttons, text="置顶", variable=self.top_var,
                                     command=lambda: self.main_window.attributes('-topmost', self.top_var.get()) if self.main_window else None)
        top_checkbox.pack(side="left", padx=10)
        
        # 创建回答区域
        answer_label = tk.Label(self.main_window, text="AI回答:", anchor="w", font=('Arial', 10))
        answer_label.pack(fill="x", padx=10, pady=(10,0))
        
        # 创建回答显示框（使用 ScrolledText）
        self.answer_text = scrolledtext.ScrolledText(self.main_window, wrap=tk.WORD, font=('Arial', 10))
        self.answer_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 修复回车键绑定
        def handle_return(event):
            if not event.state & 0x1:  # 不是 Shift+Enter
                self.on_ask()
                return "break"  # 阻止默认的换行行为
        
        self.text_input.bind("<Return>", handle_return)
        
        # 设置窗口样式
        self.main_window.configure(bg="#f0f0f0")
        if sys.platform.startswith('win'):
            # Windows 平台
            self.main_window.wm_attributes('-topmost', is_topmost)
        else:
            # Linux/Mac 平台
            self.main_window.wm_attributes('-type', 'splash')

    def show_settings(self):
        """显示设置窗口"""
        # 如果已有设置窗口，先关闭它
        if self.settings_window is not None:
            try:
                if hasattr(self.settings_window, 'winfo_exists') and self.settings_window.winfo_exists():
                    self.settings_window.destroy()
            except:
                pass
            self.settings_window = None
        
        try:
            self.settings_window = tk.Toplevel(self.main_window)
            settings = self.settings_window
            settings.title("设置")
            settings.geometry("400x500")
            settings.grab_set()
            settings.attributes('-topmost', True)
            settings.focus_force()
            
            # 帮助文本
            help_text = scrolledtext.ScrolledText(settings, height=8, wrap=tk.WORD, font=('Arial', 9))
            help_text.pack(fill="x", padx=10, pady=5)
            help_text.insert("1.0", """获取API密钥说明：

1. 百度OCR配置：(不用截图识别文本,可以不用配置)
   • 访问百度AI开放平台：https://ai.baidu.com
   • 注册账号并创建应用
   • 选择"文字识别"服务
   • 获取API Key和Secret Key

2. GPT配置：(去以下地址GitHub获取免费api)
   • 访问API服务：https://free.v36.cm
   • 注册账号获取API Key
   • 默认API地址：https://free.v36.cm/v1/chat/completions

3. 使用方法：
   • 点击"截图-Alt+1"按钮或按Alt+1快捷键进行截图OCR识别
   • 在文本框中编辑识别结果或直接输入问题
   • 点击"点击提问"按钮或按回车键获取AI回答""")
            help_text.configure(state="disabled")
            
            # OCR设置
            ocr_frame = tk.LabelFrame(settings, text="百度OCR设置", font=('Arial', 10))
            ocr_frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(ocr_frame, text="API Key:", font=('Arial', 9)).pack(anchor="w", padx=10, pady=(5,0))
            ocr_key = tk.Entry(ocr_frame, font=('Arial', 9))
            ocr_key.pack(fill="x", padx=10, pady=(0,5))
            ocr_key.insert(0, self.API_KEY)
            
            tk.Label(ocr_frame, text="Secret Key:", font=('Arial', 9)).pack(anchor="w", padx=10, pady=(5,0))
            ocr_secret = tk.Entry(ocr_frame, show="*", font=('Arial', 9))
            ocr_secret.pack(fill="x", padx=10, pady=(0,5))
            ocr_secret.insert(0, self.SECRET_KEY)
            
            # GPT设置
            gpt_frame = tk.LabelFrame(settings, text="GPT设置", font=('Arial', 10))
            gpt_frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(gpt_frame, text="API URL:", font=('Arial', 9)).pack(anchor="w", padx=10, pady=(5,0))
            gpt_url = tk.Entry(gpt_frame, font=('Arial', 9))
            gpt_url.pack(fill="x", padx=10, pady=(0,5))
            gpt_url.insert(0, self.GPT_API_URL)
            
            tk.Label(gpt_frame, text="API Key:", font=('Arial', 9)).pack(anchor="w", padx=10, pady=(5,0))
            gpt_key = tk.Entry(gpt_frame, show="*", font=('Arial', 9))
            gpt_key.pack(fill="x", padx=10, pady=(0,5))
            gpt_key.insert(0, self.GPT_API_KEY)
            
            tk.Label(gpt_frame, text="模型名称:", font=('Arial', 9)).pack(anchor="w", padx=10, pady=(5,0))
            gpt_model = tk.Entry(gpt_frame, font=('Arial', 9))
            gpt_model.pack(fill="x", padx=10, pady=(0,5))
            gpt_model.insert(0, self.GPT_MODEL)
            
            def save_settings():
                try:
                    # 保存设置前先验证 API 是否可用
                    new_api_key = ocr_key.get()
                    new_secret_key = ocr_secret.get()
                    new_gpt_url = gpt_url.get()
                    new_gpt_key = gpt_key.get()
                    new_gpt_model = gpt_model.get()
                    
                    # 获取当前窗口的置顶状态
                    current_topmost = self.main_window.attributes('-topmost') if self.main_window else False
                    
                    # 准备新的配置
                    config = {
                        'baidu_ocr': {
                            'api_key': new_api_key,
                            'secret_key': new_secret_key
                        },
                        'gpt': {
                            'api_url': new_gpt_url,
                            'api_key': new_gpt_key,
                            'model': new_gpt_model
                        },
                        'window': {
                            'topmost': current_topmost
                        }
                    }
                    
                    # 先保存配置
                    if self.config_manager.save_config(config):
                        # 保存成功后再更新内存中的值
                        self.API_KEY = new_api_key
                        self.SECRET_KEY = new_secret_key
                        self.GPT_API_URL = new_gpt_url
                        self.GPT_API_KEY = new_gpt_key
                        self.GPT_MODEL = new_gpt_model
                        
                        # 如果有百度 API，尝试获取 token
                        if new_api_key and new_secret_key:
                            self.access_token = self.get_access_token()
                        
                        if self.settings_window and self.settings_window.winfo_exists():
                            self.settings_window.destroy()
                            self.settings_window = None
                        self.show_message("设置已保存")
                        return True
                    else:
                        self.show_message("保存设置失败")
                        return False
                    
                except Exception as e:
                    self.show_message(f"保存设置失败：\n{str(e)}")
                    return False
            
            save_btn = tk.Button(settings, text="保存", command=save_settings, font=('Arial', 9), width=10)
            save_btn.pack(pady=10)
            
            # 使窗口居中
            settings.update_idletasks()
            if self.main_window:
                x = self.main_window.winfo_x() + (self.main_window.winfo_width() - settings.winfo_width()) // 2
                y = self.main_window.winfo_y() + (self.main_window.winfo_height() - settings.winfo_height()) // 2
                settings.geometry(f"+{x}+{y}")
            
            # 处理窗口关闭
            def on_closing():
                if self.settings_window and hasattr(self.settings_window, 'winfo_exists') and self.settings_window.winfo_exists():
                    self.settings_window.destroy()
                self.settings_window = None
            
            settings.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            self.show_message(f"打开设置窗口失败：\n{str(e)}")
            if self.settings_window:
                try:
                    self.settings_window.destroy()
                except:
                    pass
                self.settings_window = None
    
    def show_message(self, message):
        """显示消息提示"""
        try:
            msg = tk.Toplevel(self.main_window)
            self.message_windows.append(msg)
            msg.geometry("300x150")
            msg.title("提示")
            msg.attributes('-topmost', True)
            msg.focus_force()
            
            frame = tk.Frame(msg)
            frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            label = tk.Label(frame, text=message, wraplength=250)
            label.pack(pady=(0, 20))
            
            def close_message():
                try:
                    if msg.winfo_exists():
                        msg.destroy()
                    if msg in self.message_windows:
                        self.message_windows.remove(msg)
                except:
                    pass
            
            ok_button = tk.Button(frame, text="确定", command=close_message, width=10)
            ok_button.pack()
            
            msg.update_idletasks()
            if self.main_window:
                x = self.main_window.winfo_x() + (self.main_window.winfo_width() - msg.winfo_width()) // 2
                y = self.main_window.winfo_y() + (self.main_window.winfo_height() - msg.winfo_height()) // 2
                msg.geometry(f"+{x}+{y}")
            
            # 处理窗口关闭
            msg.protocol("WM_DELETE_WINDOW", close_message)
            
            msg.grab_set()
            msg.wait_window()
        except Exception as e:
            print(f"显示消息失败: {str(e)}")
    
    def on_ask(self):
        """处理提问"""
        # 禁用按钮，显示加载状态
        if self.left_buttons:
            for widget in self.left_buttons.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(state="disabled")
        
        # 使用线程处理请求
        thread = threading.Thread(target=self._do_api_request)
        thread.daemon = True
        thread.start()
    
    def _do_api_request(self):
        """在新线程中处理API请求"""
        try:
            current_text = self.text_input.get("1.0", "end").strip()
            
            # 检查API密钥是否为空
            if not self.GPT_API_KEY or self.GPT_API_KEY.strip() == "":
                if self.main_window:
                    self.main_window.after(0, self.show_message, "GPT API密钥未配置，请先在设置中输入API密钥")
                return
            
            # 检查输入文本是否为空
            if not current_text:
                if self.main_window:
                    self.main_window.after(0, self.show_message, "请输入要提问的问题")
                return
            
            data = {
                "model": self.GPT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个用中文回答问题的AI助手,如果只有英文输入就返回翻译信息."
                    },
                    {
                        "role": "user",
                        "content": current_text
                    }
                ],
                "temperature": 0.7
            }
            
            import ssl
            import urllib3
            # 禁用 SSL 警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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
                try:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        answer = result['choices'][0]['message']['content']
                        if answer:
                            # 使用 after 在主线程中更新 UI
                            if self.main_window:
                                self.main_window.after(0, self._update_answer, answer)
                            return
                        else:
                            if self.main_window:
                                self.main_window.after(0, self.show_message, f"API返回内容为空: {response.text}")
                    else:
                        if self.main_window:
                            self.main_window.after(0, self.show_message, f"API响应格式错误，缺少choices字段: {response.text}")
                except json.JSONDecodeError as json_err:
                    if self.main_window:
                        self.main_window.after(0, self.show_message, f"响应JSON解析错误: {str(json_err)}\n响应内容: {response.text[:200]}...")
            else:
                # 尝试解析错误响应
                try:
                    error_result = response.json()
                    error_msg = error_result.get('error', {}).get('message', str(error_result))
                    if self.main_window:
                        self.main_window.after(0, self.show_message, f"API请求失败 (状态码: {response.status_code}): {error_msg}")
                except json.JSONDecodeError:
                    if self.main_window:
                        self.main_window.after(0, self.show_message, f"API请求失败 (状态码: {response.status_code}): {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            if self.main_window:
                self.main_window.after(0, self.show_message, "请求超时，请检查网络连接或API地址是否正确")
        except requests.exceptions.ConnectionError:
            if self.main_window:
                self.main_window.after(0, self.show_message, "网络连接错误，请检查网络连接和API地址")
        except Exception as e:
            if self.main_window:
                self.main_window.after(0, self.show_message, f"请求错误: {str(e)}")
        finally:
            # 使用 after 在主线程中恢复按钮状态
            if self.main_window:
                self.main_window.after(0, self._reset_buttons)
    
    def _update_answer(self, answer):
        """更新答案"""
        self.answer_text.delete("1.0", "end")
        self.answer_text.insert("1.0", answer)
    
    def _reset_buttons(self):
        """恢复按钮状态"""
        if self.left_buttons:
            for widget in self.left_buttons.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(state="normal")
    
    def start_capture(self):
        """开始截图 - 简化版本"""
        try:
            # 关闭之前的截图窗口
            if self.capture_window:
                try:
                    self.capture_window.destroy()
                except:
                    pass
                self.capture_window = None
            
            # 创建简单的截图窗口
            self.capture_window = tk.Toplevel(self.main_window)
            self.capture_window.title("截图")
            
            # 设置窗口为半透明全屏
            self.capture_window.attributes('-alpha', 0.3)  # 30%透明度，可以看到背景
            self.capture_window.attributes('-fullscreen', True)
            self.capture_window.attributes('-topmost', True)
            self.capture_window.configure(bg='gray')
            self.capture_window.overrideredirect(True)
            
            # 创建画布
            self.canvas = tk.Canvas(
                self.capture_window,
                bg='gray',
                highlightthickness=0,
                cursor='crosshair'
            )
            self.canvas.pack(fill='both', expand=True)
            
            # 显示提示信息
            screen_width = self.capture_window.winfo_screenwidth()
            self.canvas.create_text(
                screen_width // 2, 30,
                text="拖动鼠标选择区域，按ESC取消",
                fill='red',
                font=('Arial', 16, 'bold'),
                tags='help'
            )
            
            # 简化事件处理
            def start_selection(event):
                self.capture_start = (event.x, event.y)
                self.is_capturing = True
                self.canvas.delete('help')  # 删除提示信息
                self.canvas.delete('rect')  # 删除之前的矩形
                print(f"开始选择: {self.capture_start}")
            
            def update_selection(event):
                if self.is_capturing and self.capture_start:
                    self.canvas.delete('rect')  # 删除之前的矩形
                    x1, y1 = self.capture_start
                    x2, y2 = event.x, event.y
                    
                    # 确保坐标顺序正确
                    left = min(x1, x2)
                    top = min(y1, y2)
                    right = max(x1, x2)
                    bottom = max(y1, y2)
                    
                    # 绘制非常明亮的红色边框（无填充）
                    self.canvas.create_rectangle(
                        left, top, right, bottom,
                        outline='red',
                        width=4,  # 更粗的边框
                        tags='rect'
                    )
                    
                    # 添加高对比度的内边框
                    self.canvas.create_rectangle(
                        left+1, top+1, right-1, bottom-1,
                        outline='yellow',
                        width=1,
                        tags='rect'
                    )
                    
                    # 显示尺寸信息（添加黑色背景使文字更清晰）
                    width = right - left
                    height = bottom - top
                    if width > 20 and height > 20:  # 只在区域足够大时显示
                        # 添加背景矩形使文字更清晰
                        self.canvas.create_rectangle(
                            right + 5, top - 25, right + 120, top + 5,
                            fill='black',
                            outline='white',
                            tags='rect'
                        )
                        self.canvas.create_text(
                            right + 10, top - 10,
                            text=f"{width} x {height}",
                            fill='yellow',
                            anchor='w',
                            font=('Arial', 12, 'bold'),
                            tags='rect'
                        )
            
            def end_selection(event):
                if self.is_capturing and self.capture_start:
                    self.is_capturing = False
                    x1, y1 = self.capture_start
                    x2, y2 = event.x, event.y
                    
                    print(f"结束选择: ({x1}, {y1}) -> ({x2}, {y2})")
                    
                    # 隐藏截图窗口
                    if self.capture_window:
                        self.capture_window.withdraw()
                    
                    # 处理OCR
                    try:
                        self.capture_and_recognize(x1, y1, x2, y2)
                    except Exception as e:
                        print(f"OCR处理错误: {e}")
                        self.show_message(f"OCR处理错误: {str(e)}")
            
            def cancel_capture(event=None):
                print("取消截图")
                self.is_capturing = False
                if self.capture_window:
                    self.capture_window.withdraw()
            
            # 绑定事件
            self.canvas.bind('<Button-1>', start_selection)
            self.canvas.bind('<B1-Motion>', update_selection)
            self.canvas.bind('<ButtonRelease-1>', end_selection)
            self.canvas.bind('<Escape>', cancel_capture)
            
            # 设置焦点
            self.canvas.focus_set()
            
            print("截图窗口已显示（半透明模式，可看到背景）")
            
        except Exception as e:
            print(f"创建截图窗口失败: {e}")
            self.show_message(f"截图功能错误: {str(e)}")
    
    def capture_and_recognize(self, x1, y1, x2, y2):
        """处理文字识别"""
        try:
            if not self.access_token:
                self.show_message("请先配置并保存正确的百度 OCR API 密钥")
                return
                
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
            
            import ssl
            import urllib3
            # 禁用 SSL 警告
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.post(self.OCR_URL, params=params, headers=headers, data=data, verify=False, timeout=30)
            result = response.json()
            
            if 'error_code' in result:
                self.show_message(f"识别失败: {result.get('error_msg', '未知错误')}")
                return
                
            if 'words_result' in result:
                text = ' '.join([word['words'] for word in result['words_result']])
                if text:
                    self.text_input.delete("1.0", "end")
                    self.text_input.insert("1.0", text)
                    if self.main_window:
                        self.main_window.deiconify()
                        self.main_window.lift()
                    return
            
            self.show_message("识别失败：未能识别出文字")
            
        except requests.exceptions.SSLError as e:
            self.show_message("SSL 证书验证失败，请检查网络设置")
        except requests.exceptions.RequestException as e:
            self.show_message(f"网络请求错误: {str(e)}")
        except Exception as e:
            self.show_message(f"识别错误: {str(e)}")
    
    def quit_application(self):
        """完全退出应用程序"""
        try:
            # 取消所有快捷键
            keyboard.unhook_all()
            
            # 取消所有定时任务
            if self.main_window and hasattr(self.main_window, 'winfo_exists') and self.main_window.winfo_exists():
                try:
                    for after_id in self.main_window.tk.call('after', 'info'):
                        self.main_window.after_cancel(after_id)
                except:
                    pass
            
            # 关闭所有消息窗口
            for window in self.message_windows[:]:
                try:
                    if window and hasattr(window, 'winfo_exists') and window.winfo_exists():
                        window.destroy()
                except:
                    pass
            self.message_windows.clear()
            
            # 关闭设置窗口
            if self.settings_window is not None:
                try:
                    if hasattr(self.settings_window, 'winfo_exists') and self.settings_window.winfo_exists():
                        self.settings_window.destroy()
                except:
                    pass
                self.settings_window = None
            
            # 关闭截图窗口
            if self.capture_window is not None:
                try:
                    if hasattr(self.capture_window, 'winfo_exists') and self.capture_window.winfo_exists():
                        self.capture_window.destroy()
                except:
                    pass
                self.capture_window = None
            
            # 关闭主窗口
            if self.main_window is not None:
                try:
                    if hasattr(self.main_window, 'winfo_exists') and self.main_window.winfo_exists():
                        self.main_window.quit()
                        self.main_window.destroy()
                except:
                    pass
                self.main_window = None
        except:
            pass
        finally:
            # 确保程序完全退出
            try:
                os._exit(0)
            except:
                sys.exit(0)

def main():
    app = TextRecognizer()
    
    # 使用 keyboard 直接注册热键
    def on_hotkey():
        try:
            app.start_capture()
        except Exception as e:
            print(f"热键触发错误: {str(e)}")
    
    try:
        # 注册热键 Alt+1
        keyboard.add_hotkey('alt+1', on_hotkey)
        print("热键 Alt+1 已注册")
    except Exception as e:
        print(f"注册热键失败: {str(e)}")
    
    try:
        if app.main_window:
            app.main_window.mainloop()
    except Exception as e:
        print(f"主循环发生错误: {str(e)}")
    finally:
        app.quit_application()

if __name__ == '__main__':
    main() 