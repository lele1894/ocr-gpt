import json
import os

class ConfigManager:
    def __init__(self):
        self.config_file = 'config.json'
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
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False 