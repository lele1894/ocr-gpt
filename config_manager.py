import json
import os
import sys
import logging

class ConfigManager:
    def __init__(self):
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 获取配置文件的正确路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            try:
                # 首先尝试程序目录
                application_path = os.path.dirname(sys.executable)
                test_path = os.path.join(application_path, 'test_write')
                with open(test_path, 'w') as f:
                    f.write('test')
                os.remove(test_path)
            except Exception:
                # 如果无法写入，使用用户目录
                application_path = os.path.join(os.path.expanduser('~'), 'OCR-GPT')
                os.makedirs(application_path, exist_ok=True)
        else:
            # 如果是直接运行 py 文件
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        self.config_file = os.path.join(application_path, 'config.json')
        self.logger.info(f"配置文件路径: {self.config_file}")
        
        self.default_config = {
            'baidu_ocr': {
                'api_key': '',
                'secret_key': ''
            },
            'gpt': {
                'api_url': 'https://free.v36.cm/v1/chat/completions',
                'api_key': ''
            },
            'window': {
                'topmost': True  # 默认置顶
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.logger.info("正在加载配置文件...")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 确保所有必需的键都存在
                    merged_config = self.default_config.copy()
                    if isinstance(loaded_config, dict):
                        for section in ['baidu_ocr', 'gpt']:
                            if section in loaded_config and isinstance(loaded_config[section], dict):
                                merged_config[section].update(loaded_config[section])
                    self.logger.info("配置文件加载成功")
                    return merged_config
        except Exception as e:
            self.logger.error(f"加载配置文件出错: {str(e)}")
        return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
                self.logger.info(f"创建配置目录: {config_dir}")
            
            # 验证配置数据
            if not isinstance(config, dict):
                raise ValueError("配置数据必须是字典类型")
            
            # 确保配置数据格式正确
            for section in ['baidu_ocr', 'gpt']:
                if section not in config or not isinstance(config[section], dict):
                    config[section] = self.default_config[section]
            
            self.logger.info("正在保存配置文件...")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"配置文件已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件出错: {str(e)}")
            # 如果是权限问题，尝试在用户目录保存
            try:
                backup_path = os.path.join(os.path.expanduser('~'), 'ai_text_assistant_config.json')
                self.logger.info(f"尝试保存到备用位置: {backup_path}")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                self.config_file = backup_path
                self.logger.info("配置已保存到备用位置")
                return True
            except Exception as backup_error:
                self.logger.error(f"备用保存也失败: {str(backup_error)}")
            return False 