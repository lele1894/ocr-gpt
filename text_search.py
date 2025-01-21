import pyautogui
import webbrowser
from PIL import Image
import sys
import io
import base64
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea, QPushButton, QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit
from PyQt5.QtCore import Qt, QRect, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QIcon
import keyboard
import time
import json
import threading
from config_manager import ConfigManager
import os

# 添加一个信号类
class SignalBridge(QObject):
    answer_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    reset_button_signal = pyqtSignal()

class TextRecognizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.begin = None
        self.end = None
        self.is_drawing = False
        self.capture_window = None  # 用于截图的窗口
        self.result_window = None  # 保存主窗口引用
        
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
        
        # 创建信号桥接器
        self.signal_bridge = SignalBridge()
        self.signal_bridge.answer_signal.connect(self._update_answer)
        self.signal_bridge.error_signal.connect(lambda msg: self.show_error(msg, self.result_window.x(), self.result_window.y()))
        self.signal_bridge.reset_button_signal.connect(self._reset_button)
        
        # 获取图标文件的路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            application_path = sys._MEIPASS
        else:
            # 如果是直接运行 py 文件
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(application_path, 'ai.png')
        self.app_icon = QIcon(icon_path)
        
        # 创建并显示主窗口
        self.create_result_window()
        
    def initUI(self):
        """创建截图窗口"""
        self.capture_window = QMainWindow()
        self.capture_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.capture_window.setAttribute(Qt.WA_TranslucentBackground)
        
        # 将事件处理方法移动到截图窗口
        def mousePressEvent(event):
            self.begin = event.pos()
            self.end = self.begin
            self.is_drawing = True
            self.capture_window.update()

        def mouseMoveEvent(event):
            if self.is_drawing:
                self.end = event.pos()
                self.capture_window.update()

        def mouseReleaseEvent(event):
            if self.is_drawing:
                self.capture_and_recognize()

        def paintEvent(event):
            painter = QPainter(self.capture_window)
            painter.fillRect(self.capture_window.rect(), Qt.transparent)
            overlay = QColor(0, 0, 0, 30)
            painter.fillRect(self.capture_window.rect(), overlay)
            
            if self.begin and self.end:
                painter.setPen(QPen(Qt.red, 2))
                rect = QRect(self.begin, self.end)
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.fillRect(rect, Qt.transparent)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.drawRect(rect)

        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                self.capture_window.hide()

        # 绑定事件到截图窗口
        self.capture_window.mousePressEvent = mousePressEvent
        self.capture_window.mouseMoveEvent = mouseMoveEvent
        self.capture_window.mouseReleaseEvent = mouseReleaseEvent
        self.capture_window.paintEvent = paintEvent
        self.capture_window.keyPressEvent = keyPressEvent
        
    def get_access_token(self):
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.API_KEY}&client_secret={self.SECRET_KEY}"
        response = requests.get(url)
        return response.json().get("access_token")
        
    def create_result_window(self):
        """创建固定的主窗口"""
        self.result_window = QMainWindow()
        self.result_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 设置软件图标
        self.result_window.setWindowIcon(self.app_icon)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 修改标题栏部分
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # 修改标题文本
        title_label = QLabel("OCR-GPT")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 在标题栏添加设置按钮
        settings_button = QPushButton("⚙")
        settings_button.setFixedSize(20, 20)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
        """)
        settings_button.clicked.connect(self.show_settings)
        title_layout.addWidget(settings_button)
        
        # 添加最小化按钮
        min_button = QPushButton("—")
        min_button.setFixedSize(20, 20)
        min_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
        """)
        min_button.clicked.connect(self.result_window.showMinimized)
        title_layout.addWidget(min_button)
        
        # 添加关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                color: white;
            }
        """)
        close_button.clicked.connect(self.quit_application)
        title_layout.addWidget(close_button)
        
        layout.addWidget(title_bar)
        
        # 添加识别文本区域
        ocr_label = QLabel("识别文本:")
        ocr_label.setStyleSheet("color: #666666; font-weight: bold;")
        layout.addWidget(ocr_label)
        
        self.ocr_text = QTextEdit()
        self.ocr_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ocr_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ocr_text.setStyleSheet("""
            QTextEdit {
                color: black;
                padding: 5px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                min-height: 40px;
            }
        """)
        
        # 添加快捷键支持
        def handle_keypress(event):
            if event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
                self.ocr_text.insertPlainText('\n')
                return True
            elif event.key() == Qt.Key_Return:
                self.on_ask()
                return True
            return False
        
        def keyPressEvent(event):
            if not handle_keypress(event):
                QTextEdit.keyPressEvent(self.ocr_text, event)
        
        self.ocr_text.keyPressEvent = keyPressEvent
        self.ocr_text.textChanged.connect(self.adjust_text_height)
        layout.addWidget(self.ocr_text)
        
        # 添加按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加按钮
        self.ask_button = QPushButton("点击提问")
        self.ask_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: none;
                border-radius: 3px;
                min-height: 30px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.ask_button)
        
        clear_button = QPushButton("清空回答")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 5px;
                border: none;
                border-radius: 3px;
                min-height: 30px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        button_layout.addWidget(clear_button)
        layout.addWidget(button_container)
        
        # 添加回答文本区域
        answer_label = QLabel("AI回答:")
        answer_label.setStyleSheet("color: #666666; font-weight: bold;")
        layout.addWidget(answer_label)
        
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)
        self.answer_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        self.answer_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.answer_text.setStyleSheet("""
            QTextEdit {
                color: black;
                padding: 5px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                min-height: 100px;
            }
        """)
        self.answer_text.textChanged.connect(self.adjust_text_height)
        layout.addWidget(self.answer_text)
        
        # 绑定按钮事件
        self.ask_button.clicked.connect(self.on_ask)
        clear_button.clicked.connect(self.answer_text.clear)
        
        # 添加窗口拖动功能
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.result_window._drag_pos = event.globalPos() - self.result_window.pos()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() & Qt.LeftButton:
                self.result_window.move(event.globalPos() - self.result_window._drag_pos)
                event.accept()

        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        
        # 设置中央部件
        central_widget.setStyleSheet("background-color: white;")
        self.result_window.setCentralWidget(central_widget)
        
        # 设置窗口样式和大小
        self.result_window.setStyleSheet("""
            QMainWindow {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
        """)
        
        screen = QApplication.primaryScreen().geometry()
        width = min(600, screen.width() - 100)
        height = min(400, screen.height() - 100)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.result_window.setGeometry(x, y, width, height)
        self.result_window.show()
    
    def on_ask(self):
        """处理提问请求"""
        self.ask_button.setEnabled(False)
        self.ask_button.setText("请求中...")
        
        # 创建一个新线程来处理API请求
        thread = threading.Thread(target=self._do_api_request)
        thread.daemon = True
        thread.start()
    
    def _do_api_request(self):
        """在新线程中处理API请求"""
        try:
            current_text = self.ocr_text.toPlainText()
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
                        self.signal_bridge.answer_signal.emit(answer)
                        return
            
            self.signal_bridge.error_signal.emit("获取回答失败")
            
        except Exception as e:
            self.signal_bridge.error_signal.emit(f"请求错误: {str(e)}")
        finally:
            self.signal_bridge.reset_button_signal.emit()
    
    def _update_answer(self, answer):
        """在主线程中更新答案"""
        self.answer_text.setPlainText(answer)
        self.answer_text.show()
        # 文本更新后调整大小
        QTimer.singleShot(100, self.adjust_text_height)
    
    def _reset_button(self):
        """在主线程中重置按钮状态"""
        self.ask_button.setEnabled(True)
        self.ask_button.setText("点击提问")
    
    def start_capture(self):
        """开始截图"""
        if not self.capture_window:
            self.initUI()
        self.capture_window.showFullScreen()
    
    def capture_and_recognize(self):
        """处理文字识别"""
        if self.begin and self.end:
            x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
            x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
            
            # 截图
            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            
            # 转换图片为base64
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 调用百度OCR API
            try:
                params = {
                    "access_token": self.access_token
                }
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    "image": img_base64
                }
                response = requests.post(self.OCR_URL, params=params, headers=headers, data=data)
                result = response.json()
                
                if 'words_result' in result:
                    text = ' '.join([word['words'] for word in result['words_result']])
                    if text:
                        self.capture_window.hide()
                        self.ocr_text.setPlainText(text)
                        self.result_window.show()
                        self.result_window.raise_()
                        return
            except Exception as e:
                self._show_error(f"识别错误: {str(e)}")
            
            self.capture_window.hide()

    def show_error(self, error_msg, x, y):
        """显示错误信息"""
        error_window = QMainWindow()
        error_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        error_window.setGeometry(x + 20, y + 20, 300, 50)
        error_window.setStyleSheet("""
            QMainWindow {
                background-color: rgba(255, 200, 200, 0.9);
                border: 1px solid red;
                border-radius: 5px;
            }
        """)
        
        error_label = QLabel(error_msg, error_window)
        error_label.setStyleSheet("color: red; padding: 5px;")
        error_label.setWordWrap(True)
        
        # 3秒后自动关闭
        QTimer.singleShot(3000, error_window.close)
        
        error_window.show()

    def adjust_text_height(self):
        """调整文本框和窗口高度"""
        # 调整OCR文本框高度
        ocr_doc = self.ocr_text.document()
        ocr_doc.setTextWidth(self.ocr_text.width())
        ocr_height = min(150, max(40, int(ocr_doc.size().height() + 20)))  # 转换为整数
        self.ocr_text.setFixedHeight(ocr_height)
        
        # 调整回答文本框高度
        answer_doc = self.answer_text.document()
        answer_doc.setTextWidth(self.answer_text.width())
        answer_height = min(400, max(100, int(answer_doc.size().height() + 20)))  # 转换为整数
        self.answer_text.setFixedHeight(answer_height)
        
        # 计算窗口总高度
        total_height = (
            40 +  # 标题栏
            20 +  # 标签
            ocr_height +
            40 +  # 按钮区域
            20 +  # 标签
            answer_height +
            40   # 边距
        )
        
        # 调整窗口大小
        screen = QApplication.primaryScreen().geometry()
        width = min(600, screen.width() - 100)
        height = min(total_height, screen.height() - 100)
        
        # 保持窗口水平位置不变，只调整垂直大小
        current_pos = self.result_window.pos()
        self.result_window.setGeometry(
            current_pos.x(),
            current_pos.y(),
            width,
            height
        )

    def show_settings(self):
        """显示设置窗口"""
        settings_window = QMainWindow(self.result_window)
        settings_window.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        settings_window.setWindowTitle("设置")
        
        # 创建中央部件和布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加说明文本
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 10px;
                color: #666;
                font-size: 12px;
            }
        """)
        help_text.setHtml("""
            <p><b>获取API密钥说明：(alt+1截图快捷键)</b></p>
            <p>1. 百度OCR配置：(不用截图识别文本,可以不用配置)</p>
            <ul>
                <li>访问百度AI开放平台：<a href='https://ai.baidu.com'>https://ai.baidu.com</a></li>
                <li>注册账号并创建应用</li>
                <li>选择"文字识别"服务</li>
                <li>获取API Key和Secret Key</li>
            </ul>
            <p>2. GPT配置：(去以下地址GitHub获取免费api)</p>
            <ul>
                <li>访问API服务：<a href='https://free.v36.cm'>https://free.v36.cm</a></li>
                <li>注册账号获取API Key</li>
                <li>默认API地址：https://free.v36.cm/v1/chat/completions</li>
            </ul>
        """)
        help_text.setFixedHeight(200)
        layout.addWidget(help_text)
        
        # 百度 OCR 设置
        ocr_group = QGroupBox("百度 OCR 设置")
        ocr_layout = QFormLayout()
        
        ocr_key_input = QLineEdit(self.API_KEY)
        ocr_key_input.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许右键菜单
        ocr_secret_input = QLineEdit(self.SECRET_KEY)
        ocr_secret_input.setEchoMode(QLineEdit.Password)
        ocr_secret_input.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许右键菜单
        
        # 添加显示/隐藏密码按钮
        show_secret = QPushButton("👁")
        show_secret.setFixedSize(20, 20)
        show_secret.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #666;
            }
        """)
        
        def toggle_secret():
            if ocr_secret_input.echoMode() == QLineEdit.Password:
                ocr_secret_input.setEchoMode(QLineEdit.Normal)
                show_secret.setText("🔒")
            else:
                ocr_secret_input.setEchoMode(QLineEdit.Password)
                show_secret.setText("👁")
        
        show_secret.clicked.connect(toggle_secret)
        
        secret_container = QWidget()
        secret_layout = QHBoxLayout(secret_container)
        secret_layout.setContentsMargins(0, 0, 0, 0)
        secret_layout.addWidget(ocr_secret_input)
        secret_layout.addWidget(show_secret)
        
        ocr_layout.addRow("API Key:", ocr_key_input)
        ocr_layout.addRow("Secret Key:", secret_container)
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # GPT 设置
        gpt_group = QGroupBox("GPT 设置")
        gpt_layout = QFormLayout()
        
        gpt_api_input = QLineEdit(self.GPT_API_URL)
        gpt_api_input.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许右键菜单
        gpt_key_input = QLineEdit(self.GPT_API_KEY)
        gpt_key_input.setEchoMode(QLineEdit.Password)
        gpt_key_input.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许右键菜单
        
        # 添加显示/隐藏 GPT Key 按钮
        show_gpt_key = QPushButton("👁")
        show_gpt_key.setFixedSize(20, 20)
        show_gpt_key.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #666;
            }
        """)
        
        def toggle_gpt_key():
            if gpt_key_input.echoMode() == QLineEdit.Password:
                gpt_key_input.setEchoMode(QLineEdit.Normal)
                show_gpt_key.setText("🔒")
            else:
                gpt_key_input.setEchoMode(QLineEdit.Password)
                show_gpt_key.setText("👁")
        
        show_gpt_key.clicked.connect(toggle_gpt_key)
        
        key_container = QWidget()
        key_layout = QHBoxLayout(key_container)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.addWidget(gpt_key_input)
        key_layout.addWidget(show_gpt_key)
        
        gpt_layout.addRow("API 地址:", gpt_api_input)
        gpt_layout.addRow("API Key:", key_container)
        gpt_group.setLayout(gpt_layout)
        layout.addWidget(gpt_group)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 20px;
                border: none;
                border-radius: 3px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        def save_settings():
            try:
                # 保存设置
                self.API_KEY = ocr_key_input.text()
                self.SECRET_KEY = ocr_secret_input.text()
                # 更新 access_token
                self.access_token = self.get_access_token() if self.API_KEY and self.SECRET_KEY else None
                
                # 保存 GPT 设置
                self.GPT_API_URL = gpt_api_input.text()
                self.GPT_API_KEY = gpt_key_input.text()
                
                # 保存到配置文件
                config = {
                    'baidu_ocr': {
                        'api_key': self.API_KEY,
                        'secret_key': self.SECRET_KEY
                    },
                    'gpt': {
                        'api_url': self.GPT_API_URL,
                        'api_key': self.GPT_API_KEY
                    }
                }
                if self.config_manager.save_config(config):
                    settings_window.close()
                    self.show_error("设置已保存", self.result_window.x(), self.result_window.y())
                else:
                    self.show_error("设置保存失败", self.result_window.x(), self.result_window.y())
            except Exception as e:
                self.show_error(f"保存设置时出错: {str(e)}", self.result_window.x(), self.result_window.y())
        
        save_button.clicked.connect(save_settings)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        # 设置中央部件
        settings_window.setCentralWidget(central_widget)
        
        # 设置窗口大小和位置
        settings_window.setFixedSize(400, 500)  # 增加高度以容纳说明文本
        settings_window.move(
            self.result_window.x() + (self.result_window.width() - settings_window.width()) // 2,
            self.result_window.y() + (self.result_window.height() - settings_window.height()) // 2
        )
        
        settings_window.show()

    def quit_application(self):
        """完全退出应用程序"""
        # 停止定时器
        for timer in self.findChildren(QTimer):
            timer.stop()
        
        # 关闭所有窗口
        if self.capture_window:
            self.capture_window.close()
        if self.result_window:
            self.result_window.close()
        
        # 取消注册快捷键
        keyboard.unhook_all()
        
        # 退出应用程序
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    recognizer = TextRecognizer()
    
    def check_hotkey():
        if keyboard.is_pressed('alt+1'):
            recognizer.start_capture()
    
    # 创建定时器检查快捷键
    timer = QTimer()
    timer.timeout.connect(check_hotkey)
    timer.start(100)
    
    # 设置应用程序属性
    app.setQuitOnLastWindowClosed(True)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 