import json
import os
import sys
import logging
import tempfile

class ConfigManager:
    def __init__(self):
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 获取配置文件的正确路径
        self.config_file = self._get_config_path()
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
    
    def _get_config_path(self):
        """获取配置文件路径"""
        try:
            # 首选用户目录
            user_dir = os.path.join(os.path.expanduser('~'), 'OCR-GPT')
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            return os.path.join(user_dir, 'config.json')
        except:
            # 如果用户目录不可用，使用临时目录
            temp_dir = os.path.join(tempfile.gettempdir(), 'OCR-GPT')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            return os.path.join(temp_dir, 'config.json')
    
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
                        for section in ['baidu_ocr', 'gpt', 'window']:
                            if section in loaded_config and isinstance(loaded_config[section], dict):
                                merged_config[section].update(loaded_config[section])
                    self.logger.info("配置文件加载成功")
                    return merged_config
        except Exception as e:
            self.logger.error(f"加载配置文件出错: {str(e)}")
        
        # 如果加载失败，创建默认配置
        try:
            self.save_config(self.default_config)
        except:
            pass
        return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 验证配置数据
            if not isinstance(config, dict):
                raise ValueError("配置数据必须是字典类型")
            
            # 确保配置数据格式正确
            for section in ['baidu_ocr', 'gpt', 'window']:
                if section not in config or not isinstance(config[section], dict):
                    config[section] = self.default_config[section]
            
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 尝试保存配置
            self.logger.info(f"正在保存配置到: {self.config_file}")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.logger.info("配置保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            # 尝试使用临时目录
            try:
                temp_dir = os.path.join(tempfile.gettempdir(), 'OCR-GPT')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                temp_file = os.path.join(temp_dir, 'config.json')
                
                self.logger.info(f"尝试保存到临时目录: {temp_file}")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                self.config_file = temp_file
                self.logger.info("配置已保存到临时目录")
                return True
            except Exception as temp_error:
                self.logger.error(f"保存到临时目录也失败: {str(temp_error)}")
                return False 