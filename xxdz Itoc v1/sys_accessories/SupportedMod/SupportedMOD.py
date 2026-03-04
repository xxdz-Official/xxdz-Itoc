# sys_accessories/SupportedMod/SupportedMOD.py
# 第三方插件（Mod）支持模块 - 完整版

import os
import sys
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime
import inspect
from enum import Enum


class SupportedMOD:
    """第三方插件管理器 - 完整版"""

    def __init__(self, app_reference):
        """
        初始化插件管理器

        Args:
            app_reference: 主程序引用，插件可以通过这个引用访问主程序功能
        """
        self.app = app_reference
        self.app_data = ItocAppData(app_reference)  # 数据传递对象
        self.mods = []  # 已加载的插件列表
        self.mod_tabs = {}  # 插件选项卡字典 {mod_name: tab_frame}
        self.mod_modules = {}  # 插件模块字典 {mod_name: module}
        self.active_mod = None  # 当前活跃的插件

        # 插件目录路径
        self.mods_dir = "mod"

        # 插件配置管理器
        try:
            from ModConfig import ModConfigManager
            self.config_manager = ModConfigManager()
            print("插件配置管理器初始化成功")
        except ImportError as e:
            print(f"插件配置管理器初始化失败: {e}")
            # 创建一个简单的配置管理器作为回退
            self.config_manager = SimpleConfigManager()

class ModState(Enum):
    """插件状态枚举"""
    UNLOADED = 0  # 未加载
    LOADED = 1  # 已加载
    INITIALIZED = 2  # 已初始化
    ACTIVE = 3  # 活跃中
    ERROR = 4  # 错误状态


class ItocModInfo:
    """插件信息类"""

    def __init__(self, mod_path, mod_name, mod_main_module):
        self.mod_path = mod_path  # 插件目录路径
        self.mod_name = mod_name  # 插件名称（目录名）
        self.mod_main_module = mod_main_module  # 主模块对象
        self.mod_display_name = mod_name  # 显示名称
        self.mod_description = ""  # 插件描述
        self.mod_version = "1.0.0"  # 插件版本
        self.mod_author = "Unknown"  # 作者
        self.mod_website = ""  # 作者网站
        self.mod_tab_frame = None  # 选项卡帧
        self.mod_state = ModState.UNLOADED  # 插件状态
        self.mod_last_error = None  # 最后错误信息
        self.mod_requirements = []  # 依赖要求
        self.mod_icon_path = None  # 图标路径
        self.mod_category = "General"  # 插件分类
        self.mod_priority = 50  # 优先级 (0-100)
        self.mod_config = {}  # 插件配置
        self.mod_created = datetime.now()  # 创建时间
        self.mod_last_active = None  # 最后活跃时间

        # 插件界面组件引用
        self.mod_widgets = {}

    def __str__(self):
        return f"ItocModInfo(name={self.mod_display_name}, state={self.mod_state.name}, version={self.mod_version})"

    def get_info_dict(self):
        """获取插件信息字典"""
        return {
            "name": self.mod_name,
            "display_name": self.mod_display_name,
            "description": self.mod_description,
            "version": self.mod_version,
            "author": self.mod_author,
            "website": self.mod_website,
            "state": self.mod_state.name,
            "path": self.mod_path,
            "category": self.mod_category,
            "priority": self.mod_priority,
            "created": self.mod_created.isoformat() if self.mod_created else None,
            "last_active": self.mod_last_active.isoformat() if self.mod_last_active else None,
            "requirements": self.mod_requirements
        }


class ItocAppData:
    """主程序数据传递类"""

    def __init__(self, app_reference):
        self.app = app_reference

    def get_all_data(self):
        """获取所有主程序数据"""
        if not self.app:
            return {}

        data = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        }

        try:
            # 基本播放状态
            data["playback"] = {
                "is_playing": getattr(self.app, 'is_playing', False),
                "current_beat": getattr(self.app, 'current_beat', 0.0),
                "current_time_ms": getattr(self.app, 'media_current_time', 0.0) * 1000,
                "judge_line_x": getattr(self.app, 'judge_line_x', 0),
                "total_beats": getattr(self.app, 'midi_total_beat', 32),
                "bpm": {
                    "original": getattr(self.app, 'midi_original_bpm', 120),
                    "target": getattr(self.app, 'target_bpm', 120)
                }
            }

            # 工程文件信息
            data["project"] = {
                "path": getattr(self.app, 'current_project_path', ""),
                "filename": os.path.basename(getattr(self.app, 'current_project_path', "")) if getattr(self.app,
                                                                                                       'current_project_path',
                                                                                                       "") else "",
                "modified": getattr(self.app, 'project_modified', False),
                "total_notes": getattr(self.app, 'total_notes', 0)
            }

            # 文件路径
            data["files"] = {
                "midi_path": getattr(self.app, 'current_midi_path', ""),
                "audio_path": getattr(self.app, 'media_path', ""),
                "audio_duration": getattr(self.app, 'media_duration', 0.0),
                "srt_path": getattr(self.app.srt_manager, 'subtitle_file', "") if hasattr(self.app,
                                                                                          'srt_manager') and self.app.srt_manager else ""
            }

            # 音符数据
            data["notes"] = {
                "total_count": getattr(self.app, 'total_notes', 0),
                "selected_count": len(getattr(self.app, 'selected_notes', [])),
                "selected_ids": [int(note_id) for note_id in getattr(self.app, 'selected_notes', [])],
                "all_notes_count": len(getattr(self.app, 'all_notes', []))
            }

            # CZEmakers 相关数据
            data["czemakers"] = {
                "has_module": hasattr(self.app, 'cz_makers') and self.app.cz_makers is not None,
                "selected_notes_cze": []
            }

            # 获取选中音符的CZEmakers属性
            if hasattr(self.app, 'selected_notes') and self.app.selected_notes:
                cze_data = []
                for note_id in self.app.selected_notes:
                    for note_data in getattr(self.app, 'all_notes', []):
                        if len(note_data) >= 6 and note_data[4] == note_id:
                            cze_makers = note_data[5]
                            if cze_makers and isinstance(cze_makers, dict):
                                cze_data.append({
                                    "note_id": int(note_id),
                                    "note_value": note_data[3],
                                    "track_idx": note_data[0],
                                    "start_beat": note_data[1],
                                    "cze_properties": cze_makers
                                })
                            break
                data["czemakers"]["selected_notes_cze"] = cze_data

            # 标记和全局命令数据
            data["markers"] = {
                "count": 0,
                "list": []
            }

            if hasattr(self.app, 'marker_manager') and self.app.marker_manager:
                data["markers"]["count"] = self.app.marker_manager.get_marker_count()
                # 这里可以添加标记的详细信息

            data["global_commands"] = {
                "count": 0,
                "list": []
            }

            if hasattr(self.app, 'global_command_manager') and self.app.global_command_manager:
                data["global_commands"]["count"] = self.app.global_command_manager.get_command_count()
                # 这里可以添加全局命令的详细信息

            # 音频音谱数据
            data["audio_spectrum"] = {
                "has_module": hasattr(self.app, 'yinpin_yinpu') and self.app.yinpin_yinpu is not None,
                "is_active": getattr(self.app.yinpin_yinpu, 'is_active', False) if hasattr(self.app,
                                                                                           'yinpin_yinpu') and self.app.yinpin_yinpu else False
            }

            # SRT字幕数据
            data["subtitles"] = {
                "has_module": hasattr(self.app, 'srt_manager') and self.app.srt_manager is not None,
                "current_subtitle": None
            }

            if hasattr(self.app, 'srt_manager') and self.app.srt_manager:
                current_time_ms = data["playback"]["current_time_ms"]
                current_sub = self.app.srt_manager.get_current_subtitle(current_time_ms)
                if current_sub:
                    data["subtitles"]["current_subtitle"] = {
                        "text": current_sub.text,
                        "start": current_sub.start,
                        "end": current_sub.end
                    }

            # 终端数据
            data["terminal"] = {
                "is_active": getattr(self.app, 'terminal_active', False)
            }

            # 用户统计
            data["user_stats"] = {
                "today_uses": 0,
                "total_uses": 0
            }

            if hasattr(self.app, 'user_stats') and self.app.user_stats:
                data["user_stats"]["today_uses"] = self.app.user_stats.get_today_uses()
                data["user_stats"]["total_uses"] = self.app.user_stats.get_total_uses()

            # 插件系统状态
            data["mod_system"] = {
                "total_mods": len(getattr(self.app, 'mod_infos', [])),
                "active_mod": None
            }

            # 窗口和UI状态
            data["ui"] = {
                "window_title": self.app.root.title() if hasattr(self.app, 'root') else "",
                "canvas_size": {
                    "width": self.app.canvas.winfo_width() if hasattr(self.app, 'canvas') else 0,
                    "height": self.app.canvas.winfo_height() if hasattr(self.app, 'canvas') else 0
                },
                "scale_factor": getattr(self.app, 'scale_factor_x', 1.0),
                "volume": {
                    "master": getattr(self.app, 'master_volume', 1.0),
                    "midi": getattr(self.app, 'midi_volume', 1.0),
                    "audio": getattr(self.app, 'audio_volume', 1.0)
                }
            }

            # 配置信息
            data["config"] = {
                "config_file": "shezhi.txt",
                "has_config": os.path.exists("shezhi.txt")
            }

            # 音频起始时间
            data["audio_start"] = {
                "start_time_ms": getattr(self.app, 'audio_start_time_ms', 0.0),
                "initialized": getattr(self.app, 'audio_start_time_initialized', False)
            }

            # 音调控制
            data["pitch_control"] = {
                "intensity": self.app.pitch_control.get_intensity() if hasattr(self.app,
                                                                               'pitch_control') and self.app.pitch_control else 2.0
            }

            # 选择模式和自动跟随
            data["modes"] = {
                "select_mode": self.app.select_mode.is_active() if hasattr(self.app,
                                                                           'select_mode') and self.app.select_mode else False,
                "auto_follow": self.app.auto_follow.is_enabled() if hasattr(self.app,
                                                                            'auto_follow') and self.app.auto_follow else False,
                "move_mode": self.app.note_mover.move_mode if hasattr(self.app,
                                                                      'note_mover') and self.app.note_mover else False
            }

            # 模块可用性
            data["modules"] = {
                "czemakers": CZEMAKERS_MODULE_AVAILABLE,
                "midi_color": MIDI_COLOR_MODULE_AVAILABLE,
                "srt": SRT_MODULE_AVAILABLE,
                "yinpin_yinpu": YINPINYINPU_MODULE_AVAILABLE,
                "terminal": hasattr(self.app, 'terminal_widget') and self.app.terminal_widget is not None,
                "marker": MARK_MODULE_AVAILABLE,
                "move": MOVE_MODULE_AVAILABLE,
                "global_command": GLOBAL_COMMAND_MODULE_AVAILABLE,
                "recent_files": RECENT_FILES_MODULE_AVAILABLE,
                "timeline_fix": TIMELINE_FIX_MODULE_AVAILABLE,
                "supported_mod": SUPPORTED_MOD_AVAILABLE
            }

            # 系统信息
            data["system"] = {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd(),
                "app_start_time": getattr(self.app, 'app_start_time', None)
            }

        except Exception as e:
            data["error"] = f"获取数据时出错: {str(e)}"

        return data

    def send_event(self, event_type, event_data=None):
        """向主程序发送事件"""
        if not self.app:
            return False

        try:
            # 这里可以定义一些插件可以触发的事件
            events = {
                "refresh_display": lambda: self.app.refresh_cze_display() if hasattr(self.app,
                                                                                     'refresh_cze_display') else None,
                "update_selection": lambda: self.app.on_selection_changed() if hasattr(self.app,
                                                                                       'on_selection_changed') else None,
                "play_pause": lambda: self.app.toggle_play_pause() if hasattr(self.app, 'toggle_play_pause') else None,
                "stop_play": lambda: self.app.stop_play() if hasattr(self.app, 'stop_play') else None,
                "save_project": lambda: self.app.save_cze_project() if hasattr(self.app, 'save_cze_project') else None,
                "load_midi": lambda path: self.app.load_midi() if hasattr(self.app, 'load_midi') else None,
                "select_media": lambda: self.app.select_media() if hasattr(self.app, 'select_media') else None,
                "set_bpm": lambda bpm: self.app.set_bpm_from_value(bpm) if hasattr(self.app,
                                                                                   'set_bpm_from_value') else None
            }

            if event_type in events:
                if event_data:
                    return events[event_type](event_data)
                else:
                    return events[event_type]()
            else:
                print(f"未知事件类型: {event_type}")
                return False

        except Exception as e:
            print(f"发送事件失败: {e}")
            return False


class SupportedMOD:
    """第三方插件管理器 - 完整版"""

    def __init__(self, app_reference):
        """
        初始化插件管理器

        Args:
            app_reference: 主程序引用，插件可以通过这个引用访问主程序功能
        """
        self.app = app_reference
        self.app_data = ItocAppData(app_reference)  # 数据传递对象
        self.mods = []  # 已加载的插件列表
        self.mod_tabs = {}  # 插件选项卡字典 {mod_name: tab_frame}
        self.mod_modules = {}  # 插件模块字典 {mod_name: module}
        self.active_mod = None  # 当前活跃的插件
        self.mod_update_thread = None  # 插件数据更新线程
        self.mod_update_interval = 1.0  # 数据更新间隔（秒）
        self.mod_update_running = False  # 更新线程运行标志

        # 插件目录路径
        self.mods_dir = "mod"

        # 插件事件回调
        self.mod_event_handlers = {}

        # 创建插件数据共享字典
        self.shared_data = {
            "last_update": time.time(),
            "plugins_data": {}
        }

        print("第三方插件管理器初始化完成")

    def scan_mods(self):
        """扫描mod目录下的所有插件"""
        print("=" * 60)
        print("开始扫描第三方插件...")

        # 确保mod目录存在
        if not os.path.exists(self.mods_dir):
            print(f"插件目录 '{self.mods_dir}' 不存在，创建目录")
            os.makedirs(self.mods_dir, exist_ok=True)

            # 创建示例插件目录结构
            self.create_sample_mod_structure()
            return []

        # 获取所有子目录（每个目录代表一个插件）
        mod_dirs = []
        for item in os.listdir(self.mods_dir):
            item_path = os.path.join(self.mods_dir, item)
            if os.path.isdir(item_path):
                mod_dirs.append(item_path)

        print(f"找到 {len(mod_dirs)} 个插件目录")

        loaded_mods = []
        for mod_dir in mod_dirs:
            mod_info = self.load_mod(mod_dir)
            if mod_info:
                loaded_mods.append(mod_info)

        # 按优先级排序
        loaded_mods.sort(key=lambda x: x.mod_priority, reverse=True)

        print(f"成功加载 {len(loaded_mods)} 个插件")
        print("=" * 60)
        return loaded_mods

    def load_mod(self, mod_dir):
        """加载单个插件"""
        mod_name = os.path.basename(mod_dir)

        print(f"\n尝试加载插件: {mod_name}")
        print(f"  路径: {mod_dir}")

        # 检查必需的文件
        main_file = os.path.join(mod_dir, "ItocMod.py")
        name_file = os.path.join(mod_dir, "ModName.txt")

        # 检查主文件
        if not os.path.exists(main_file):
            print(f"  警告: 插件 '{mod_name}' 缺少主文件 ItocMod.py")
            # 检查是否有其他可能的入口文件
            possible_files = ["main.py", "plugin.py", "mod.py", "entry.py"]
            for file in possible_files:
                alt_file = os.path.join(mod_dir, file)
                if os.path.exists(alt_file):
                    print(f"  发现替代入口文件: {file}")
                    main_file = alt_file
                    break
            else:
                print(f"  错误: 找不到入口文件，跳过此插件")
                return None

        # 读取插件名称
        mod_display_name = mod_name
        if os.path.exists(name_file):
            try:
                with open(name_file, 'r', encoding='utf-8') as f:
                    mod_display_name = f.read().strip()
                print(f"  插件显示名称: {mod_display_name}")
            except Exception as e:
                print(f"  读取插件名称文件失败: {e}")

        # 尝试加载插件模块
        try:
            # 将插件目录添加到Python路径
            if mod_dir not in sys.path:
                sys.path.insert(0, mod_dir)

            # 动态加载模块
            module_name = f"itoc_mod_{mod_name.replace(' ', '_').lower()}"
            spec = importlib.util.spec_from_file_location(module_name, main_file)
            mod_module = importlib.util.module_from_spec(spec)

            # 创建插件信息对象
            mod_info = ItocModInfo(mod_dir, mod_name, mod_module)
            mod_info.mod_display_name = mod_display_name
            mod_info.mod_state = ModState.LOADED

            # 尝试加载插件元数据
            self.load_mod_metadata(mod_info)

            # 保存模块引用
            self.mod_modules[mod_name] = mod_module
            mod_info.mod_state = ModState.LOADED

            print(f"  [OK] 成功加载插件: {mod_display_name} v{mod_info.mod_version}")
            return mod_info

        except Exception as e:
            print(f"  [ERROR] 加载插件 '{mod_name}' 失败: {e}")
            mod_info.mod_state = ModState.ERROR
            mod_info.mod_last_error = str(e)
            import traceback
            traceback.print_exc()
            return mod_info

    def load_mod_metadata(self, mod_info):
        """加载插件的元数据（描述、版本、作者等）"""
        # 首先尝试读取 Attribute.txt 文件
        attribute_file = os.path.join(mod_info.mod_path, "Attribute.txt")

        if os.path.exists(attribute_file):
            try:
                print(f"    读取 Attribute.txt 文件")
                attributes = self.parse_attribute_file(attribute_file)

                # 从 Attribute.txt 中读取信息
                mod_info.mod_display_name = attributes.get('displayname', mod_info.mod_display_name)
                mod_info.mod_description = attributes.get('description', mod_info.mod_description)
                mod_info.mod_version = attributes.get('version', mod_info.mod_version)
                mod_info.mod_author = attributes.get('author', mod_info.mod_author)

                # 处理作者网站（单独存储）
                website = attributes.get('website', '')
                if website:
                    mod_info.mod_website = website
                    print(f"    网站: {website}")

                print(f"    版本: {mod_info.mod_version}")
                print(f"    作者: {mod_info.mod_author}")
                if mod_info.mod_description:
                    desc_preview = mod_info.mod_description[:80] + "..." if len(
                        mod_info.mod_description) > 80 else mod_info.mod_description
                    print(f"    描述: {desc_preview}")

                # 属性文件加载成功，直接返回
                return

            except Exception as e:
                print(f"    读取 Attribute.txt 文件失败: {e}")

        # 如果 Attribute.txt 不存在或读取失败，回退到旧的 ModInfo.json
        metadata_file = os.path.join(mod_info.mod_path, "ModInfo.json")

        if os.path.exists(metadata_file):
            try:
                print(f"    读取 ModInfo.json 文件")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                mod_info.mod_description = metadata.get("description", "")
                mod_info.mod_version = metadata.get("version", "1.0.0")
                mod_info.mod_author = metadata.get("author", "Unknown")
                mod_info.mod_category = metadata.get("category", "General")
                mod_info.mod_priority = metadata.get("priority", 50)
                mod_info.mod_requirements = metadata.get("requirements", [])
                mod_info.mod_config = metadata.get("config", {})

                # 从旧格式中读取网站信息（如果存在）
                if 'website' in metadata:
                    mod_info.mod_website = metadata['website']

                print(f"    版本: {mod_info.mod_version}")
                print(f"    作者: {mod_info.mod_author}")
                if mod_info.mod_website:
                    print(f"    网站: {mod_info.mod_website}")
                print(f"    分类: {mod_info.mod_category}")
                if mod_info.mod_description:
                    desc_preview = mod_info.mod_description[:80] + "..." if len(
                        mod_info.mod_description) > 80 else mod_info.mod_description
                    print(f"    描述: {desc_preview}")

            except Exception as e:
                print(f"    读取插件元数据失败: {e}")

        # 检查图标文件
        icon_files = ["icon.png", "icon.ico", "icon.jpg", "icon.gif"]
        for icon_file in icon_files:
            icon_path = os.path.join(mod_info.mod_path, icon_file)
            if os.path.exists(icon_path):
                mod_info.mod_icon_path = icon_path
                print(f"    图标: {icon_file}")
                break

    def parse_attribute_file(self, file_path):
        """解析Attribute.txt文件"""
        attributes = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue

                    # 处理键值对：key=value 或 key: value
                    key_value_pair = None
                    if '=' in line:
                        key_value_pair = line.split('=', 1)
                    elif ':' in line and not line.startswith('http'):  # 避免将网址分割
                        key_value_pair = line.split(':', 1)

                    if key_value_pair and len(key_value_pair) == 2:
                        key = key_value_pair[0].strip()
                        value = key_value_pair[1].strip()
                        attributes[key.lower()] = value

        except Exception as e:
            print(f"  解析Attribute.txt失败: {str(e)}")

        return attributes

    def create_mod_tab(self, mod_info, notebook):
        """为插件创建选项卡"""
        try:
            # 创建选项卡帧
            tab_frame = ttk.Frame(notebook)

            # 设置选项卡文本（包含图标标识）
            tab_text = mod_info.mod_display_name
            if mod_info.mod_state == ModState.ERROR:
                tab_text += " ⚠"
            elif mod_info.mod_priority > 80:
                tab_text += " ★"

            # 添加到选项卡控件
            notebook.add(tab_frame, text=tab_text)

            # 保存引用
            mod_info.mod_tab_frame = tab_frame
            self.mod_tabs[mod_info.mod_name] = tab_frame

            print(f"为插件 '{mod_info.mod_display_name}' 创建了选项卡")

            return tab_frame

        except Exception as e:
            print(f"创建插件选项卡失败: {e}")
            return None

    def initialize_mod(self, mod_info):
        """初始化插件"""
        try:
            if mod_info.mod_state == ModState.INITIALIZED or mod_info.mod_state == ModState.ACTIVE:
                return True

            if mod_info.mod_state == ModState.ERROR:
                print(f"插件 {mod_info.mod_display_name} 处于错误状态，无法初始化")
                return False

            print(f"初始化插件: {mod_info.mod_display_name}")

            # 获取模块
            mod_module = self.mod_modules.get(mod_info.mod_name)
            if not mod_module:
                print(f"  错误: 找不到模块 {mod_info.mod_name}")
                mod_info.mod_state = ModState.ERROR
                return False

            # 导入模块
            module_name = f"itoc_mod_{mod_info.mod_name.replace(' ', '_').lower()}"
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(mod_info.mod_path, "ItocMod.py")
            )

            try:
                mod_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mod_module
                spec.loader.exec_module(mod_module)
            except Exception as e:
                print(f"  导入模块失败: {e}")
                mod_info.mod_state = ModState.ERROR
                mod_info.mod_last_error = str(e)
                return False

            # 检查模块是否有初始化函数
            if hasattr(mod_module, 'initialize_mod'):
                print(f"  调用插件的 initialize_mod() 函数")
                try:
                    # 获取函数参数
                    sig = inspect.signature(mod_module.initialize_mod)
                    params = list(sig.parameters.keys())

                    # 根据参数数量调用
                    if len(params) == 3:
                        # 包含app, tab_frame, app_data
                        mod_module.initialize_mod(self.app, mod_info.mod_tab_frame, self.app_data)
                    elif len(params) == 2:
                        # 包含app, tab_frame
                        mod_module.initialize_mod(self.app, mod_info.mod_tab_frame)
                    elif len(params) == 1:
                        # 只包含app
                        mod_module.initialize_mod(self.app)
                    else:
                        print(f"  警告: initialize_mod 函数参数不匹配")
                        mod_module.initialize_mod(self.app, mod_info.mod_tab_frame, self.app_data)

                except Exception as e:
                    print(f"  调用 initialize_mod 失败: {e}")
                    mod_info.mod_state = ModState.ERROR
                    mod_info.mod_last_error = str(e)
                    return False
            else:
                print(f"  警告: 插件没有 initialize_mod 函数")

            mod_info.mod_state = ModState.INITIALIZED
            mod_info.mod_last_error = None
            print(f"  [OK] 插件初始化完成")
            return True

        except Exception as e:
            print(f"初始化插件失败: {e}")
            mod_info.mod_state = ModState.ERROR
            mod_info.mod_last_error = str(e)
            import traceback
            traceback.print_exc()
            return False

    def activate_mod_tab(self, mod_info):
        """激活插件选项卡（当用户点击该选项卡时调用）"""
        try:
            print(f"激活插件选项卡: {mod_info.mod_display_name}")

            # 更新最后活跃时间
            mod_info.mod_last_active = datetime.now()

            # 如果插件未初始化，先初始化
            if mod_info.mod_state != ModState.INITIALIZED and mod_info.mod_state != ModState.ACTIVE:
                print(f"  插件未初始化，正在初始化...")
                if not self.initialize_mod(mod_info):
                    print(f"  [ERROR] 插件初始化失败")
                    return False

            # 停用之前的活跃插件
            if self.active_mod and self.active_mod != mod_info:
                self.deactivate_mod_tab(self.active_mod)

            # 检查模块是否有激活函数
            mod_module = self.mod_modules.get(mod_info.mod_name)
            if mod_module and hasattr(mod_module, 'activate_mod'):
                print(f"  调用插件的 activate_mod() 函数")
                try:
                    # 获取函数参数
                    sig = inspect.signature(mod_module.activate_mod)
                    params = list(sig.parameters.keys())

                    # 获取当前应用数据
                    current_data = self.app_data.get_all_data()

                    # 根据参数数量调用
                    if len(params) == 3:
                        # 包含app, tab_frame, app_data
                        mod_module.activate_mod(self.app, mod_info.mod_tab_frame, current_data)
                    elif len(params) == 2:
                        # 包含app, tab_frame
                        mod_module.activate_mod(self.app, mod_info.mod_tab_frame)
                    elif len(params) == 1:
                        # 只包含app
                        mod_module.activate_mod(self.app)
                    else:
                        mod_module.activate_mod(self.app, mod_info.mod_tab_frame, current_data)

                except Exception as e:
                    print(f"  调用 activate_mod 失败: {e}")

            mod_info.mod_state = ModState.ACTIVE
            self.active_mod = mod_info

            # 启动数据更新线程（如果尚未启动）
            if not self.mod_update_running:
                self.start_data_update_thread()

            print(f"  [OK] 插件激活完成")
            return True

        except Exception as e:
            print(f"激活插件选项卡失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def deactivate_mod_tab(self, mod_info):
        """停用插件选项卡（当用户切换到其他选项卡时调用）"""
        try:
            if mod_info.mod_state != ModState.ACTIVE:
                return

            print(f"停用插件选项卡: {mod_info.mod_display_name}")

            mod_module = self.mod_modules.get(mod_info.mod_name)
            if mod_module and hasattr(mod_module, 'deactivate_mod'):
                print(f"  调用插件的 deactivate_mod() 函数")
                try:
                    mod_module.deactivate_mod(self.app)
                except Exception as e:
                    print(f"  调用 deactivate_mod 失败: {e}")

            mod_info.mod_state = ModState.INITIALIZED
            if self.active_mod == mod_info:
                self.active_mod = None

        except Exception as e:
            print(f"停用插件选项卡失败: {e}")

    def start_data_update_thread(self):
        """启动数据更新线程，定期向活跃插件发送数据"""
        if self.mod_update_running:
            return

        self.mod_update_running = True

        def update_loop():
            while self.mod_update_running:
                try:
                    # 如果有活跃插件，发送数据更新
                    if self.active_mod and self.active_mod.mod_state == ModState.ACTIVE:
                        self.update_active_mod_data()

                    # 更新共享数据
                    self.shared_data["last_update"] = time.time()
                    self.shared_data["plugins_data"] = {
                        mod.mod_name: mod.get_info_dict() for mod in self.mods
                    }

                except Exception as e:
                    print(f"数据更新线程错误: {e}")

                time.sleep(self.mod_update_interval)

        self.mod_update_thread = threading.Thread(target=update_loop, daemon=True)
        self.mod_update_thread.start()
        print("插件数据更新线程已启动")

    def update_active_mod_data(self):
        """向活跃插件发送数据更新"""
        try:
            mod_module = self.mod_modules.get(self.active_mod.mod_name)
            if not mod_module:
                return

            # 检查插件是否有数据更新处理函数
            if hasattr(mod_module, 'on_data_update'):
                # 获取所有应用数据
                app_data = self.app_data.get_all_data()

                try:
                    # 调用插件的on_data_update函数
                    mod_module.on_data_update(self.app, app_data)
                except Exception as e:
                    print(f"插件数据更新失败: {e}")

        except Exception as e:
            print(f"更新活跃插件数据失败: {e}")

    def send_event_to_mods(self, event_type, event_data=None, target_mod=None):
        """向插件发送事件"""
        try:
            if target_mod:
                # 发送给特定插件
                mod_module = self.mod_modules.get(target_mod)
                if mod_module and hasattr(mod_module, 'on_event'):
                    mod_module.on_event(self.app, event_type, event_data)
            else:
                # 发送给所有插件
                for mod_name, mod_module in self.mod_modules.items():
                    if hasattr(mod_module, 'on_event'):
                        try:
                            mod_module.on_event(self.app, event_type, event_data)
                        except Exception as e:
                            print(f"向插件 {mod_name} 发送事件失败: {e}")

        except Exception as e:
            print(f"发送事件失败: {e}")

    def get_mod_info(self, mod_name):
        """获取插件信息"""
        for mod_info in self.mods:
            if mod_info.mod_name == mod_name:
                return mod_info
        return None

    def get_all_mods_info(self):
        """获取所有插件信息"""
        return [mod.get_info_dict() for mod in self.mods]

    def get_app_data_snapshot(self):
        """获取应用数据快照"""
        return self.app_data.get_all_data()

    def register_event_handler(self, event_type, handler_func, mod_name):
        """注册事件处理器"""
        if event_type not in self.mod_event_handlers:
            self.mod_event_handlers[event_type] = []

        self.mod_event_handlers[event_type].append({
            "mod_name": mod_name,
            "handler": handler_func
        })
        print(f"插件 {mod_name} 注册了事件处理器: {event_type}")

    def trigger_event(self, event_type, event_data=None):
        """触发事件"""
        if event_type in self.mod_event_handlers:
            for handler_info in self.mod_event_handlers[event_type]:
                try:
                    handler_info["handler"](event_data)
                except Exception as e:
                    print(f"事件处理器 {event_type} 执行失败: {e}")

    def create_sample_mod_structure(self):
        """创建示例插件目录结构"""
        print("创建示例插件目录结构...")

        sample_mod_dir = os.path.join(self.mods_dir, "示例插件")
        os.makedirs(sample_mod_dir, exist_ok=True)

        # 创建ModName.txt
        with open(os.path.join(sample_mod_dir, "ModName.txt"), 'w', encoding='utf-8') as f:
            f.write("示例插件")

        # 创建ModInfo.json
        mod_info = {
            "description": "这是一个示例插件，演示插件系统的功能",
            "version": "1.0.0",
            "author": "Itoc开发团队",
            "category": "示例",
            "priority": 90,
            "supported_features": ["数据监视", "工程管理", "实时预览"],
            "requirements": [],
            "config": {
                "auto_update": True,
                "debug_mode": False
            }
        }

        with open(os.path.join(sample_mod_dir, "ModInfo.json"), 'w', encoding='utf-8') as f:
            json.dump(mod_info, f, ensure_ascii=False, indent=2)

        # 创建ItocMod.py（示例代码会在后面提供）
        sample_code = '''# mod/示例插件/ItocMod.py
# 示例插件 - 完整功能演示

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import json

# 插件全局变量
plugin_data = {
    "start_time": None,
    "update_count": 0,
    "last_data": None
}

def initialize_mod(app, tab_frame, app_data):
    """插件初始化函数"""
    global plugin_data

    plugin_data["start_time"] = datetime.now()
    print(f"示例插件初始化，时间: {plugin_data['start_time']}")

    # 在选项卡中添加内容
    create_plugin_ui(tab_frame, app, app_data)

    print("示例插件初始化完成")

def create_plugin_ui(tab_frame, app, app_data):
    """创建插件界面"""
    # 标题
    title_label = ttk.Label(tab_frame, text="🎵 Itoc 示例插件", 
                           font=("微软雅黑", 16, "bold"))
    title_label.pack(pady=10)

    # 描述
    desc_label = ttk.Label(tab_frame, 
                          text="这是一个功能完整的示例插件，演示插件系统的各种功能",
                          font=("微软雅黑", 10))
    desc_label.pack(pady=5)

    # 分隔线
    ttk.Separator(tab_frame, orient='horizontal').pack(fill='x', padx=20, pady=10)

    # 创建主框架
    main_frame = ttk.Frame(tab_frame)
    main_frame.pack(fill='both', expand=True, padx=10, pady=5)

    # 左侧框架 - 数据显示
    left_frame = ttk.LabelFrame(main_frame, text="实时数据", padding=10)
    left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

    # 右侧框架 - 控制面板
    right_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
    right_frame.pack(side='right', fill='y', padx=(5, 0))

    # 左侧：数据标签
    global data_labels
    data_labels = {}

    # 播放状态
    play_frame = ttk.Frame(left_frame)
    play_frame.pack(fill='x', pady=5)

    ttk.Label(play_frame, text="播放状态:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["play_status"] = ttk.Label(play_frame, text="未知", foreground="gray")
    data_labels["play_status"].pack(side='left', padx=5)

    # 当前时间
    time_frame = ttk.Frame(left_frame)
    time_frame.pack(fill='x', pady=5)

    ttk.Label(time_frame, text="当前时间:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["current_time"] = ttk.Label(time_frame, text="0.000s", foreground="blue")
    data_labels["current_time"].pack(side='left', padx=5)

    # BPM信息
    bpm_frame = ttk.Frame(left_frame)
    bpm_frame.pack(fill='x', pady=5)

    ttk.Label(bpm_frame, text="BPM:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["bpm_info"] = ttk.Label(bpm_frame, text="120", foreground="green")
    data_labels["bpm_info"].pack(side='left', padx=5)

    # 工程信息
    project_frame = ttk.Frame(left_frame)
    project_frame.pack(fill='x', pady=5)

    ttk.Label(project_frame, text="工程文件:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["project_file"] = ttk.Label(project_frame, text="无", foreground="purple")
    data_labels["project_file"].pack(side='left', padx=5)

    # 音符信息
    notes_frame = ttk.Frame(left_frame)
    notes_frame.pack(fill='x', pady=5)

    ttk.Label(notes_frame, text="音符统计:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["notes_info"] = ttk.Label(notes_frame, text="0个音符", foreground="orange")
    data_labels["notes_info"].pack(side='left', padx=5)

    # CZEmakers信息
    cze_frame = ttk.Frame(left_frame)
    cze_frame.pack(fill='x', pady=5)

    ttk.Label(cze_frame, text="CZEmakers:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["cze_info"] = ttk.Label(cze_frame, text="无", foreground="red")
    data_labels["cze_info"].pack(side='left', padx=5)

    # 更新次数
    update_frame = ttk.Frame(left_frame)
    update_frame.pack(fill='x', pady=5)

    ttk.Label(update_frame, text="更新次数:", font=("微软雅黑", 10, "bold")).pack(side='left')
    data_labels["update_count"] = ttk.Label(update_frame, text="0", foreground="gray")
    data_labels["update_count"].pack(side='left', padx=5)

    # 右侧：控制按钮
    ttk.Button(right_frame, text="刷新数据", 
              command=lambda: refresh_data_manual(app_data)).pack(pady=5, fill='x')

    ttk.Button(right_frame, text="保存快照", 
              command=lambda: save_data_snapshot(app_data)).pack(pady=5, fill='x')

    ttk.Button(right_frame, text="测试事件", 
              command=lambda: send_test_event(app)).pack(pady=5, fill='x')

    ttk.Button(right_frame, text="显示信息", 
              command=show_plugin_info).pack(pady=5, fill='x')

    ttk.Button(right_frame, text="调试控制台", 
              command=open_debug_console).pack(pady=5, fill='x')

    # 插件状态
    status_frame = ttk.Frame(right_frame)
    status_frame.pack(pady=10)

    ttk.Label(status_frame, text="插件状态:", font=("微软雅黑", 9)).pack()
    data_labels["plugin_status"] = ttk.Label(status_frame, text="已加载", foreground="green")
    data_labels["plugin_status"].pack()

def activate_mod(app, tab_frame, app_data):
    """插件激活函数"""
    print("示例插件被激活")

    if "plugin_status" in data_labels:
        data_labels["plugin_status"].config(text="活跃中", foreground="blue")

    # 立即更新一次数据
    on_data_update(app, app_data)

def deactivate_mod(app):
    """插件停用函数"""
    print("示例插件被停用")

    if "plugin_status" in data_labels:
        data_labels["plugin_status"].config(text="后台运行", foreground="orange")

def on_data_update(app, app_data):
    """数据更新处理函数"""
    global plugin_data

    plugin_data["update_count"] += 1
    plugin_data["last_data"] = app_data

    # 更新UI显示
    update_ui_with_data(app_data)

    # 每10次更新打印一次日志
    if plugin_data["update_count"] % 10 == 0:
        print(f"示例插件数据更新 {plugin_data['update_count']} 次")

def update_ui_with_data(app_data):
    """用新数据更新UI"""
    try:
        # 播放状态
        is_playing = app_data.get("playback", {}).get("is_playing", False)
        play_text = "播放中 ▶" if is_playing else "暂停 ⏸"
        play_color = "green" if is_playing else "gray"

        if "play_status" in data_labels:
            data_labels["play_status"].config(text=play_text, foreground=play_color)

        # 当前时间
        current_time = app_data.get("playback", {}).get("current_time_ms", 0)
        time_text = f"{current_time/1000:.3f}s"

        if "current_time" in data_labels:
            data_labels["current_time"].config(text=time_text)

        # BPM信息
        bpm_original = app_data.get("playback", {}).get("bpm", {}).get("original", 120)
        bpm_target = app_data.get("playback", {}).get("bpm", {}).get("target", 120)
        bpm_text = f"{bpm_target}/{bpm_original}"

        if "bpm_info" in data_labels:
            data_labels["bpm_info"].config(text=bpm_text)

        # 工程文件
        project_path = app_data.get("project", {}).get("filename", "无")
        if "project_file" in data_labels:
            data_labels["project_file"].config(text=project_path)

        # 音符信息
        total_notes = app_data.get("notes", {}).get("total_count", 0)
        selected_notes = app_data.get("notes", {}).get("selected_count", 0)
        notes_text = f"{total_notes}个 (选中{selected_notes}个)"

        if "notes_info" in data_labels:
            data_labels["notes_info"].config(text=notes_text)

        # CZEmakers信息
        cze_notes = app_data.get("czemakers", {}).get("selected_notes_cze", [])
        cze_text = f"{len(cze_notes)}个音符有属性"

        if "cze_info" in data_labels:
            data_labels["cze_info"].config(text=cze_text)

        # 更新次数
        if "update_count" in data_labels:
            data_labels["update_count"].config(text=str(plugin_data["update_count"]))

    except Exception as e:
        print(f"更新UI失败: {e}")

def refresh_data_manual(app_data):
    """手动刷新数据"""
    data = app_data.get_all_data()
    update_ui_with_data(data)
    messagebox.showinfo("手动刷新", "数据已刷新！")

def save_data_snapshot(app_data):
    """保存数据快照"""
    data = app_data.get_all_data()

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"plugin_snapshot_{timestamp}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("保存成功", f"数据快照已保存到:\\n{filename}")
        print(f"数据快照保存到: {filename}")

    except Exception as e:
        messagebox.showerror("保存失败", f"保存数据快照失败:\\n{str(e)}")

def send_test_event(app):
    """发送测试事件"""
    try:
        # 尝试调用主程序的事件发送功能
        if hasattr(app, 'supported_mod'):
            app.supported_mod.trigger_event("test_event", {"message": "来自示例插件"})
            messagebox.showinfo("测试事件", "测试事件已发送！")
        else:
            messagebox.showinfo("测试事件", "事件系统不可用")
    except Exception as e:
        print(f"发送测试事件失败: {e}")

def show_plugin_info():
    """显示插件信息"""
    info_text = f"""示例插件信息:

启动时间: {plugin_data['start_time']}
更新次数: {plugin_data['update_count']}
最后数据: {'有' if plugin_data['last_data'] else '无'}

这是一个功能完整的示例插件，演示了：
1. 实时数据监视
2. UI动态更新
3. 数据快照保存
4. 事件系统集成
5. 错误处理机制"""

    messagebox.showinfo("插件信息", info_text)

def open_debug_console():
    """打开调试控制台"""
    debug_win = tk.Toplevel()
    debug_win.title("示例插件调试控制台")
    debug_win.geometry("500x400")

    text_widget = tk.Text(debug_win, wrap=tk.WORD)
    text_widget.pack(fill='both', expand=True, padx=10, pady=10)

    info_text = f"""调试信息:

插件启动时间: {plugin_data['start_time']}
数据更新次数: {plugin_data['update_count']}
最后更新: {datetime.now()}

全局变量 data_labels 数量: {len(data_labels) if 'data_labels' in globals() else '未定义'}
"""

    text_widget.insert(1.0, info_text)
    text_widget.config(state=tk.DISABLED)

    ttk.Button(debug_win, text="关闭", command=debug_win.destroy).pack(pady=10)

def on_event(app, event_type, event_data):
    """事件处理函数"""
    print(f"示例插件收到事件: {event_type}")
    print(f"事件数据: {event_data}")

    if event_type == "test_event":
        messagebox.showinfo("插件事件", f"收到测试事件: {event_data.get('message', '无消息')}")

def cleanup_mod(app):
    """插件清理函数"""
    print("示例插件正在清理")

    # 保存插件状态
    try:
        state_file = "plugin_state.json"
        state_data = {
            "last_update": datetime.now().isoformat(),
            "total_updates": plugin_data["update_count"]
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)

        print(f"插件状态已保存到: {state_file}")
    except Exception as e:
        print(f"保存插件状态失败: {e}")

    print("示例插件清理完成")

# 全局变量声明
data_labels = {}
'''

        with open(os.path.join(sample_mod_dir, "ItocMod.py"), 'w', encoding='utf-8') as f:
            f.write(sample_code)

        print(f"示例插件已创建在: {sample_mod_dir}")

    def cleanup(self):
        """清理所有插件"""
        print("=" * 60)
        print("清理插件资源...")

        # 停止数据更新线程
        self.mod_update_running = False
        if self.mod_update_thread and self.mod_update_thread.is_alive():
            self.mod_update_thread.join(timeout=2.0)

        # 清理每个插件
        for mod_info in self.mods:
            try:
                mod_module = self.mod_modules.get(mod_info.mod_name)
                if mod_module and hasattr(mod_module, 'cleanup_mod'):
                    print(f"清理插件: {mod_info.mod_display_name}")
                    mod_module.cleanup_mod(self.app)
            except Exception as e:
                print(f"清理插件 {mod_info.mod_name} 失败: {e}")

        self.mods.clear()
        self.mod_tabs.clear()
        self.mod_modules.clear()
        self.active_mod = None
        self.mod_event_handlers.clear()

        print("插件资源清理完成")
        print("=" * 60)


# 插件开发者指南
"""
插件开发指南：

1. 文件结构：
   mod/
   └── 你的插件名称/
       ├── ItocMod.py      # 主文件（必需）
       ├── ModName.txt     # 显示名称（推荐）
       ├── ModInfo.json    # 元数据文件（推荐）
       └── icon.png        # 图标文件（可选）

2. ModInfo.json 格式：
   {
     "description": "插件描述",
     "version": "1.0.0",
     "author": "作者名",
     "category": "插件分类",
     "priority": 50,  // 0-100，数字越大越靠前
     "supported_features": ["功能1", "功能2"],
     "requirements": ["依赖1", "依赖2"],
     "config": {
       "auto_update": true,
       "debug_mode": false
     }
   }

3. 主文件必须包含的函数：
   - initialize_mod(app, tab_frame, app_data): 初始化插件
   - activate_mod(app, tab_frame, app_data): 激活插件选项卡
   - deactivate_mod(app): 停用插件选项卡
   - cleanup_mod(app): 清理插件资源

4. 可选函数：
   - on_data_update(app, app_data): 实时数据更新
   - on_event(app, event_type, event_data): 事件处理

5. app_data 对象提供的方法：
   - get_all_data(): 获取所有主程序数据
   - send_event(event_type, event_data): 向主程序发送事件

6. 数据格式：
   app_data.get_all_data() 返回的数据包含：
   - playback: 播放状态、时间、BPM等
   - project: 工程文件信息
   - files: 文件路径
   - notes: 音符数据
   - czemakers: CZEmakers属性
   - markers: 标记数据
   - global_commands: 全局命令
   - subtitles: SRT字幕
   - user_stats: 用户统计
   - ui: 界面状态
   - config: 配置信息
   - system: 系统信息
"""