# sys_accessories/SupportedMod/ModConfig.py
"""
插件配置管理器
用于管理插件的启用/禁用状态和其他设置
"""

import os
import json
from enum import Enum


class ModStatus(Enum):
    """插件状态枚举"""
    ENABLED = "enabled"  # 已启用
    DISABLED = "disabled"  # 已禁用
    HIDDEN = "hidden"  # 已隐藏


class ModConfigManager:
    """插件配置管理器"""

    def __init__(self, config_file="ModShezhi.txt"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_data = {}
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        self.config_data = json.loads(content)
                    else:
                        self.config_data = {}
                print(f"加载插件配置: {self.config_file}")
            except Exception as e:
                print(f"加载插件配置失败: {e}")
                self.config_data = {}
                self.save_config()  # 创建默认配置
        else:
            self.config_data = {}
            self.save_config()  # 创建新配置文件

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            print(f"保存插件配置: {self.config_file}")
        except Exception as e:
            print(f"保存插件配置失败: {e}")

    def get_mod_config(self, mod_name):
        """获取插件配置"""
        return self.config_data.get(mod_name, {
            "status": ModStatus.ENABLED.value,
            "enabled": True,
            "visible": True,
            "priority": 50,
            "settings": {}
        })

    def set_mod_config(self, mod_name, config):
        """设置插件配置"""
        self.config_data[mod_name] = config
        self.save_config()

    def enable_mod(self, mod_name):
        """启用插件"""
        config = self.get_mod_config(mod_name)
        config["status"] = ModStatus.ENABLED.value
        config["enabled"] = True
        self.set_mod_config(mod_name, config)
        print(f"启用插件: {mod_name}")

    def disable_mod(self, mod_name):
        """禁用插件"""
        config = self.get_mod_config(mod_name)
        config["status"] = ModStatus.DISABLED.value
        config["enabled"] = False
        self.set_mod_config(mod_name, config)
        print(f"禁用插件: {mod_name}")

    def hide_mod(self, mod_name):
        """隐藏插件（不在选项卡中显示）"""
        config = self.get_mod_config(mod_name)
        config["visible"] = False
        self.set_mod_config(mod_name, config)
        print(f"隐藏插件: {mod_name}")

    def show_mod(self, mod_name):
        """显示插件"""
        config = self.get_mod_config(mod_name)
        config["visible"] = True
        self.set_mod_config(mod_name, config)
        print(f"显示插件: {mod_name}")

    def set_mod_priority(self, mod_name, priority):
        """设置插件优先级"""
        config = self.get_mod_config(mod_name)
        config["priority"] = max(0, min(100, priority))
        self.set_mod_config(mod_name, config)
        print(f"设置插件优先级: {mod_name} -> {priority}")

    def set_mod_setting(self, mod_name, key, value):
        """设置插件特定设置"""
        config = self.get_mod_config(mod_name)
        if "settings" not in config:
            config["settings"] = {}
        config["settings"][key] = value
        self.set_mod_config(mod_name, config)
        print(f"设置插件设置: {mod_name}.{key} = {value}")

    def get_mod_setting(self, mod_name, key, default=None):
        """获取插件特定设置"""
        config = self.get_mod_config(mod_name)
        return config.get("settings", {}).get(key, default)

    def is_mod_enabled(self, mod_name):
        """检查插件是否启用"""
        config = self.get_mod_config(mod_name)
        return config.get("enabled", True)

    def is_mod_visible(self, mod_name):
        """检查插件是否可见"""
        config = self.get_mod_config(mod_name)
        return config.get("visible", True)

    def get_mod_priority(self, mod_name):
        """获取插件优先级"""
        config = self.get_mod_config(mod_name)
        return config.get("priority", 50)

    def get_all_mods_config(self):
        """获取所有插件配置"""
        return self.config_data

    def delete_mod_config(self, mod_name):
        """删除插件配置"""
        if mod_name in self.config_data:
            del self.config_data[mod_name]
            self.save_config()
            print(f"删除插件配置: {mod_name}")
            return True
        return False

    def reset_all_configs(self):
        """重置所有配置"""
        self.config_data = {}
        self.save_config()
        print("重置所有插件配置")

    def export_config(self, export_file):
        """导出配置到文件"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            print(f"导出插件配置到: {export_file}")
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, import_file):
        """从文件导入配置"""
        if os.path.exists(import_file):
            try:
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                self.config_data.update(imported_data)
                self.save_config()
                print(f"从文件导入插件配置: {import_file}")
                return True
            except Exception as e:
                print(f"导入配置失败: {e}")
                return False
        return False