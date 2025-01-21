import json
import os
import sys

class ConfigManager:
    def __init__(self):
        # 获取配置文件的正确路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是直接运行 py 文件
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        self.config_file = os.path.join(application_path, 'config.json')
        
        self.default_config = {
            'baidu_ocr': {
                'api_key': '',
                'secret_key': ''
            },
            'gpt': {
                'api_url': 'https://free.v36.cm/v1/chat/completions',
                'api_key': ''
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 确保所有必需的键都存在
                    merged_config = self.default_config.copy()
                    if isinstance(loaded_config, dict):
                        for section in ['baidu_ocr', 'gpt']:
                            if section in loaded_config and isinstance(loaded_config[section], dict):
                                merged_config[section].update(loaded_config[section])
                    return merged_config
        except Exception as e:
            print(f"加载配置文件出错: {str(e)}")
        return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件出错: {str(e)}")
            return False 