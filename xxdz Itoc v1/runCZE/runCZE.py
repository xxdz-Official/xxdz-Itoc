#!/usr/bin/env python3
"""
runCZE.py - 运行CzeData文件的弹窗播放器
"""

import json
import time
import os
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import sys
import threading
import pygame
import random
import subprocess
import math
import platform  # ：用于检测操作系统版本
from PIL import Image, ImageTk
import re


# ：操作系统检测函数
def get_windows_version():
    """
    检测当前Windows操作系统版本
    返回对应的图标文件夹名称
    """
    if sys.platform != 'win32':
        print(f"非Windows系统: {sys.platform}")
        return "11"  # 默认使用Windows 11图标

    try:
        # 获取Windows版本信息
        version_info = platform.win32_ver()
        version_str = version_info[0]  # 例如 '10', '11' 等

        # 获取Windows版本号
        major_version = int(platform.version().split('.')[0])

        print(f"Windows版本: {version_str}, 主版本号: {major_version}")

        # Windows 11检测 (Windows 11的版本号是10.0.22000或更高)
        if major_version == 10 and int(platform.version().split('.')[2]) >= 22000:
            return "11"
        elif version_str == '11' or '11' in platform.release():
            return "11"
        # Windows 10检测
        elif version_str == '10' or major_version == 10:
            return "10"
        # Windows 8.1/8/7/Vista检测
        elif version_str in ['8.1', '8', '7'] or major_version in [6, 7, 8]:
            return "LogonVista78"
        # Windows XP检测
        elif version_str == 'XP' or major_version == 5:
            return "XP"
        # 比XP更早的系统
        elif major_version < 5:
            return "0~XP"
        else:
            # 未知版本，默认使用Windows 11
            return "11"

    except Exception as e:
        print(f"检测Windows版本失败: {e}")
        return "11"  # 默认使用Windows 11图标


# 导入托盘图标库
try:
    import pystray

    TRAY_AVAILABLE = True
except ImportError:
    print("警告: pystray库未安装，气泡通知在旧版Windows可能失效")
    TRAY_AVAILABLE = False

# 导入Windows系统通知
try:
    from plyer import notification

    NOTIFICATION_AVAILABLE = True
except ImportError:
    print("警告: plyer库未安装，无法使用Windows系统通知")
    NOTIFICATION_AVAILABLE = False

# 导入Windows API
if sys.platform == 'win32':
    import winsound
    import ctypes
    import win32api
    import win32con
    import win32com.client
    import pythoncom

    # 定义键盘虚拟键码常量
    VK_A = 0x41
    VK_B = 0x42
    VK_C = 0x43
    VK_D = 0x44
    VK_E = 0x45
    VK_F = 0x46
    VK_G = 0x47
    VK_H = 0x48
    VK_I = 0x49
    VK_J = 0x4A
    VK_K = 0x4B
    VK_L = 0x4C
    VK_M = 0x4D
    VK_N = 0x4E
    VK_O = 0x4F
    VK_P = 0x50
    VK_Q = 0x51
    VK_R = 0x52
    VK_S = 0x53
    VK_T = 0x54
    VK_U = 0x55
    VK_V = 0x56
    VK_W = 0x57
    VK_X = 0x58
    VK_Y = 0x59
    VK_Z = 0x5A
    VK_0 = 0x30
    VK_1 = 0x31
    VK_2 = 0x32
    VK_3 = 0x33
    VK_4 = 0x34
    VK_5 = 0x35
    VK_6 = 0x36
    VK_7 = 0x37
    VK_8 = 0x38
    VK_9 = 0x39


def set_window_style_only_close(hwnd):
    """仅保留Windows原生窗口的关闭按钮"""
    GWL_STYLE = -16
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000

    try:
        if ctypes.sizeof(ctypes.c_void_p) == 8:
            get_window_long = ctypes.windll.user32.GetWindowLongPtrW
            set_window_long = ctypes.windll.user32.SetWindowLongPtrW
        else:
            get_window_long = ctypes.windll.user32.GetWindowLongW
            set_window_long = ctypes.windll.user32.SetWindowLongW
    except:
        get_window_long = ctypes.windll.user32.GetWindowLongW
        set_window_long = ctypes.windll.user32.SetWindowLongW

    current_style = get_window_long(hwnd, GWL_STYLE)
    new_style = current_style & ~WS_MINIMIZEBOX & ~WS_MAXIMIZEBOX
    set_window_long(hwnd, GWL_STYLE, new_style)
    ctypes.windll.user32.SetWindowPos(
        hwnd, None, 0, 0, 0, 0,
        0x0001 | 0x0002 | 0x0020
    )


class WindowAnimationExecutor:
    """窗口位移动画执行器"""

    def __init__(self, command_executor):
        self.command_executor = command_executor

    def execute_window_animation(self, params):
        """执行窗口位移动画（支持新旧格式）"""
        print(f"执行窗口位移动画: {params}")

        try:
            # 新格式：直接从animations参数中解析动画数据
            # 查找animations参数
            animations_match = re.search(r'animations=(.+)', params)
            if not animations_match:
                print("错误: 未找到动画参数")
                return

            animations_str = animations_match.group(1)

            try:
                animations = json.loads(animations_str)
                print(f"解析到 {len(animations)} 个动画")

                # 检查动画数据是否包含目标信息
                if animations and 'target_type' in animations[0]:
                    print("检测到新格式动画数据（每个动画行独立目标）")
                    self.execute_new_format_animations(animations)
                else:
                    print("检测到旧格式动画数据（统一目标）")
                    self.execute_old_format_animations(params, animations)

            except Exception as e:
                print(f"JSON解析失败: {e}")
                return

        except Exception as e:
            print(f"执行窗口动画失败: {e}")
            import traceback
            traceback.print_exc()

    def execute_new_format_animations(self, animations):
        """执行新格式的动画（每个动画行有独立的目标）"""
        print(f"执行新格式动画，共 {len(animations)} 个动画行")

        # 按目标对动画进行分组
        target_animations = {}

        for anim in animations:
            # 获取目标信息
            target_type = anim.get('target_type', '窗口编组')
            target_name = anim.get('target_name', '')
            target_code = anim.get('target_code', 'group' if target_type == '窗口编组' else 'class')

            if not target_name:
                print(f"警告: 动画缺少目标名称: {anim.get('comment', '未知动画')}")
                continue

            # 创建目标键
            target_key = f"{target_code}:{target_name}"

            if target_key not in target_animations:
                target_animations[target_key] = {
                    'target_code': target_code,
                    'target_name': target_name,
                    'animations': []
                }

            # 添加到对应目标的动画列表
            target_animations[target_key]['animations'].append(anim)

        print(f"按目标分组后得到 {len(target_animations)} 个目标组")

        # 为每个目标组执行动画
        for target_key, target_data in target_animations.items():
            target_code = target_data['target_code']
            target_name = target_data['target_name']
            target_animations_list = target_data['animations']

            print(f"为目标 '{target_name}' ({target_code}) 执行 {len(target_animations_list)} 个动画")
            self.execute_animations_for_target(target_code, target_name, target_animations_list)

    def execute_old_format_animations(self, params, animations):
        """执行旧格式的动画（统一目标）"""
        print("执行旧格式动画（统一目标）")

        # 尝试解析目标参数（旧格式）
        target_match = re.search(r'target=([^:]+):([^:]+)', params)
        if not target_match:
            print("错误: 未找到目标参数")
            return

        target_type = target_match.group(1)  # group或class
        target_name = target_match.group(2)

        print(f"统一目标: {target_type}:{target_name}")

        # 根据目标类型查找窗口
        windows = []
        if target_type == 'group':
            if target_name in self.command_executor.window_groups:
                windows = self.command_executor.window_groups[target_name]
                print(f"找到编组 '{target_name}' 中的 {len(windows)} 个窗口")
            else:
                print(f"警告: 编组 '{target_name}' 不存在")
                return
        elif target_type == 'class':
            if target_name in self.command_executor.window_classes:
                windows = self.command_executor.window_classes[target_name]
                print(f"找到类名 '{target_name}' 对应的 {len(windows)} 个窗口")
            else:
                print(f"警告: 类名 '{target_name}' 不存在")
                return
        else:
            print(f"错误: 未知的目标类型 '{target_type}'")
            return

        if not windows:
            print(f"警告: 未找到目标窗口")
            return

        # 为每个窗口执行动画序列
        for window in windows:
            if window and window.winfo_exists():
                self.execute_animations_for_window(window, animations)

    def execute_animations_for_target(self, target_code, target_name, animations):
        """为指定目标执行动画序列"""
        # 根据目标类型查找窗口
        windows = []
        if target_code == 'group':
            if target_name in self.command_executor.window_groups:
                windows = self.command_executor.window_groups[target_name]
                print(f"✓ 找到编组 '{target_name}' 中的 {len(windows)} 个窗口")
                # 打印所有窗口的标题，确认是否正确
                for i, w in enumerate(windows):
                    try:
                        if w.winfo_exists():
                            title = w.title() if hasattr(w, 'title') else "未知标题"
                            print(f"  窗口 {i + 1}: {title} (存在)")
                        else:
                            print(f"  窗口 {i + 1}: 已销毁")
                    except:
                        print(f"  窗口 {i + 1}: 访问失败")
            else:
                print(f"✗ 警告: 编组 '{target_name}' 不存在")
                # 打印所有已注册的编组，帮助调试
                print(f"当前已注册的编组: {list(self.command_executor.window_groups.keys())}")
                return
        elif target_code == 'class':
            if target_name in self.command_executor.window_classes:
                windows = self.command_executor.window_classes[target_name]
                print(f"找到类名 '{target_name}' 对应的 {len(windows)} 个窗口")
            else:
                print(f"警告: 类名 '{target_name}' 不存在")
                return
        else:
            print(f"错误: 未知的目标类型 '{target_code}'")
            return

        if not windows:
            print(f"警告: 未找到目标窗口")
            return

        # 为每个窗口执行动画序列
        for window in windows:
            if window and window.winfo_exists():
                self.execute_animations_for_window(window, animations)

    def execute_animations_for_window(self, window, animations):
        """为单个窗口执行动画序列"""

        def animation_thread():
            try:
                for anim in animations:
                    self.execute_single_animation(window, anim)
                    # 等待当前动画完成
                    duration = anim.get('duration', 1000)
                    time.sleep(duration / 1000.0)
            except Exception as e:
                print(f"窗口动画执行失败: {e}")

        # 在新线程中执行动画
        threading.Thread(target=animation_thread, daemon=True).start()

    def execute_single_animation(self, window, anim):
        """执行单个动画"""
        try:
            comment = anim.get('comment', '动画')
            position_type = anim.get('position_type', '绝对位置')
            position = anim.get('position', '0,0')
            duration = anim.get('duration', 1000)
            easing = anim.get('easing', 'linear')

            # 支持新的字段名（从JSON生成的格式）
            if 'easing_display' in anim and 'easing' not in anim:
                easing_map = {
                    '线性': 'linear',
                    '缓入': 'ease_in',
                    '缓出': 'ease_out',
                    '缓入缓出': 'ease_in_out'
                }
                easing_display = anim.get('easing_display', '线性')
                easing = easing_map.get(easing_display, 'linear')

            # 支持新的字段名（动画编辑器生成的格式）
            if 'position_x' in anim and 'position_y' in anim and not position:
                position_x = anim.get('position_x', 0)
                position_y = anim.get('position_y', 0)
                position = f"{position_x},{position_y}"

            print(f"执行动画: {comment}, 位置类型: {position_type}, 位置: {position}, "
                  f"持续时间: {duration}ms, 缓动: {easing}")

            # 解析位置
            x_str, y_str = position.split(',')
            target_x = int(x_str.strip())
            target_y = int(y_str.strip())

            # 获取窗口当前位置
            current_x = window.winfo_x()
            current_y = window.winfo_y()

            # 计算目标位置
            if position_type == '绝对位置':
                final_x = target_x
                final_y = target_y
            else:  # 相对位置
                final_x = current_x + target_x
                final_y = current_y + target_y

            # 边界检查
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            window_width = window.winfo_width()
            window_height = window.winfo_height()

            final_x = max(0, min(final_x, screen_width - window_width))
            final_y = max(0, min(final_y, screen_height - window_height))

            # 检查窗口是否还存在
            try:
                if not window.winfo_exists():
                    print(f"窗口已不存在，取消动画: {comment}")
                    return
            except:
                print(f"窗口已销毁，取消动画: {comment}")
                return

            # 执行动画
            self.animate_window_movement(window, current_x, current_y,
                                         final_x, final_y, duration, easing)

        except Exception as e:
            print(f"执行单个动画失败: {e}")

    def animate_window_movement(self, window, start_x, start_y, target_x, target_y, duration, easing):
        """执行窗口移动动画 - 优化版，支持镂空窗口动画标记"""
        steps = max(10, min(60, int(duration / 20)))  # 根据持续时间动态调整步数
        interval = max(10, int(duration / steps))  # 每步间隔时间（毫秒）

        # 检查窗口是否有动画标记
        has_animation_marker = hasattr(window, '_has_animation') and window._has_animation
        if has_animation_marker:
            print(f"窗口有动画标记，窗口移动动画将与其他动画共存")

        def update_position(step):
            if step > steps:
                return  # 动画完成

            # 检查窗口是否还存在
            try:
                if not window.winfo_exists():
                    return
            except:
                return  # 窗口已销毁

            t = step / steps
            eased_t = self.apply_easing(t, easing)

            # 计算当前位置
            current_x = start_x + (target_x - start_x) * eased_t
            current_y = start_y + (target_y - start_y) * eased_t

            # 获取当前窗口大小（对于镂空窗口，保持当前大小）
            try:
                current_width = window.winfo_width()
                current_height = window.winfo_height()
                # 移动窗口，保持当前大小
                if window.winfo_exists():
                    window.geometry(f"{current_width}x{current_height}+{int(current_x)}+{int(current_y)}")
            except:
                # 如果无法获取大小，只移动位置
                try:
                    if window.winfo_exists():
                        window.geometry(f"+{int(current_x)}+{int(current_y)}")
                except:
                    return  # 窗口已被销毁

            # 继续下一步
            if step < steps:
                try:
                    if window.winfo_exists():
                        window.after(interval, lambda: update_position(step + 1))
                except:
                    pass

        # 开始动画
        try:
            if window.winfo_exists():
                window.after(0, lambda: update_position(0))
        except:
            pass  # 窗口已销毁，不启动动画

    def apply_easing(self, t, easing):
        """应用缓动函数"""
        if easing == 'linear':
            return t
        elif easing == 'ease_in':
            return t * t
        elif easing == 'ease_out':
            return 1 - (1 - t) * (1 - t)
        elif easing == 'ease_in_out':
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - math.pow(-2 * t + 2, 2) / 2
        else:
            return t  # 默认线性


class GlobalCommandExecutor:
    """全局命令执行器"""

    def __init__(self, player):
        self.player = player
        self.window_groups = {}
        self.window_classes = {}

        # 窗口动画执行器
        self.animation_executor = WindowAnimationExecutor(self)

        if sys.platform != 'win32':
            print("警告: 非Windows系统，全局命令功能受限")
            return

        # 按键映射表
        self.key_map = {
            'Enter': win32con.VK_RETURN,
            'Escape': win32con.VK_ESCAPE,
            'Tab': win32con.VK_TAB,
            'Space': win32con.VK_SPACE,
            'Backspace': win32con.VK_BACK,
            'Delete': win32con.VK_DELETE,
            'Insert': win32con.VK_INSERT,
            'Home': win32con.VK_HOME,
            'End': win32con.VK_END,
            'PageUp': win32con.VK_PRIOR,
            'PageDown': win32con.VK_NEXT,
            'Up': win32con.VK_UP,
            'Down': win32con.VK_DOWN,
            'Left': win32con.VK_LEFT,
            'Right': win32con.VK_RIGHT,
            'F1': win32con.VK_F1,
            'F2': win32con.VK_F2,
            'F3': win32con.VK_F3,
            'F4': win32con.VK_F4,
            'F5': win32con.VK_F5,
            'F6': win32con.VK_F6,
            'F7': win32con.VK_F7,
            'F8': win32con.VK_F8,
            'F9': win32con.VK_F9,
            'F10': win32con.VK_F10,
            'F11': win32con.VK_F11,
            'F12': win32con.VK_F12,
            'A': VK_A, 'B': VK_B, 'C': VK_C, 'D': VK_D, 'E': VK_E,
            'F': VK_F, 'G': VK_G, 'H': VK_H, 'I': VK_I, 'J': VK_J,
            'K': VK_K, 'L': VK_L, 'M': VK_M, 'N': VK_N, 'O': VK_O,
            'P': VK_P, 'Q': VK_Q, 'R': VK_R, 'S': VK_S, 'T': VK_T,
            'U': VK_U, 'V': VK_V, 'W': VK_W, 'X': VK_X, 'Y': VK_Y,
            'Z': VK_Z,
            '0': VK_0, '1': VK_1, '2': VK_2, '3': VK_3, '4': VK_4,
            '5': VK_5, '6': VK_6, '7': VK_7, '8': VK_8, '9': VK_9,
        }

        # 修饰键映射
        self.modifier_map = {
            'Ctrl': win32con.VK_CONTROL,
            'Control': win32con.VK_CONTROL,
            'Alt': win32con.VK_MENU,
            'Shift': win32con.VK_SHIFT,
            'Windows': win32con.VK_LWIN,
        }

    def register_window_group(self, window, group_name):
        """注册窗口到编组"""
        # 首先检查窗口是否有效
        if not window or not window.winfo_exists():
            print(f"警告: 尝试注册无效窗口到编组 {group_name}")
            return

        print(f"[注册编组] 尝试将窗口 '{window.title()}' 注册到编组 '{group_name}'")

        # 检查编组是否已存在
        if group_name in self.window_groups:
            print(f"[注册编组] 编组 '{group_name}' 已存在，现有 {len(self.window_groups[group_name])} 个窗口")
            # 编组已存在，检查窗口是否已在编组中
            if window not in self.window_groups[group_name]:
                self.window_groups[group_name].append(window)
                print(f"✓ 窗口已注册到现有编组: {group_name} (编组现有 {len(self.window_groups[group_name])} 个窗口)")
                # 打印所有窗口标题，方便调试
                titles = []
                for w in self.window_groups[group_name]:
                    try:
                        if w.winfo_exists():
                            titles.append(w.title() if hasattr(w, 'title') else "未知")
                        else:
                            titles.append("已销毁")
                    except:
                        titles.append("访问失败")
                print(f"  当前编组窗口: {titles}")
            else:
                print(f"窗口已经存在于编组: {group_name}")
        else:
            # 编组不存在，创建新编组
            print(f"[注册编组] 编组 '{group_name}' 不存在，创建新编组")
            self.window_groups[group_name] = [window]
            print(f"创建新编组: {group_name} (首个窗口)")

    def register_window_class(self, window, class_name):
        """注册窗口类名"""
        if class_name not in self.window_classes:
            self.window_classes[class_name] = []

        if window not in self.window_classes[class_name]:
            self.window_classes[class_name].append(window)
            print(f"窗口已注册类名: {class_name}")

    def remove_window(self, window):
        """从所有编组和类名中移除窗口"""
        for group_name, windows in list(self.window_groups.items()):
            if window in windows:
                windows.remove(window)
                print(f"窗口从编组移除: {group_name}")
                if not windows:
                    del self.window_groups[group_name]

        for class_name, windows in list(self.window_classes.items()):
            if window in windows:
                windows.remove(window)
                print(f"窗口从类名移除: {class_name}")
                if not windows:
                    del self.window_classes[class_name]

    def execute_command(self, command_str):
        """执行全局命令"""
        print(f"执行全局命令: {command_str}")

        try:
            if ':' in command_str:
                cmd_type, params = command_str.split(':', 1)
            else:
                cmd_type = command_str
                params = ""

            cmd_type = cmd_type.strip()
            params = params.strip()

            # 根据命令类型执行
            if cmd_type == 'exit_program':
                self.execute_exit_program()
            elif cmd_type == 'close_all_popups':
                self.execute_close_all_popups(params)
            elif cmd_type == 'close_group_popups':
                self.execute_close_group_popups(params)
            elif cmd_type == 'close_class_popups':
                self.execute_close_class_popups(params)
            elif cmd_type == 'show_desktop':
                self.execute_show_desktop()
            elif cmd_type == 'start_menu':
                self.execute_start_menu()
            elif cmd_type == 'mouse_move':
                self.execute_mouse_move(params)
            elif cmd_type == 'simulate_keypress':
                self.execute_simulate_keypress(params)
            elif cmd_type == 'set_wallpaper':
                self.execute_set_wallpaper(params)
            elif cmd_type == 'custom_cmd':
                self.execute_custom_cmd(params)
            elif cmd_type == 'window_animation':  # ：窗口位移动画
                self.animation_executor.execute_window_animation(params)
            else:
                print(f"未知命令类型: {cmd_type}")

        except Exception as e:
            print(f"执行命令失败: {e}")
            import traceback
            traceback.print_exc()

    def execute_exit_program(self):
        """退出程序 - 立即终止"""
        print("执行命令: 退出程序 - 立即终止")
        # 直接调用 player 的 exit_program 方法
        if self.player:
            # 在新线程中执行退出，避免阻塞命令执行
            threading.Thread(target=self.player.exit_program, daemon=True).start()

    def execute_close_all_popups(self, params):
        """关闭所有弹窗（支持动画关闭）"""
        print(f"执行命令: 关闭所有弹窗, 参数: {params}")

        # 设置阻止新窗口标志
        if self.player:
            self.player.prevent_new_windows = True
            print("已设置阻止新窗口创建标志，后续窗口将不再显示")

        sequential = True
        if params:
            for param in params.split(':'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.strip() == 'sequential':
                        sequential = value.strip().lower() in ['true', 'yes', '1', 't']

        popups = []
        if self.player.main_root:
            for window in self.player.main_root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    popups.append(window)

        def close_with_animation(popup):
            """带动画关闭单个窗口"""
            try:
                # 检查窗口是否还存在
                if not popup.winfo_exists():
                    return False

                # 检查是否有动画属性
                if hasattr(popup, '_has_animation') and popup._has_animation:
                    print(f"窗口 {popup.title()} 有动画，播放退出动画")
                    if hasattr(popup, '_play_exit_animation'):
                        popup._play_exit_animation()
                        return True

                # 无动画，直接关闭
                print(f"窗口 {popup.title()} 无动画，直接关闭")
                try:
                    popup.destroy()
                except:
                    pass
                return False
            except Exception as e:
                print(f"关闭窗口时出错: {e}")
                try:
                    popup.destroy()
                except:
                    pass
                return False

        if sequential:
            def close_sequentially():
                for popup in popups:
                    try:
                        has_animation = close_with_animation(popup)
                        if has_animation:
                            # 如果有动画，等待动画完成（动画时长150ms）
                            time.sleep(0.003)
                        else:
                            # 无动画，等待0.4秒
                            time.sleep(0.003)
                    except:
                        pass

                # 清理列表
                self.player.current_windows = []
                # 不清除编组，只清除已销毁的窗口
                for group_name in list(self.window_groups.keys()):
                    self.window_groups[group_name] = [w for w in self.window_groups[group_name]
                                                      if w.winfo_exists()]
                    if not self.window_groups[group_name]:
                        del self.window_groups[group_name]
                # 不清除类名，只清除已销毁的窗口
                for class_name in list(self.window_classes.keys()):
                    self.window_classes[class_name] = [w for w in self.window_classes[class_name]
                                                       if w.winfo_exists()]
                    if not self.window_classes[class_name]:
                        del self.window_classes[class_name]
                print(f"已关闭 {len(popups)} 个弹窗")

            threading.Thread(target=close_sequentially, daemon=True).start()
        else:
            # 同时关闭所有窗口
            for popup in popups:
                close_with_animation(popup)

            self.player.current_windows = []
            self.window_groups.clear()
            self.window_classes.clear()
            print(f"已关闭 {len(popups)} 个弹窗")

    def execute_close_group_popups(self, params):
        """关闭编组内的弹窗"""
        print(f"执行命令: 关闭编组弹窗, 参数: {params}")

        group_name = ""
        sequential = True

        if params:
            for param in params.split(':'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'group':
                        group_name = value
                    elif key == 'sequential':
                        sequential = value.lower() in ['true', 'yes', '1', 't']

        if not group_name:
            print("错误: 未指定编组名称")
            return

        if group_name in self.window_groups:
            popups = self.window_groups[group_name].copy()
            print(f"找到编组 '{group_name}' 中的 {len(popups)} 个窗口")

            def close_group_sequentially():
                closed_count = 0
                for popup in popups:
                    try:
                        if popup.winfo_exists():
                            # 检查是否有动画属性
                            if hasattr(popup, '_has_animation') and popup._has_animation:
                                print(f"窗口 {popup.title()} 有动画，播放退出动画")
                                if hasattr(popup, '_play_exit_animation'):
                                    popup._play_exit_animation()
                                    closed_count += 1
                                    if sequential:
                                        time.sleep(0.4)
                                    continue

                            # 无动画，直接关闭
                            popup.destroy()
                            closed_count += 1
                            print(f"关闭窗口: {popup.title()}")
                            if sequential:
                                time.sleep(0.4)
                    except:
                        pass

                if group_name in self.window_groups:
                    remaining_windows = []
                    for w in self.window_groups[group_name]:
                        try:
                            if hasattr(w, 'winfo_exists') and w.winfo_exists():
                                remaining_windows.append(w)
                        except:
                            pass
                    self.window_groups[group_name] = remaining_windows
                    if not self.window_groups[group_name]:
                        del self.window_groups[group_name]

                remaining_current = []
                for w in self.player.current_windows:
                    try:
                        if hasattr(w, 'winfo_exists') and w.winfo_exists():
                            remaining_current.append(w)
                    except:
                        pass
                self.player.current_windows = remaining_current

                print(f"已关闭编组 '{group_name}' 中的 {closed_count} 个窗口")

            threading.Thread(target=close_group_sequentially, daemon=True).start()
        else:
            print(f"警告: 编组 '{group_name}' 不存在")

    def execute_close_class_popups(self, params):
        """关闭某类名的弹窗"""
        print(f"执行命令: 关闭类名弹窗, 参数: {params}")

        class_name = ""
        sequential = True

        if params:
            for param in params.split(':'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'class':
                        class_name = value
                    elif key == 'sequential':
                        sequential = value.lower() in ['true', 'yes', '1', 't']

        if not class_name:
            print("错误: 未指定类名")
            return

        if class_name in self.window_classes:
            popups = self.window_classes[class_name].copy()
            print(f"找到类名 '{class_name}' 对应的 {len(popups)} 个窗口")

            def close_class_sequentially():
                closed_count = 0
                for popup in popups:
                    try:
                        if popup.winfo_exists():
                            popup.destroy()
                            closed_count += 1
                            print(f"关闭窗口: {popup.title()}")
                            if sequential:
                                time.sleep(0.4)
                    except:
                        pass

                if class_name in self.window_classes:
                    remaining_windows = []
                    for w in self.window_classes[class_name]:
                        try:
                            if hasattr(w, 'winfo_exists') and w.winfo_exists():
                                remaining_windows.append(w)
                        except:
                            pass
                    self.window_classes[class_name] = remaining_windows
                    if not self.window_classes[class_name]:
                        del self.window_classes[class_name]

                remaining_current = []
                for w in self.player.current_windows:
                    try:
                        if hasattr(w, 'winfo_exists') and w.winfo_exists():
                            remaining_current.append(w)
                    except:
                        pass
                self.player.current_windows = remaining_current

                print(f"已关闭类名 '{class_name}' 对应的 {closed_count} 个窗口")

            threading.Thread(target=close_class_sequentially, daemon=True).start()
        else:
            print(f"警告: 类名 '{class_name}' 不存在")

    def execute_start_menu(self):
        """打开开始菜单"""
        print("执行命令: 打开开始菜单")

        if sys.platform == 'win32':
            try:
                pythoncom.CoInitialize()
                try:
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys("^{ESC}")
                    print("已打开开始菜单（方法1：Ctrl+ESC）")
                except Exception as e1:
                    print(f"方法1失败: {e1}")
                    try:
                        ctypes.windll.shell32.ShellExecuteW(None, "open",
                                                            "shell:::{2559a1f3-21d7-11d4-bdaf-00c04f60b9f0}", None,
                                                            None, 1)
                        print("已打开开始菜单（方法2：直接调用开始菜单）")
                    except Exception as e2:
                        print(f"方法2失败: {e2}")
                        try:
                            win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                            time.sleep(0.05)
                            win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
                            print("已打开开始菜单（方法3：模拟Windows键）")
                        except Exception as e3:
                            print(f"方法3失败: {e3}")
                finally:
                    pythoncom.CoUninitialize()

            except Exception as e:
                print(f"所有开始菜单方法都失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("开始菜单功能仅支持Windows系统")

    def smooth_move_mouse(self, start_x, start_y, target_x, target_y, duration=0.5):
        """平滑移动鼠标（缓动效果）"""
        steps = 60
        delay = duration / steps

        for i in range(steps + 1):
            t = i / steps
            if t < 0.5:
                ease_t = 2 * t * t
            else:
                t = t * 2 - 1
                ease_t = 1 - (1 - t) * (1 - t) / 2

            current_x = start_x + (target_x - start_x) * ease_t
            current_y = start_y + (target_y - start_y) * ease_t

            win32api.SetCursorPos((int(current_x), int(current_y)))
            time.sleep(delay)

    def execute_mouse_move(self, params):
        """鼠标移动（带缓动效果）"""
        print(f"执行命令: 鼠标移动, 参数: {params}")

        if sys.platform != 'win32':
            print("鼠标移动功能仅支持Windows系统")
            return

        try:
            if ',' in params:
                x_str, y_str = params.split(',', 1)
                target_x = int(x_str.strip())
                target_y = int(y_str.strip())

                current_x, current_y = win32api.GetCursorPos()

                def move_thread():
                    self.smooth_move_mouse(current_x, current_y, target_x, target_y, 0.5)
                    print(f"鼠标已平滑移动到 ({target_x}, {target_y})")

                threading.Thread(target=move_thread, daemon=True).start()
            else:
                print("错误: 坐标格式应为 'x,y'")
        except Exception as e:
            print(f"鼠标移动失败: {e}")

    def execute_simulate_keypress(self, params):
        """模拟按键"""
        print(f"执行命令: 模拟按键, 参数: {params}")

        if sys.platform != 'win32':
            print("模拟按键功能仅支持Windows系统")
            return

        try:
            keys = params.split('+')
            modifier_keys = []

            for key in keys[:-1]:
                key = key.strip()
                if key in self.modifier_map:
                    vk_code = self.modifier_map[key]
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    modifier_keys.append(vk_code)
                    time.sleep(0.01)

            main_key = keys[-1].strip()
            if main_key in self.key_map:
                vk_code = self.key_map[main_key]
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            else:
                if len(main_key) == 1:
                    ascii_code = ord(main_key.upper())
                    win32api.keybd_event(ascii_code, 0, 0, 0)
                    time.sleep(0.05)
                    win32api.keybd_event(ascii_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    print(f"未知按键: {main_key}")

            time.sleep(0.05)
            for vk_code in modifier_keys:
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

            print(f"已模拟按键: {params}")

        except Exception as e:
            print(f"模拟按键失败: {e}")

    def set_wallpaper_thread(self, actual_path):
        """在独立线程中设置壁纸"""
        try:
            SPI_SETDESKWALLPAPER = 20
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDWININICHANGE = 0x02

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                actual_path,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )

            if result:
                print(f"已设置桌面背景: {actual_path}")
            else:
                print(f"设置桌面背景失败，错误代码: {ctypes.GetLastError()}")
        except Exception as e:
            print(f"设置桌面背景失败: {e}")

    def execute_set_wallpaper(self, params):
        """设置桌面背景（使用相对路径）"""
        print(f"执行命令: 设置桌面背景, 参数: {params}")

        if sys.platform != 'win32':
            print("设置桌面背景功能仅支持Windows系统")
            return

        try:
            # 清理路径：移除可能存在的绝对路径前缀
            img_param = params.strip()
            
            # 如果参数是绝对路径，提取文件名
            if ':' in img_param or img_param.startswith('/') or img_param.startswith('\\'):
                # 可能是绝对路径或 set_wallpaper: 开头的命令
                if img_param.startswith('set_wallpaper:'):
                    # 移除 set_wallpaper: 前缀
                    img_param = img_param[14:].strip()
                
                # 提取文件名
                img_filename = os.path.basename(img_param)
                print(f"从绝对路径提取文件名: {img_filename}")
            else:
                img_filename = img_param
                print(f"使用相对路径文件名: {img_filename}")

            # 在 img 目录下查找文件
            img_dir = os.path.join(os.path.dirname(__file__), "img")
            img_paths = [
                os.path.join(img_dir, img_filename),           # ./img/文件名
                os.path.join(os.getcwd(), "img", img_filename), # 当前目录的img/文件名
                os.path.join(os.getcwd(), img_filename),        # 当前目录
                img_filename,                                   # 直接文件名
                os.path.join(os.path.dirname(__file__), img_filename) # 程序所在目录
            ]

            actual_path = None
            for path in img_paths:
                if os.path.exists(path):
                    actual_path = path
                    print(f"找到图片文件: {path}")
                    break

            if actual_path:
                actual_path = os.path.abspath(actual_path)
                print(f"使用图片文件: {actual_path}")
                threading.Thread(target=self.set_wallpaper_thread, args=(actual_path,), daemon=True).start()
            else:
                print(f"图片文件不存在: {img_filename}")
                print(f"查找路径:")
                for path in img_paths:
                    print(f"  - {path} [{'存在' if os.path.exists(path) else '不存在'}]")

        except Exception as e:
            print(f"设置桌面背景失败: {e}")

    def execute_custom_cmd(self, params):
        """执行自定义CMD命令"""
        print(f"执行命令: 自定义CMD, 参数: {params}")

        try:
            def cmd_thread():
                result = subprocess.run(
                    params,
                    shell=True,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )

                print(f"命令输出: {result.stdout}")
                if result.stderr:
                    print(f"命令错误: {result.stderr}")
                print(f"命令执行完成，返回码: {result.returncode}")

            threading.Thread(target=cmd_thread, daemon=True).start()

        except Exception as e:
            print(f"执行CMD命令失败: {e}")


class CzePlayer:
    def __init__(self):
        self.notes = []
        self.global_commands = []
        self.running = True
        self.screen_width = 1920
        self.screen_height = 1080
        self.window_queue = []
        self.current_windows = []
        self.icon_images = {}
        self.main_root = None
        self.audio_loaded = False
        self.audio_ready = threading.Event()
        self.ui_ready = threading.Event()
        self.start_time = None
        self.audio_started = False
        self.named_windows = {}
        self.windows_default_offset = 40
        self.is_wav = False  # 标记是否为WAV文件
        self.wav_sound = None  # 存储WAV声音对象
        self.running = True  # 程序运行标志
        self.prevent_new_windows = False  # ：阻止新窗口创建标志

        self.command_executor = GlobalCommandExecutor(self)
        self.icon_paths = self.get_icon_paths()
        self.tray_icon = None  # 托盘图标对象

    def get_icon_paths(self):
        """获取图标文件路径"""
        icon_paths = {}
        icon_files = {
            'info': 'xinxi.ico',
            'warning': 'jinggao.ico',
            'error': 'cuowu.ico',
            'question': 'xunwen.ico'
        }

        # ：根据操作系统版本选择图标文件夹
        windows_version = get_windows_version()
        print(f"检测到Windows版本: {windows_version}，使用 {windows_version} 文件夹下的图标")

        # 可能的图标目录路径
        possible_dirs = [
            os.path.join(os.path.dirname(__file__), "ico", windows_version),
            os.path.join(os.path.dirname(__file__), f"ico\\{windows_version}"),
            f"ico/{windows_version}",
            f"./ico/{windows_version}",
            f"ico\\{windows_version}"
        ]

        # 如果找不到对应版本的图标，使用默认的11文件夹
        base_dir = None
        for dir_path in possible_dirs:
            test_file = os.path.join(dir_path, 'xinxi.ico')
            if os.path.exists(test_file):
                base_dir = dir_path
                print(f"找到图标目录: {base_dir}")
                break

        # 如果找不到对应版本的图标，尝试其他备选目录
        if base_dir is None:
            print(f"警告: 找不到 {windows_version} 文件夹下的图标，尝试其他备选目录")
            fallback_dirs = [
                os.path.join(os.path.dirname(__file__), "ico", "11"),
                os.path.join(os.path.dirname(__file__), "ico\\11"),
                "ico/11",
                "./ico/11",
                "ico\\11",
                os.path.join(os.path.dirname(__file__), "ico"),
                "ico",
                "./ico"
            ]

            for dir_path in fallback_dirs:
                test_file = os.path.join(dir_path, 'xinxi.ico')
                if os.path.exists(test_file):
                    base_dir = dir_path
                    print(f"找到备选图标目录: {base_dir}")
                    break

        if base_dir:
            for icon_type, filename in icon_files.items():
                full_path = os.path.join(base_dir, filename)
                if os.path.exists(full_path):
                    icon_paths[icon_type] = full_path
                    print(f"找到图标: {icon_type} -> {full_path}")
                else:
                    # 尝试其他可能的扩展名
                    for ext in ['.ico', '.png', '.jpg']:
                        alt_path = os.path.join(base_dir, filename.replace('.ico', ext))
                        if os.path.exists(alt_path):
                            icon_paths[icon_type] = alt_path
                            print(f"找到替代格式图标: {icon_type} -> {alt_path}")
                            break

        # 如果某些图标没有找到，尝试在ico根目录查找
        for icon_type, filename in icon_files.items():
            if icon_type not in icon_paths:
                root_icon_path = os.path.join(os.path.dirname(__file__), "ico", filename)
                if os.path.exists(root_icon_path):
                    icon_paths[icon_type] = root_icon_path
                    print(f"从ico根目录找到图标: {icon_type} -> {root_icon_path}")

        return icon_paths

    def init_icons(self, root):
        """初始化图标"""
        print("初始化图标...")
        for icon_type, icon_path in self.icon_paths.items():
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                if img.size != (40, 40):
                    img = img.resize((40, 40), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img, master=root)
                self.icon_images[icon_type] = photo
                print(f"成功加载图标: {icon_type}")
            except ImportError:
                try:
                    photo = tk.PhotoImage(file=icon_path, master=root)
                    self.icon_images[icon_type] = photo
                    print(f"使用tkinter加载图标: {icon_type}")
                except Exception as e:
                    print(f"加载图标失败 {icon_type}: {e}")
            except Exception as e:
                print(f"加载图标失败 {icon_type}: {e}")

    def get_screen_resolution(self):
        """获取屏幕分辨率"""
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            self.screen_width = temp_root.winfo_screenwidth()
            self.screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
            print(f"屏幕分辨率: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            print(f"获取屏幕分辨率失败: {e}")
            self.screen_width = 1920
            self.screen_height = 1080

    def load_czedata(self, filepath):
        """加载CzeData文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'notes' in data:
                self.notes = data['notes']

            if 'global_commands' in data:
                self.global_commands = data['global_commands']
                print(f"加载了 {len(self.global_commands)} 个全局命令")
                for i, cmd in enumerate(self.global_commands, 1):
                    print(f"全局命令 {i}: 时间={cmd.get('time_s', 0)}秒, 命令={cmd.get('command', '')}")

            print("=== 音符开始时间列表 ===")
            for i, note in enumerate(self.notes, 1):
                if 'start_s' in note:
                    print(f"音符 {i}: {note['start_s']}秒")
                    if 'cze_makers' in note:
                        window_type = note['cze_makers'].get('window_type', '信息框')
                        pos_type = note['cze_makers'].get('window_position', {}).get('type', '默认')
                        print(f"    弹窗类型: {window_type}")
                        print(f"    弹窗位置类型: {pos_type}")
                        pos = self.calculate_position(note['cze_makers'].get('window_position'))
                        print(f"    弹窗位置: {pos if pos else '默认位置'}")

                        if window_type == '图片框' and 'image_path' in note['cze_makers']:
                            image_path = note['cze_makers']['image_path']
                            filename = os.path.basename(image_path)
                            print(f"    图片文件: {filename}")

                        if 'window_life' in note['cze_makers']:
                            window_life = note['cze_makers']['window_life']
                            if window_life.get('enabled', False):
                                value = window_life.get('value', '1000')
                                unit = window_life.get('unit', 'ms')
                                print(f"    窗口寿命: {value}{unit}")
                        if 'window_class' in note['cze_makers']:
                            window_class = note['cze_makers']['window_class']
                            print(f"    窗口类名: {window_class}")
                        if 'window_group' in note['cze_makers']:
                            window_group = note['cze_makers']['window_group']
                            print(f"    窗口编组: {window_group}")

            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False

    def calculate_position(self, position_info):
        """计算窗口位置"""
        if not position_info or 'type' not in position_info:
            return None

        position_type = position_info['type']

        if position_type == 'screen':
            return self.calculate_screen_position(position_info)
        elif position_type == 'align':
            return self.calculate_align_position(position_info)
        elif position_type == 'link':
            return self.calculate_link_position(position_info)
        elif position_type == 'random':
            return self.calculate_random_position(position_info)
        else:
            print(f"未知的位置类型: {position_type}")
            return None

    def calculate_screen_position(self, position_info):
        """计算屏幕绝对/相对坐标位置"""
        coords = position_info.get('screen_coords', {})
        coord_type = coords.get('coord_type', 'abs')

        try:
            if coord_type == 'abs':
                x_str = coords.get('x_abs', '0')
                y_str = coords.get('y_abs', '0')
                x = int(x_str) if x_str and x_str.strip() != '' else 0
                y = int(y_str) if y_str and y_str.strip() != '' else 0
                print(f"使用绝对坐标: x={x}, y={y}")

            elif coord_type == 'rel':
                x_rel_str = coords.get('x_rel', '0')
                y_rel_str = coords.get('y_rel', '0')
                ref_x_str = coords.get('ref_x', '')
                ref_y_str = coords.get('ref_y', '')

                actual_width = self.screen_width
                actual_height = self.screen_height

                if x_rel_str and x_rel_str.strip() != '':
                    x_rel = float(x_rel_str)
                else:
                    x_rel = 0.0

                if y_rel_str and y_rel_str.strip() != '':
                    y_rel = float(y_rel_str)
                else:
                    y_rel = 0.0

                if ref_x_str and ref_x_str.strip() != '' and ref_y_str and ref_y_str.strip() != '':
                    try:
                        ref_x = float(ref_x_str)
                        ref_y = float(ref_y_str)
                        scale_x = actual_width / ref_x
                        scale_y = actual_height / ref_y

                        x_ref_pixels = (x_rel / 100.0) * ref_x
                        y_ref_pixels = (y_rel / 100.0) * ref_y

                        x = int(x_ref_pixels * scale_x)
                        y = int(y_ref_pixels * scale_y)

                        print(
                            f"相对坐标拉伸: ({x_rel}%, {y_rel}%) -> 参考({ref_x}x{ref_y}) -> 实际({actual_width}x{actual_height})")
                    except ValueError as e:
                        print(f"参考分辨率转换错误，使用直接百分比: {e}")
                        x = int((x_rel / 100.0) * actual_width)
                        y = int((y_rel / 100.0) * actual_height)
                else:
                    x = int((x_rel / 100.0) * actual_width)
                    y = int((y_rel / 100.0) * actual_height)
                    print(f"使用直接百分比: ({x_rel}%, {y_rel}%) -> ({x}, {y})")
            else:
                print(f"未知坐标类型: {coord_type}")
                return None

            window_width = 350
            window_height = 100

            x = max(0, min(x, self.screen_width - window_width))
            y = max(0, min(y, self.screen_height - window_height))

            return (x, y)

        except Exception as e:
            print(f"屏幕坐标计算错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def calculate_align_position(self, position_info):
        """计算屏幕对齐位置"""
        coords = position_info.get('align_coords', {})
        coord_type = coords.get('coord_type', 'abs')
        direction = coords.get('direction', '↖')

        print(f"计算对齐位置: 方向={direction}, 坐标类型={coord_type}")

        window_width = 350
        window_height = 100

        try:
            offset_x = 0
            offset_y = 0

            if coord_type == 'abs':
                x_str = coords.get('x_abs', '0')
                y_str = coords.get('y_abs', '0')
                offset_x = int(x_str) if x_str and x_str.strip() != '' else 0
                offset_y = int(y_str) if y_str and y_str.strip() != '' else 0
                print(f"  绝对偏移: x={offset_x}, y={offset_y}")

            elif coord_type == 'rel':
                x_rel_str = coords.get('x_rel', '0')
                y_rel_str = coords.get('y_rel', '0')
                ref_x_str = coords.get('ref_x', '')
                ref_y_str = coords.get('ref_y', '')

                if ref_x_str and ref_x_str.strip() != '' and ref_y_str and ref_y_str.strip() != '':
                    try:
                        ref_x = float(ref_x_str)
                        ref_y = float(ref_y_str)
                        scale_x = self.screen_width / ref_x
                        scale_y = self.screen_height / ref_y

                        if x_rel_str and x_rel_str.strip() != '':
                            x_rel = float(x_rel_str)
                            x_ref_pixels = x_rel
                            offset_x = int(x_ref_pixels * scale_x)

                        if y_rel_str and y_rel_str.strip() != '':
                            y_rel = float(y_rel_str)
                            y_ref_pixels = y_rel
                            offset_y = int(y_ref_pixels * scale_y)

                        print(
                            f"  相对坐标偏移拉伸: ({x_rel_str}, {y_rel_str})px -> 参考({ref_x}x{ref_y}) -> 实际({self.screen_width}x{self.screen_height})")
                    except ValueError as e:
                        print(f"参考分辨率转换错误，使用屏幕百分比: {e}")
                        if x_rel_str and x_rel_str.strip() != '':
                            offset_x = int(float(x_rel_str))
                        if y_rel_str and y_rel_str.strip() != '':
                            offset_y = int(float(y_rel_str))
                else:
                    if x_rel_str and x_rel_str.strip() != '':
                        offset_x = int(float(x_rel_str))
                    if y_rel_str and y_rel_str.strip() != '':
                        offset_y = int(float(y_rel_str))
                    print(f"  相对偏移(像素): ({offset_x}, {offset_y})")

            if direction == '↖':
                x = offset_x
                y = offset_y
                print(f"  左上角对齐: 偏移({offset_x}, {offset_y}) -> 位置({x}, {y})")
            elif direction == '←':
                x = offset_x
                y = (self.screen_height - window_height) // 2 + offset_y
                print(f"  左居中对齐: 偏移({offset_x}, {offset_y}), 垂直居中调整到({x}, {y})")
            elif direction == '↙':
                x = offset_x
                y = self.screen_height - window_height - offset_y
                print(f"  左下角对齐: 偏移({offset_x}, {offset_y}), 底部调整到({x}, {y})")
            elif direction == '↑':
                x = (self.screen_width - window_width) // 2 + offset_x
                y = offset_y
                print(f"  上居中对齐: 偏移({offset_x}, {offset_y}), 水平居中调整到({x}, {y})")
            elif direction == '→':
                x = self.screen_width - window_width - offset_x
                y = (self.screen_height - window_height) // 2 + offset_y
                print(f"  右居中对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '↗':
                x = self.screen_width - window_width - offset_x
                y = offset_y
                print(f"  右上角对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '↓':
                x = (self.screen_width - window_width) // 2 + offset_x
                y = self.screen_height - window_height - offset_y
                print(f"  下居中对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '↘':
                x = self.screen_width - window_width - offset_x
                y = self.screen_height - window_height - offset_y
                print(f"  右下角对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '↔':
                x = (self.screen_width - window_width) // 2 + offset_x
                y = offset_y
                print(f"  水平居中对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '↕':
                x = offset_x
                y = (self.screen_height - window_height) // 2 + offset_y
                print(f"  垂直居中对齐: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            elif direction == '•':
                x = (self.screen_width - window_width) // 2 + offset_x
                y = (self.screen_height - window_height) // 2 + offset_y
                print(f"  屏幕居中: 偏移({offset_x}, {offset_y}), 位置调整到({x}, {y})")
            else:
                print(f"  未知对齐方向: {direction}，使用屏幕居中")
                x = (self.screen_width - window_width) // 2 + offset_x
                y = (self.screen_height - window_height) // 2 + offset_y

            if direction in ['↖', '←', '↙']:
                x = max(0, x)
                x = min(x, self.screen_width - window_width)
            elif direction in ['↗', '→', '↘']:
                x = max(0, x)
                x = min(x, self.screen_width - window_width)
            else:
                x = max(0, min(x, self.screen_width - window_width))

            if direction in ['↖', '↑', '↗']:
                y = max(0, y)
                y = min(y, self.screen_height - window_height)
            elif direction in ['↙', '↓', '↘']:
                y = max(0, y)
                y = min(y, self.screen_height - window_height)
            else:
                y = max(0, min(y, self.screen_height - window_height))

            print(f"  最终对齐位置(边界保护后): ({x}, {y})")
            return (x, y)

        except Exception as e:
            print(f"对齐坐标计算错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def calculate_random_position(self, position_info):
        """计算随机位置"""
        print("计算随机位置...")

        window_width = 350
        window_height = 100

        max_x = self.screen_width - window_width
        max_y = self.screen_height - window_height

        if max_x <= 0 or max_y <= 0:
            print(f"屏幕太小，无法容纳窗口，使用居中位置")
            x = max(0, (self.screen_width - window_width) // 2)
            y = max(0, (self.screen_height - window_height) // 2)
            return (x, y)

        x = random.randint(0, max_x)
        y = random.randint(0, max_y)

        print(f"随机位置: ({x}, {y}), 屏幕范围: 0-{max_x}x0-{max_y}")

        if position_info and 'random_settings' in position_info:
            settings = position_info['random_settings']

            if 'region' in settings:
                region = settings['region']
                if region == 'top_half':
                    max_y = max_y // 2
                    y = random.randint(0, max_y)
                    print(f"限制在顶部区域: y=0-{max_y}")
                elif region == 'bottom_half':
                    min_y = max_y // 2
                    y = random.randint(min_y, max_y)
                    print(f"限制在底部区域: y={min_y}-{max_y}")
                elif region == 'left_half':
                    max_x = max_x // 2
                    x = random.randint(0, max_x)
                    print(f"限制在左侧区域: x=0-{max_x}")
                elif region == 'right_half':
                    min_x = max_x // 2
                    x = random.randint(min_x, max_x)
                    print(f"限制在右侧区域: x={min_x}-{max_x}")
                elif region == 'center_region':
                    center_min_x = max_x // 3
                    center_max_x = max_x * 2 // 3
                    center_min_y = max_y // 3
                    center_max_y = max_y * 2 // 3
                    x = random.randint(center_min_x, center_max_x)
                    y = random.randint(center_min_y, center_max_y)
                    print(f"限制在中心区域: x={center_min_x}-{center_max_x}, y={center_min_y}-{center_max_y}")

            if 'avoid_edges' in settings and settings['avoid_edges']:
                edge_margin = settings.get('edge_margin', 50)
                x = random.randint(edge_margin, max_x - edge_margin)
                y = random.randint(edge_margin, max_y - edge_margin)
                print(
                    f"避开边缘{edge_margin}像素: x={edge_margin}-{max_x - edge_margin}, y={edge_margin}-{max_y - edge_margin}")

        return (x, y)

    def calculate_aligned_position_with_actual_size(self, position_info, actual_width, actual_height):
        """根据实际窗口尺寸重新计算对齐位置"""
        coords = position_info.get('align_coords', {})
        coord_type = coords.get('coord_type', 'abs')
        direction = coords.get('direction', '↖')

        offset_x = 0
        offset_y = 0

        if coord_type == 'abs':
            x_str = coords.get('x_abs', '0')
            y_str = coords.get('y_abs', '0')
            offset_x = int(x_str) if x_str and x_str.strip() != '' else 0
            offset_y = int(y_str) if y_str and y_str.strip() != '' else 0

        elif coord_type == 'rel':
            x_rel_str = coords.get('x_rel', '0')
            y_rel_str = coords.get('y_rel', '0')
            ref_x_str = coords.get('ref_x', '')
            ref_y_str = coords.get('ref_y', '')

            if ref_x_str and ref_x_str.strip() != '' and ref_y_str and ref_y_str.strip() != '':
                try:
                    ref_x = float(ref_x_str)
                    ref_y = float(ref_y_str)
                    scale_x = self.screen_width / ref_x
                    scale_y = self.screen_height / ref_y

                    if x_rel_str and x_rel_str.strip() != '':
                        x_rel = float(x_rel_str)
                        offset_x = int(x_rel * scale_x)

                    if y_rel_str and y_rel_str.strip() != '':
                        y_rel = float(y_rel_str)
                        offset_y = int(y_rel * scale_y)

                except ValueError:
                    if x_rel_str and x_rel_str.strip() != '':
                        offset_x = int(float(x_rel_str))
                    if y_rel_str and y_rel_str.strip() != '':
                        offset_y = int(float(y_rel_str))
            else:
                if x_rel_str and x_rel_str.strip() != '':
                    offset_x = int(float(x_rel_str))
                if y_rel_str and y_rel_str.strip() != '':
                    offset_y = int(float(y_rel_str))

        # 注意：这里的偏移量含义是窗口的对应角距离屏幕对应角的距离
        # 例如：↙ 方向，offset_y 是窗口左下角距离屏幕左下角的距离（向上为正）

        if direction == '↖':
            # 窗口左上角距离屏幕左上角 (offset_x, offset_y)
            x = offset_x
            y = offset_y
        elif direction == '←':
            # 窗口左边中点距离屏幕左边中点 (offset_x, offset_y)
            x = offset_x
            y = (self.screen_height - actual_height) // 2 + offset_y
        elif direction == '↙':
            # 窗口左下角距离屏幕左下角 (offset_x, offset_y)
            # offset_y 是向上偏移量，所以窗口的 y 坐标 = 屏幕高度 - 窗口高度 - offset_y
            x = offset_x
            y = self.screen_height - actual_height - offset_y
            print(f"  左下角对齐: 窗口左下角距离屏幕左下角 ({offset_x}, {offset_y}) -> 窗口左上角位置 ({x}, {y})")
        elif direction == '↑':
            # 窗口上边中点距离屏幕上边中点 (offset_x, offset_y)
            x = (self.screen_width - actual_width) // 2 + offset_x
            y = offset_y
        elif direction == '→':
            # 窗口右边中点距离屏幕右边中点 (offset_x, offset_y)
            x = self.screen_width - actual_width - offset_x
            y = (self.screen_height - actual_height) // 2 + offset_y
        elif direction == '↗':
            # 窗口右上角距离屏幕右上角 (offset_x, offset_y)
            # offset_x 是向左偏移量，所以窗口的 x 坐标 = 屏幕宽度 - 窗口宽度 - offset_x
            x = self.screen_width - actual_width - offset_x
            y = offset_y
            print(f"  右上角对齐: 窗口右上角距离屏幕右上角 ({offset_x}, {offset_y}) -> 窗口左上角位置 ({x}, {y})")
        elif direction == '↓':
            # 窗口下边中点距离屏幕下边中点 (offset_x, offset_y)
            x = (self.screen_width - actual_width) // 2 + offset_x
            y = self.screen_height - actual_height - offset_y
        elif direction == '↘':
            # 窗口右下角距离屏幕右下角 (offset_x, offset_y)
            # offset_x 是向左偏移量，offset_y 是向上偏移量
            x = self.screen_width - actual_width - offset_x
            y = self.screen_height - actual_height - offset_y
            print(f"  右下角对齐: 窗口右下角距离屏幕右下角 ({offset_x}, {offset_y}) -> 窗口左上角位置 ({x}, {y})")
        elif direction == '↔':
            # 水平居中，垂直方向按偏移
            x = (self.screen_width - actual_width) // 2 + offset_x
            y = offset_y
        elif direction == '↕':
            # 垂直居中，水平方向按偏移
            x = offset_x
            y = (self.screen_height - actual_height) // 2 + offset_y
        elif direction == '•':
            # 完全居中
            x = (self.screen_width - actual_width) // 2 + offset_x
            y = (self.screen_height - actual_height) // 2 + offset_y
        else:
            # 默认居中
            x = (self.screen_width - actual_width) // 2 + offset_x
            y = (self.screen_height - actual_height) // 2 + offset_y

        # 确保窗口在屏幕范围内
        x = max(0, min(x, self.screen_width - actual_width))
        y = max(0, min(y, self.screen_height - actual_height))

        print(f"  根据实际尺寸重新计算位置: ({x}, {y}), 实际尺寸: {actual_width}x{actual_height}")
        return (x, y)

    def calculate_link_position(self, position_info):
        """计算链接窗口位置"""
        link_info = position_info.get('link_window', {})
        window_name = link_info.get('window_name', '')
        link_type = link_info.get('link_type', 'sys')
        direction = link_info.get('direction', '↘')

        print(f"计算链式链接位置: 目标窗口={window_name}, 链接类型={link_type}, 方向={direction}")

        if window_name not in self.named_windows:
            print(f"  警告: 目标窗口 '{window_name}' 不存在，使用默认居中位置")
            return None

        target_window = self.named_windows[window_name]
        if not target_window or not target_window.winfo_exists():
            print(f"  警告: 目标窗口 '{window_name}' 已销毁，使用默认居中位置")
            return None

        try:
            base_window = None
            offset_count = 0

            link_chain_prefix = f"link_to_{window_name}_"
            for name, win in list(self.named_windows.items()):
                if name.startswith(link_chain_prefix):
                    try:
                        chain_num = int(name.replace(link_chain_prefix, "").split('_')[0])
                        if chain_num > offset_count:
                            offset_count = chain_num
                            base_window = win
                            print(f"  找到链中的窗口 {name}, 序号: {chain_num}")
                    except:
                        pass

            if base_window is None:
                base_window = target_window
                print(f"  使用原始目标窗口作为基准")
            else:
                print(f"  使用链中最后一个窗口作为基准 (序号: {offset_count})")

            base_x = base_window.winfo_x()
            base_y = base_window.winfo_y()
            base_width = base_window.winfo_width()
            base_height = base_window.winfo_height()

            print(f"  基准窗口位置: ({base_x}, {base_y}), 尺寸: {base_width}x{base_height}")

            window_width = 350
            window_height = 100

            offset_x = 0
            offset_y = 0

            if link_type == 'sys':
                offset_x = self.windows_default_offset
                offset_y = self.windows_default_offset
                print(f"  使用系统默认距离: ({offset_x}, {offset_y})像素")

            elif link_type == 'add':
                add_value_str = link_info.get('add_value', '20')
                add_unit = link_info.get('add_unit', 'px')

                try:
                    add_value = float(add_value_str)

                    if add_unit == 'px':
                        offset_value = int(add_value)
                    elif add_unit == 'rpx':
                        ref_x_str = link_info.get('ref_x', '')
                        ref_y_str = link_info.get('ref_y', '')

                        if ref_x_str and ref_x_str.strip() != '' and ref_y_str and ref_y_str.strip() != '':
                            try:
                                ref_x = float(ref_x_str)
                                ref_y = float(ref_y_str)
                                scale_x = self.screen_width / ref_x
                                scale_y = self.screen_height / ref_y
                                scale = min(scale_x, scale_y)
                                offset_value = int(add_value * scale)
                                print(f"  rpx拉伸: {add_value}rpx -> {offset_value}px (比例={scale:.3f})")
                            except:
                                offset_value = int(add_value)
                                print(f"  rpx转换失败，使用原始值: {offset_value}px")
                        else:
                            offset_value = int(add_value)
                            print(f"  无参考分辨率，使用原始值: {offset_value}px")
                    else:
                        offset_value = int(add_value)
                        print(f"  未知单位'{add_unit}'，使用像素值: {offset_value}px")

                    offset_x = offset_value
                    offset_y = offset_value
                    print(f"  使用自定义偏移量: ({offset_x}, {offset_y})像素")

                except ValueError as e:
                    print(f"  偏移量转换错误: {e}，使用系统默认距离{self.windows_default_offset}像素")
                    offset_x = self.windows_default_offset
                    offset_y = self.windows_default_offset

            direction_multipliers = {
                '↘': (1, 1), '↖': (-1, -1), '←': (-1, 0), '↙': (-1, 1),
                '↑': (0, -1), '→': (1, 0), '↗': (1, -1), '↓': (0, 1), '•': (1, 1)
            }

            mult_x, mult_y = direction_multipliers.get(direction, (1, 1))
            offset_x *= mult_x
            offset_y *= mult_y

            print(f"  方向 '{direction}' 应用乘数: ({mult_x}, {mult_y})")
            print(f"  调整后的偏移量: ({offset_x}, {offset_y})")

            x = base_x + offset_x
            y = base_y + offset_y

            print(f"  原始计算位置: ({x}, {y})")

            x = max(0, min(x, self.screen_width - window_width))
            y = max(0, min(y, self.screen_height - window_height))

            print(f"  最终位置(边界保护后): ({x}, {y})")

            return (x, y)

        except Exception as e:
            print(f"链接位置计算错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def play_system_sound(self, window_type):
        """播放系统提示音"""
        if sys.platform != 'win32':
            return

        try:
            sound_constants = {
                '信息框': winsound.MB_ICONASTERISK,
                '警告框': winsound.MB_ICONEXCLAMATION,
                '错误框': winsound.MB_ICONHAND,
                '询问框': winsound.MB_ICONQUESTION,
                '图片框': winsound.MB_ICONASTERISK,
                '气泡/通知': winsound.MB_ICONASTERISK
            }

            system_aliases = {
                '信息框': "SystemAsterisk",
                '警告框': "SystemExclamation",
                '错误框': "SystemHand",
                '询问框': "SystemQuestion",
                '图片框': "SystemAsterisk",
                '气泡/通知': "SystemNotification"
            }

            sound_alias = system_aliases.get(window_type, "SystemAsterisk")
            sound_type = sound_constants.get(window_type, winsound.MB_ICONASTERISK)

            try:
                winsound.PlaySound(sound_alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
                print(f"播放系统音效: {window_type} -> {sound_alias}")
            except Exception as play_error:
                print(f"PlaySound播放失败，尝试MessageBeep: {play_error}")
                try:
                    winsound.MessageBeep(sound_type)
                    print(f"使用MessageBeep播放音效: {window_type}")
                except Exception as beep_error:
                    print(f"MessageBeep播放失败: {beep_error}")
                    try:
                        beep_freqs = {
                            '信息框': 1000,
                            '警告框': 800,
                            '错误框': 600,
                            '询问框': 1200,
                            '图片框': 1000,
                            '气泡/通知': 1000
                        }
                        frequency = beep_freqs.get(window_type, 1000)
                        winsound.Beep(frequency, 200)
                        print(f"使用备选蜂鸣音效: {window_type} ({frequency}Hz)")
                    except Exception as beep_fail:
                        print(f"所有音效播放方法均失败: {beep_fail}")

        except Exception as e:
            print(f"音效播放失败: {e}")

    def pre_calculate_window_size(self, content):
        """预计算窗口高度"""
        lines = content.split('\n')
        total_lines = 0
        for line in lines:
            estimated_lines = len(line) // 30 + 1
            total_lines += estimated_lines

        content_height = max(total_lines * 20, 60)
        total_height = content_height + 45 + 20

        return total_height

    def get_window_life_time(self, note):
        """获取窗口寿命时间"""
        if 'cze_makers' not in note:
            return None

        cze = note['cze_makers']
        if 'window_life' not in cze:
            return None

        window_life = cze['window_life']
        if not window_life.get('enabled', False):
            return None

        try:
            value_str = window_life.get('value', '1000')
            unit = window_life.get('unit', 'ms')

            value = float(value_str)

            if unit == 'ms':
                return value
            elif unit == 's':
                return value * 1000
            elif unit == 'min':
                return value * 1000 * 60
            else:
                print(f"未知的时间单位: {unit}，使用毫秒")
                return value
        except Exception as e:
            print(f"解析窗口寿命失败: {e}")
            return None

    def find_image_file(self, image_path):
        """查找图片文件（统一处理绝对路径和相对路径）"""
        # 如果直接存在，返回
        if os.path.exists(image_path):
            print(f"图片文件直接存在: {image_path}")
            return image_path

        # 提取文件名
        filename = os.path.basename(image_path)
        print(f"提取文件名: {filename}")

        # 可能的查找路径
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "img", filename),  # ./img/文件名
            os.path.join(os.getcwd(), "img", filename),                 # 当前目录的img/文件名
            os.path.join(os.path.dirname(__file__), filename),          # 程序所在目录
            os.path.join(os.getcwd(), filename),                        # 当前目录
            filename                                                     # 直接文件名
        ]

        # 添加去重后的路径
        unique_paths = []
        seen = set()
        for path in possible_paths:
            norm_path = os.path.normpath(path)
            if norm_path not in seen:
                seen.add(norm_path)
                unique_paths.append(path)

        for path in unique_paths:
            if os.path.exists(path):
                print(f"找到图片文件: {path}")
                return path

        print(f"警告: 图片文件未找到: {filename}")
        print(f"查找路径:")
        for path in unique_paths:
            print(f"  - {path} [{'存在' if os.path.exists(path) else '不存在'}]")
        return None

    def create_window_now(self, note):
        """创建弹窗窗口"""
        if 'cze_makers' not in note:
            return

        cze = note['cze_makers']
        title = cze.get('window_title', '信息框')
        content = cze.get('window_content', '')
        window_type = cze.get('window_type', '信息框')
        window_group = cze.get('window_group', '')
        window_life_ms = self.get_window_life_time(note)
        window_class = cze.get('window_class', '')

        is_link_window = False
        link_target = None
        if 'window_position' in cze and cze['window_position'].get('type') == 'link':
            is_link_window = True
            link_target = cze['window_position'].get('link_window', {}).get('window_name', '')
            print(f"这是一个链接窗口，链接到: {link_target}")

        self.play_system_sound(window_type)

        try:
            if window_type == '气泡/通知':
                self.create_windows_notification(cze, window_life_ms, window_class)
                return

            popup = tk.Toplevel(self.main_root)
            popup.withdraw()
            popup.resizable(False, False)

            if sys.platform == 'win32':
                try:
                    import ctypes
                    myappid = 'CzePlayer.RunCZE.1.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                except:
                    pass

            style = ttk.Style()
            try:
                if sys.platform == 'win32':
                    style.theme_use('vista')
            except:
                style.theme_use('clam')

            if window_type == '图片框':
                # 先创建窗口但不显示，获取实际尺寸后再计算位置
                # 但 create_image_window 会立即显示窗口，所以需要特殊处理

                # 方法1：先调用 create_image_window 但不显示（需要修改 create_image_window）
                # 但为了最小化修改，我们采用方法2：在 create_image_window 中重新计算位置

                # 这里我们传递 None 作为位置，让 create_image_window 自己计算
                # 但需要修改 create_image_window 来支持位置计算

                # 为了兼容现有代码，我们传递原始位置，但在 create_image_window 中重新计算
                # 这需要修改 create_image_window

                # 临时解决方案：延迟创建图片框，先获取窗口尺寸
                # 但为了不破坏现有结构，我们采用最直接的方案：
                # 在 create_image_window 中，如果位置是 None 或需要重新计算，就自己计算

                # 计算初始位置（使用默认窗口尺寸）
                position = None
                if 'window_position' in cze:
                    position_info = cze['window_position']
                    # 使用默认窗口尺寸计算临时位置
                    pos = self.calculate_position(position_info)
                    if pos:
                        position = pos
                        print(f"图片框临时计算出的位置: {position}")
                    else:
                        print("图片框位置计算失败，将使用默认居中")

                # 创建图片框，传递位置参数
                # 在 create_image_window 内部，我们会根据实际尺寸重新计算位置
                success = self.create_image_window(popup, cze, title, window_life_ms, window_class, window_group,
                                                   position)
                if not success:
                    popup.destroy()
                    return

                # 获取实际尺寸后重新计算位置
                popup.update_idletasks()
                actual_width = popup.winfo_width()
                actual_height = popup.winfo_height()

                # 如果是对齐位置，重新计算
                if 'window_position' in cze and cze['window_position'].get('type') == 'align':
                    position_info = cze['window_position']
                    screen_x, screen_y = self.calculate_aligned_position_with_actual_size(
                        position_info, actual_width, actual_height)
                    position = (screen_x, screen_y)
                    print(f"图片框对齐位置重新计算（使用实际尺寸）: {position}")

                    # 重新设置窗口位置
                    x, y = position
                    popup.geometry(f"{actual_width}x{actual_height}+{x}+{y}")
                    print(f"弹窗位置已更新: ({x}, {y})")
            else:
                popup.title(title)
                self.create_regular_window(popup, cze, content, window_type, window_life_ms, window_class, window_group)

            if window_life_ms:
                original_title = popup.title()
                popup.title(f"{original_title} (自动关闭: {window_life_ms}ms)")

            popup.update_idletasks()
            actual_width = popup.winfo_width()
            actual_height = popup.winfo_height()

            print(f"窗口实际尺寸（隐藏状态下）: {actual_width}x{actual_height}")

            # 设置窗口图标
            if sys.platform == 'win32':
                try:
                    icon_path = os.path.join("ico", "zhanwei.ico")
                    if os.path.exists(icon_path):
                        popup.iconbitmap(icon_path)
                        print(f"已设置窗口图标: {icon_path}")
                    else:
                        print(f"图标文件未找到: {icon_path}")
                except Exception as e:
                    print(f"设置窗口图标失败: {e}")
            else:
                print("非Windows系统，跳过图标设置")

            position = None
            if 'window_position' in cze:
                position_info = cze['window_position']

                if position_info.get('type') == 'random':
                    print(f"计算随机位置（使用实际尺寸）: {actual_width}x{actual_height}")

                    max_x = self.screen_width - actual_width
                    max_y = self.screen_height - actual_height

                    if max_x <= 0 or max_y <= 0:
                        print(f"屏幕太小，无法容纳窗口，使用居中位置")
                        x = max(0, (self.screen_width - actual_width) // 2)
                        y = max(0, (self.screen_height - actual_height) // 2)
                    else:
                        x = random.randint(0, max_x)
                        y = random.randint(0, max_y)

                    position = (x, y)
                    print(f"随机位置重新计算: {position}")

                elif position_info.get('type') == 'align':
                    screen_x, screen_y = self.calculate_aligned_position_with_actual_size(
                        position_info, actual_width, actual_height)
                    position = (screen_x, screen_y)
                    print(f"对齐位置重新计算（使用实际尺寸）: {position}")
                else:
                    position = self.calculate_position(position_info)
                    if position:
                        x, y = position
                        x = max(0, min(x, self.screen_width - actual_width))
                        y = max(0, min(y, self.screen_height - actual_height))
                        position = (x, y)
                        print(f"其他位置类型（使用实际尺寸边界保护）: {position}")
            else:
                print(f"未指定位置，使用居中显示")

            if position:
                x, y = position
                popup.geometry(f"{actual_width}x{actual_height}+{x}+{y}")
                print(f"弹窗位置已设置（隐藏中）: ({x}, {y}), 实际尺寸: {actual_width}x{actual_height}")
            else:
                x = (self.screen_width // 2) - (actual_width // 2)
                y = (self.screen_height // 2) - (actual_height // 2)
                popup.geometry(f"{actual_width}x{actual_height}+{x}+{y}")
                print(f"弹窗居中位置已设置（隐藏中）: ({x}, {y}), 实际尺寸: {actual_width}x{actual_height}")

            if sys.platform == 'win32':
                try:
                    hwnd = ctypes.windll.user32.GetParent(popup.winfo_id())
                    if hwnd == 0:
                        hwnd = popup.winfo_id()

                    print(f"窗口句柄（隐藏中）: {hwnd}")
                    set_window_style_only_close(hwnd)
                    print("窗口样式已修改（隐藏中）：仅保留关闭按钮")
                except Exception as e:
                    print(f"修改窗口样式失败: {e}")
                    import traceback
                    traceback.print_exc()

            if window_life_ms:
                print(f"窗口寿命: {window_life_ms}毫秒")
            if window_class:
                print(f"窗口类名: {window_class}")
            if window_group:
                print(f"窗口编组: {window_group}")

            popup.deiconify()
            popup.lift()
            popup.focus_force()

            try:
                for child in popup.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Frame):
                                for widget in subchild.winfo_children():
                                    if isinstance(widget, ttk.Button):
                                        widget.focus_set()
                                        break
            except:
                pass

            if window_class:
                self.command_executor.register_window_class(popup, window_class)
            if window_group:
                # 延迟一点注册，确保窗口完全创建
                def delayed_register():
                    if popup.winfo_exists():
                        self.command_executor.register_window_group(popup, window_group)

                popup.after(50, delayed_register)

            if window_life_ms:
                def auto_close():
                    try:
                        print(f"窗口寿命到期，自动关闭窗口: {popup.title()}")

                        # 检查窗口是否还存在
                        if not popup.winfo_exists():
                            return

                        # 检查是否有动画属性（由 create_image_window 设置）
                        if hasattr(popup, '_has_animation') and popup._has_animation:
                            # 有动画，播放退出动画
                            print("自动关闭播放退出动画")
                            if hasattr(popup, '_play_exit_animation'):
                                popup._play_exit_animation()
                                return

                        # 无动画，直接关闭
                        if window_class and window_class in self.named_windows:
                            del self.named_windows[window_class]
                            print(f"从命名窗口字典中移除: {window_class}")
                        if is_link_window and link_target:
                            link_chain_prefix = f"link_to_{link_target}_"
                            for name in list(self.named_windows.keys()):
                                if name.startswith(link_chain_prefix) and self.named_windows[name] == popup:
                                    del self.named_windows[name]
                                    print(f"从命名窗口字典中移除链式类名: {name}")
                                    break

                        self.command_executor.remove_window(popup)

                        try:
                            popup.destroy()
                        except:
                            pass
                    except Exception as e:
                        print(f"自动关闭窗口时出错: {e}")

                close_after_ms = int(window_life_ms)
                popup.after(close_after_ms, auto_close)

            self.current_windows.append(popup)

            if window_class:
                self.named_windows[window_class] = popup
                print(f"窗口已注册类名: {window_class}")

            if is_link_window and link_target:
                link_chain_prefix = f"link_to_{link_target}_"
                chain_count = 0
                chain_names = []
                for name in list(self.named_windows.keys()):
                    if name.startswith(link_chain_prefix):
                        chain_count += 1
                        chain_names.append(name)

                print(f"当前链接链窗口: {chain_names}")

                new_chain_count = chain_count + 1
                link_chain_name = f"{link_chain_prefix}{new_chain_count}"
                self.named_windows[link_chain_name] = popup
                print(f"链接窗口注册链式类名: {link_chain_name} (链中序号: {new_chain_count})")

        except Exception as e:
            print(f"创建窗口失败: {e}")
            import traceback
            traceback.print_exc()

    def create_regular_window(self, popup, cze, content, window_type, window_life_ms, window_class, window_group):
        """创建常规弹窗窗口"""
        CONTENT_BG = 'white'
        BUTTON_BG = '#F0F0F0' if sys.platform == 'win32' else '#F5F5F5'

        main_frame = tk.Frame(popup, bg=CONTENT_BG)
        main_frame.pack(fill='both', expand=True)

        content_frame = tk.Frame(main_frame, bg=CONTENT_BG)
        content_frame.pack(fill='both', expand=True, padx=15, pady=15)
        content_frame.pack_propagate(True)
        content_frame.grid_columnconfigure(1, weight=1)

        icon_frame = tk.Frame(content_frame, bg=CONTENT_BG)
        icon_frame.grid(row=0, column=0, padx=(0, 12), sticky='nw')

        icon_mapping = {
            '信息框': 'info',
            '警告框': 'warning',
            '错误框': 'error',
            '询问框': 'question'
        }
        icon_type = icon_mapping.get(window_type, 'info')

        if icon_type in self.icon_images:
            icon_label = tk.Label(icon_frame, image=self.icon_images[icon_type], bg=CONTENT_BG)
            icon_label.pack()
            print(f"显示真实图标: {icon_type}")
        else:
            char_mapping = {
                'info': "ℹ",
                'warning': "⚠",
                'error': "⛔",
                'question': "?"
            }
            color_mapping = {
                'info': '#0078D7',
                'warning': '#FF9900',
                'error': '#D13438',
                'question': '#0078D7'
            }
            icon_char = char_mapping.get(icon_type, "ℹ")
            icon_color = color_mapping.get(icon_type, '#0078D7')
            icon_label = tk.Label(icon_frame, text=icon_char, font=('Segoe UI Symbol', 20),
                                  fg=icon_color, bg=CONTENT_BG)
            icon_label.pack()
            print(f"使用字符图标: {icon_type}")

        text_label = tk.Label(content_frame, text=content,
                              font=('Segoe UI', 9) if sys.platform == 'win32' else ('Arial', 9),
                              wraplength=220, justify='left', bg=CONTENT_BG)
        text_label.grid(row=0, column=1, sticky='w')

        button_frame = tk.Frame(main_frame, bg=BUTTON_BG, height=45)
        button_frame.pack(fill='x', side='bottom')
        button_frame.pack_propagate(False)

        btn_container = tk.Frame(button_frame, bg=BUTTON_BG)
        btn_container.pack(side='right', padx=15, pady=10)

        def close_window():
            if window_class and window_class in self.named_windows:
                del self.named_windows[window_class]
                print(f"从命名窗口字典中移除: {window_class}")
            self.command_executor.remove_window(popup)
            popup.destroy()

        btn = ttk.Button(btn_container, text="确定", width=10, command=close_window)
        btn.pack()

        popup.bind('<Return>', lambda e: close_window())
        popup.bind('<Escape>', lambda e: close_window())

    def create_image_window(self, popup, cze, title, window_life_ms, window_class, window_group, position=None):
        """创建图片框窗口（支持完全镂空透明效果，无窗口边框）"""
        # 获取镂空设置
        hollow_enabled = cze.get('hollow_enabled', False)

        if hollow_enabled:
            # 镂空模式：无标题栏、无边框、置顶
            popup.title('')
            popup.overrideredirect(True)
            popup.attributes('-topmost', True)
            print("镂空模式: 使用无边框窗口")
        else:
            # 普通模式：有标题栏和边框
            popup.title(title)
            # 保留窗口装饰（有标题栏、有关闭按钮）
            popup.overrideredirect(False)
            # 可选：设置窗口置顶（如果需要）
            # popup.attributes('-topmost', True)
            print("普通模式: 使用标准窗口")

        image_path = cze.get('image_path', '')
        size_option = cze.get('size_option', 'image_size')
        custom_width = cze.get('custom_width', 400)
        custom_height = cze.get('custom_height', 300)

        # 镂空相关字段 - 现在默认禁用
        hollow_enabled = cze.get('hollow_enabled', False)  # 默认为False，不启用镂空
        hollow_animation = cze.get('hollow_animation', False)
        hollow_color = cze.get('hollow_color', '#FFFFFF')

        # 普通图片框的动画选项（非镂空）
        normal_animation = cze.get('normal_animation', False)  # 普通图片框的动画

        print(f"创建图片框窗口: {title}")
        print(f"图片路径: {image_path}")
        print(f"尺寸选项: {size_option}")
        if size_option == 'custom_size':
            print(f"自定义尺寸: {custom_width}x{custom_height}")

        # 区分显示模式
        if hollow_enabled:
            print(f" 镂空模式: 启用，镂空颜色: {hollow_color}")
            if hollow_animation:
                print(f"  镂空动画: 启用")
        else:
            print(f"普通模式: 不镂空")
            if normal_animation:
                print(f"  普通动画: 启用")

        actual_image_path = self.find_image_file(image_path)

        if not actual_image_path:
            error_frame = tk.Frame(popup, bg='white')
            error_frame.pack(fill='both', expand=True, padx=20, pady=20)

            error_label = tk.Label(error_frame, text=f"图片文件未找到:\n{os.path.basename(image_path)}",
                                   font=('Segoe UI', 10), fg='red', bg='white')
            error_label.pack(expand=True)

            def close_on_right_click(event):
                if window_class and window_class in self.named_windows:
                    del self.named_windows[window_class]
                self.command_executor.remove_window(popup)
                popup.destroy()

            error_label.bind('<Button-3>', close_on_right_click)
            error_frame.bind('<Button-3>', close_on_right_click)

            return True

        try:
            # 设置窗口背景
            if hollow_enabled:
                # 镂空模式：设置透明背景
                if sys.platform == 'win32':
                    try:
                        popup.configure(bg='black')
                        popup.wm_attributes('-transparentcolor', 'black')
                        print("镂空模式: Windows 透明窗口设置成功")
                    except Exception as e:
                        print(f"镂空模式: Windows 透明窗口设置失败: {e}")
                        popup.configure(bg='white')
                else:
                    try:
                        popup.wm_attributes('-alpha', 0.95)
                        popup.configure(bg='white')
                    except:
                        popup.configure(bg='white')
            else:
                # 普通模式：使用白色背景
                popup.configure(bg='white')
                print("普通模式: 使用白色背景")

            # 加载图片
            img = Image.open(actual_image_path)

            print(f"原始图片模式: {img.mode}, 尺寸: {img.size}")

            # 处理镂空效果（仅在启用时执行）
            if hollow_enabled:
                # 转换颜色格式：从"#FFFFFF"到RGB元组
                if hollow_color.startswith('#'):
                    hollow_color_rgb = tuple(int(hollow_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                else:
                    # 默认白色
                    hollow_color_rgb = (255, 255, 255)

                print(f"镂空颜色: {hollow_color} -> RGB: {hollow_color_rgb}")

                # 确保图片是RGBA模式
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    print(f"转换后图片模式: {img.mode}")

                # 获取图片数据
                data = list(img.getdata())

                # 创建新图片数据
                new_data = []
                hollow_pixels = 0
                total_pixels = len(data)

                # 统计
                white_pixels = 0
                black_pixels = 0
                other_pixels = 0

                for i, pixel in enumerate(data):
                    if len(pixel) >= 4:
                        r, g, b, a = pixel[0], pixel[1], pixel[2], pixel[3]

                        # 判断是否是白色（要镂空的颜色）
                        if r == hollow_color_rgb[0] and g == hollow_color_rgb[1] and b == hollow_color_rgb[2]:
                            # 将白色变为完全透明
                            new_data.append((r, g, b, 0))
                            hollow_pixels += 1
                            white_pixels += 1

                        # 判断是否是深色（应该是黑色，但实际是灰色）
                        elif r < 150 and g < 150 and b < 150:  # 深色阈值
                            # 将深色转换为纯黑 (0,0,0)，这样窗口透明机制会处理它
                            new_data.append((0, 0, 0, a))
                            black_pixels += 1
                            other_pixels += 1

                        else:
                            # 其他颜色保留原样
                            new_data.append((r, g, b, a))
                            other_pixels += 1

                # 更新图片数据
                img.putdata(new_data)

                # 打印调试信息
                print(f"镂空处理完成:")
                print(f"  - 白色像素(镂空): {white_pixels}/{total_pixels} ({white_pixels / total_pixels * 100:.1f}%)")
                print(
                    f"  - 深色像素(转为纯黑): {black_pixels}/{total_pixels} ({black_pixels / total_pixels * 100:.1f}%)")
                print(f"  - 其他像素: {other_pixels}/{total_pixels} ({other_pixels / total_pixels * 100:.1f}%)")
            else:
                print(f"普通图片框模式: 不进行镂空处理")

            # 调整图片大小
            if size_option == 'image_size':
                img_width, img_height = img.size
                max_width = 600
                max_height = 400

                if img_width > max_width or img_height > max_height:
                    ratio = min(max_width / img_width, max_height / img_height)
                    img_width = int(img_width * ratio)
                    img_height = int(img_height * ratio)
                    img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            else:
                img_width = custom_width
                img_height = custom_height
                img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)

            # 创建 PhotoImage
            photo = ImageTk.PhotoImage(img, master=popup)

            # 创建图片标签 - 根据模式设置背景色
            if hollow_enabled:
                img_label = tk.Label(popup, image=photo, bg='black', bd=0, highlightthickness=0)
            else:
                # 普通模式：使用系统默认背景色
                img_label = tk.Label(popup, image=photo, bg='white', bd=0, highlightthickness=0)
            img_label.image = photo
            img_label.pack(fill='both', expand=True)

            # 获取窗口的最终位置（使用传递进来的 position）
            if position:
                # 检查是否需要对位置进行重新计算
                # 如果是镂空模式且是对齐位置，需要重新计算（因为实际尺寸可能不同）
                if hollow_enabled and 'window_position' in cze and cze['window_position'].get('type') == 'align':
                    # 重新计算对齐位置（使用实际图片尺寸）
                    position_info = cze['window_position']
                    # 使用 calculate_aligned_position_with_actual_size 重新计算
                    from types import MethodType
                    if hasattr(self, 'calculate_aligned_position_with_actual_size'):
                        screen_x, screen_y = self.calculate_aligned_position_with_actual_size(
                            position_info, img_width, img_height)
                        final_x, final_y = screen_x, screen_y
                        print(f"镂空窗口重新计算对齐位置（使用实际尺寸）: ({final_x}, {final_y})")
                    else:
                        # 如果方法不存在，直接使用传递的位置
                        final_x, final_y = position
                        print(f"使用传递进来的位置（未重新计算）: ({final_x}, {final_y})")
                else:
                    # 非镂空模式或非对齐位置，直接使用计算好的位置
                    final_x, final_y = position
                    print(f"使用传递进来的位置: ({final_x}, {final_y})")
            else:
                # 如果没有传递位置，使用默认居中
                final_x = (self.screen_width - img_width) // 2
                final_y = (self.screen_height - img_height) // 2

            # 如果启用了进入动画（镂空动画或普通动画）
            if hollow_animation or normal_animation:
                if hollow_enabled and hollow_animation:
                    print("✓ 镂空模式进入动画已启用，开始播放动画")
                elif not hollow_enabled and normal_animation:
                    print("✓ 普通模式进入动画已启用，开始播放动画")

                # 动画参数
                animation_duration = 150  # 0.15秒 = 150毫秒（原来是300）
                steps = 15  # 动画步数（减少步数让动画更快）
                delay = animation_duration // steps  # 每步延迟

                # 记录当前窗口位置作为目标位置（可能已被全局命令修改）
                target_x = final_x
                target_y = final_y
                target_width = img_width
                target_height = img_height

                # 计算起始位置（下方30像素，相对于当前目标位置）
                start_y = target_y + 30  # 从下方30像素开始
                print(f"进入动画: 起始Y={start_y}, 目标Y={target_y}, 时长{animation_duration}ms")

                # 先把窗口移到起始位置，并设置初始缩放为60%
                popup.geometry(f"{target_width}x{target_height}+{target_x}+{start_y}")
                popup.update_idletasks()

                # 执行动画
                def run_enter_animation():
                    current_step = 0

                    def animation_step():
                        nonlocal current_step
                        if current_step > steps:
                            # 动画结束，确保在目标位置和正常大小
                            try:
                                popup.geometry(f"{target_width}x{target_height}+{target_x}+{target_y}")
                                popup.update_idletasks()
                                print("动画完成")
                            except:
                                pass
                            return

                        # 计算当前进度 (0 到 1)
                        progress = current_step / steps

                        # 缓动函数：ease-out (先快后慢)
                        progress_eased = 1 - (1 - progress) * (1 - progress)

                        # 计算当前位置：从start_y移动到target_y
                        current_y = start_y + (target_y - start_y) * progress_eased

                        # 计算当前缩放比例：从60%到100%
                        scale = 0.6 + 0.4 * progress_eased
                        current_width = int(target_width * scale)
                        current_height = int(target_height * scale)

                        # 计算缩放后的位置偏移，保持居中
                        current_x = target_x - (current_width - target_width) // 2
                        current_y_adj = int(current_y) - (current_height - target_height) // 2

                        try:
                            # 更新位置和大小
                            popup.geometry(f"{current_width}x{current_height}+{current_x}+{current_y_adj}")
                            popup.update_idletasks()
                        except:
                            pass

                        current_step += 1
                        popup.after(delay, animation_step)

                    # 开始动画
                    animation_step()

                # 立即开始动画
                run_enter_animation()

                # 定义退出动画函数（使用窗口当前实际位置）
                def play_exit_animation():
                    """播放退出动画（基于窗口当前实际位置）"""
                    print("开始播放退出动画")

                    # 获取窗口当前实际位置和大小
                    try:
                        if not popup.winfo_exists():
                            return

                        current_x_actual = popup.winfo_x()
                        current_y_actual = popup.winfo_y()
                        current_width_actual = popup.winfo_width()
                        current_height_actual = popup.winfo_height()

                        print(
                            f"退出动画: 当前实际位置=({current_x_actual}, {current_y_actual}), 大小={current_width_actual}x{current_height_actual}")
                    except:
                        # 如果无法获取，使用目标值
                        current_x_actual = target_x
                        current_y_actual = target_y
                        current_width_actual = target_width
                        current_height_actual = target_height
                        print(f"退出动画: 无法获取实际位置，使用目标位置=({current_x_actual}, {current_y_actual})")

                    def run_exit_animation():
                        current_step = 0

                        def exit_animation_step():
                            nonlocal current_step
                            if current_step > steps:
                                # 动画结束，销毁窗口
                                try:
                                    if window_class and window_class in self.named_windows:
                                        del self.named_windows[window_class]
                                    self.command_executor.remove_window(popup)
                                    popup.destroy()
                                    print("退出动画完成，窗口已销毁")
                                except:
                                    pass
                                return

                            # 计算当前进度 (0 到 1)
                            progress = current_step / steps

                            # 缓动函数：ease-in (先慢后快，反向动画)
                            progress_eased = progress * progress  # ease-in

                            # 计算目标位置：从当前位置移动到下方30像素
                            target_exit_y = current_y_actual + 30

                            # 计算当前位置：从current_y_actual移动到target_exit_y
                            current_y = current_y_actual + (target_exit_y - current_y_actual) * progress_eased

                            # 计算当前缩放比例：从100%到60%
                            scale = 1.0 - 0.4 * progress_eased
                            current_width = int(current_width_actual * scale)
                            current_height = int(current_height_actual * scale)

                            # 计算缩放后的位置偏移，保持居中（基于当前实际位置）
                            current_x = current_x_actual - (current_width - current_width_actual) // 2
                            current_y_adj = int(current_y) - (current_height - current_height_actual) // 2

                            try:
                                # 更新位置和大小
                                popup.geometry(f"{current_width}x{current_height}+{current_x}+{current_y_adj}")
                                popup.update_idletasks()
                            except:
                                pass

                            current_step += 1
                            popup.after(delay, exit_animation_step)

                        # 开始退出动画
                        exit_animation_step()

                    # 在新线程中执行退出动画
                    threading.Thread(target=run_exit_animation, daemon=True).start()

                # 将退出动画函数保存为窗口属性，以便自动关闭时调用
                popup._has_animation = True
                popup._play_exit_animation = play_exit_animation

            else:
                # 无动画，直接显示在正确位置
                popup.geometry(f"{img_width}x{img_height}+{final_x}+{final_y}")
                popup.update_idletasks()

            # 绑定鼠标右键关闭窗口
            def close_on_right_click(event):
                # 检查是否有动画函数可用
                if (hollow_animation or normal_animation) and 'play_exit_animation' in locals():
                    # 有动画，播放退出动画
                    print("右键点击，播放退出动画")
                    play_exit_animation()
                else:
                    # 无动画或动画函数未定义，直接关闭
                    print("右键点击，直接关闭窗口")
                    if window_class and window_class in self.named_windows:
                        del self.named_windows[window_class]
                    self.command_executor.remove_window(popup)
                    try:
                        popup.destroy()
                    except:
                        pass

            img_label.bind('<Button-3>', close_on_right_click)

            print(f"完全镂空图片框创建成功: {img_width}x{img_height}")
            return True


        except Exception as e:
            print(f"创建图片框失败: {e}")
            import traceback
            traceback.print_exc()

            error_frame = tk.Frame(popup, bg='white')
            error_frame.pack(fill='both', expand=True, padx=20, pady=20)

            error_label = tk.Label(error_frame, text=f"无法加载图片:\n{str(e)}",
                                   font=('Segoe UI', 10), fg='red', bg='white')
            error_label.pack(expand=True)

            error_label.bind('<Button-1>', lambda e: popup.destroy())
            return True

    def create_windows_notification(self, cze, window_life_ms, window_class):
        """创建Windows系统通知（专为编译环境优化）"""
        title = cze.get('window_title', 'xxdz_itoc  ♪(^∇^*)')
        message = cze.get('notice_content', '')
        timeout = 5

        if window_life_ms:
            timeout = min(int(window_life_ms / 1000), 30)

        print(f"发送Windows系统通知:")
        print(f"  标题: {title}")
        print(f"  内容: {message}")
        print(f"  显示时间: {timeout}秒")

        # 方法1: 使用ctypes直接调用Windows API (最稳定，不需要额外库)
        try:
            import ctypes
            from ctypes import wintypes

            # Windows通知API
            try:
                # 尝试使用Windows 10/11的Toast通知 - 修复import *问题
                import winrt.windows.ui.notifications as notifications
                import winrt.windows.data.xml.dom as dom

                # 创建通知
                notifier = notifications.ToastNotificationManager.create_toast_notifier("小小电子xxdz_itoc")
                template = notifications.ToastNotificationManager.get_template_content(
                    notifications.ToastTemplateType.toast_text_02
                )

                xml = template.get_xml()
                doc = dom.XmlDocument()
                doc.load_xml(xml)

                # 设置标题和内容
                texts = doc.get_elements_by_tag_name("text")
                texts.item(0).inner_text = title
                if texts.length > 1:
                    texts.item(1).inner_text = message

                notification = notifications.ToastNotification(doc)
                notifier.show(notification)
                print("使用Windows Toast通知成功")
                return
            except ImportError:
                print("winrt未安装，跳过Toast通知")
            except Exception as e:
                print(f"Toast通知失败: {e}")

            # 使用传统的气球通知
            try:
                # 定义需要的Windows API
                Shell_NotifyIconW = ctypes.windll.shell32.Shell_NotifyIconW
                Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.c_void_p]
                Shell_NotifyIconW.restype = wintypes.BOOL

                NIM_ADD = 0x00000000
                NIM_DELETE = 0x00000002
                NIF_INFO = 0x00000010

                class NOTIFYICONDATAW(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.DWORD),
                        ("hWnd", wintypes.HWND),
                        ("uID", wintypes.UINT),
                        ("uFlags", wintypes.UINT),
                        ("uCallbackMessage", wintypes.UINT),
                        ("hIcon", wintypes.HANDLE),
                        ("szTip", wintypes.WCHAR * 128),
                        ("dwState", wintypes.DWORD),
                        ("dwStateMask", wintypes.DWORD),
                        ("szInfo", wintypes.WCHAR * 256),
                        ("uVersion", wintypes.UINT),
                        ("szInfoTitle", wintypes.WCHAR * 64),
                        ("dwInfoFlags", wintypes.DWORD),
                        ("guidItem", wintypes.BYTE * 16),
                        ("hBalloonIcon", wintypes.HANDLE)
                    ]

                # 创建一个隐藏窗口作为通知的父窗口
                import tkinter as tk
                temp_root = tk.Tk()
                temp_root.withdraw()
                hwnd = int(temp_root.winfo_id())

                # 创建通知数据
                nid = NOTIFYICONDATAW()
                nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
                nid.hWnd = hwnd
                nid.uID = 1
                nid.uFlags = NIF_INFO
                nid.szInfo = message[:255]
                nid.szInfoTitle = title[:63]
                nid.dwInfoFlags = 0x01  # 信息图标

                # 添加通知
                if Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
                    print("使用Windows气球通知成功")

                    # 延迟后删除通知图标
                    def cleanup():
                        try:
                            temp_root.after(timeout * 1000,
                                            lambda: Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid)))
                            temp_root.after(timeout * 1000 + 1000, temp_root.destroy)
                        except:
                            pass

                    temp_root.after(100, cleanup)
                    return
                else:
                    temp_root.destroy()
                    print("添加气球通知失败")
            except Exception as e:
                print(f"气球通知失败: {e}")
                try:
                    temp_root.destroy()
                except:
                    pass
        except Exception as e:
            print(f"Windows API通知失败: {e}")

        # 方法2: 使用win10toast（如果可用）
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=timeout,
                threaded=True
            )
            print("使用win10toast发送通知成功")
            return
        except ImportError:
            print("win10toast未安装")
        except Exception as e:
            print(f"win10toast失败: {e}")

        # 方法3: 使用plyer
        if NOTIFICATION_AVAILABLE:
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="小小电子xxdz_itoc",
                    timeout=timeout
                )
                print("使用plyer发送通知成功")
                return
            except Exception as e:
                print(f"plyer失败: {e}")

        # 方法4: 使用MessageBox
        try:
            import win32api
            import win32con
            win32api.MessageBox(0, message, title,
                                win32con.MB_OK | win32con.MB_ICONINFORMATION | win32con.MB_SETFOREGROUND)
            print("使用MessageBox发送通知成功")
            return
        except ImportError:
            print("win32api未安装")
        except Exception as e:
            print(f"MessageBox失败: {e}")

        # 方法5: 使用tkinter messagebox
        try:
            import tkinter.messagebox
            import threading
            def show_msgbox():
                root = tk.Tk()
                root.withdraw()
                tkinter.messagebox.showinfo(title, message)
                root.destroy()

            threading.Thread(target=show_msgbox, daemon=True).start()
            print("使用tkinter messagebox发送通知成功")
            return
        except Exception as e:
            print(f"tkinter messagebox失败: {e}")

        # 最后的手段：控制台输出
        print(f"\n{'=' * 50}")
        print(f"通知标题: {title}")
        print(f"通知内容: {message}")
        print(f"显示时间: {timeout}秒")
        print(f"{'=' * 50}\n")

    def create_tray_icon(self):
        """创建托盘图标"""
        if not TRAY_AVAILABLE or sys.platform != 'win32':
            return False

        try:
            # 使用现有的图标或创建简单图标
            icon_image = None

            # 尝试使用现有的图标文件
            icon_paths_to_try = [
                os.path.join("ico", "zhanwei.ico"),
                "ico/zhanwei.ico",
                "ico\\zhanwei.ico",
                os.path.join(os.path.dirname(__file__), "ico", "zhanwei.ico")
            ]

            for icon_path in icon_paths_to_try:
                if os.path.exists(icon_path):
                    try:
                        icon_image = Image.open(icon_path)
                        icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                        print(f"加载托盘图标: {icon_path}")
                        break
                    except:
                        pass

            # 如果找不到图标，创建一个简单的图标
            if icon_image is None:
                icon_image = Image.new('RGB', (64, 64), color='blue')
                print("使用默认蓝色托盘图标")

            # 创建菜单 - 确保退出功能直接调用exit_program
            def on_exit():
                print("托盘菜单：用户点击退出")
                self.exit_program()

            def on_open_website():
                """打开官网"""
                print("托盘菜单：用户点击使用 xxdz Itoc 编写")
                import webbrowser
                webbrowser.open("https://xxdz-official.github.io/xxdz-Itoc/OwO.html")

            menu = pystray.Menu(
                pystray.MenuItem('使用 xxdz Itoc 编写', on_open_website),
                pystray.MenuItem('退出', on_exit)
            )

            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                "CzePlayer",
                icon_image,
                "xxdz Itoc 弹窗程序",
                menu
            )

            # 在新线程中运行托盘图标
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            print("托盘图标已创建")
            return True

        except Exception as e:
            print(f"创建托盘图标失败: {e}")
            return False

    def exit_program(self):
        """退出程序（完全退出进程）"""
        print("退出程序，终止所有进程...")

        # 设置运行标志为False，通知所有线程停止
        self.running = False

        # 停止所有音频播放
        if self.audio_loaded:
            try:
                if hasattr(self, 'is_wav') and self.is_wav and hasattr(self, 'wav_sound'):
                    self.wav_sound.stop()
                else:
                    pygame.mixer.music.stop()
                pygame.mixer.quit()
                print("音频已停止")
            except Exception as e:
                print(f"停止音频时出错: {e}")

        # 关闭所有窗口（支持动画）
        if self.current_windows:
            # 创建副本，避免在迭代时修改列表
            windows_to_close = self.current_windows.copy()

            # 检查是否有动画窗口
            has_animated_windows = False
            for window in windows_to_close:
                try:
                    if window and window.winfo_exists() and hasattr(window, '_has_animation') and window._has_animation:
                        has_animated_windows = True
                        break
                except:
                    pass

            if has_animated_windows:
                print("检测到有动画窗口，播放退出动画...")
                # 为所有动画窗口播放退出动画
                for window in windows_to_close:
                    try:
                        if window and window.winfo_exists():
                            if hasattr(window, '_has_animation') and window._has_animation:
                                if hasattr(window, '_play_exit_animation'):
                                    window._play_exit_animation()
                            else:
                                try:
                                    window.destroy()
                                except:
                                    pass
                    except Exception as e:
                        print(f"关闭窗口时出错: {e}")
                # 给动画一点时间
                time.sleep(0.3)
            else:
                # 没有动画窗口，直接关闭
                for window in windows_to_close:
                    try:
                        if window and window.winfo_exists():
                            try:
                                window.destroy()
                            except:
                                pass
                    except:
                        pass

            self.current_windows.clear()
            print("所有弹窗已关闭")

        # 清除所有命名窗口
        self.named_windows.clear()

        # 清除所有窗口编组和类名
        if hasattr(self, 'command_executor'):
            self.command_executor.window_groups.clear()
            self.command_executor.window_classes.clear()

        # 停止托盘图标
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                print("托盘图标已停止")
            except Exception as e:
                print(f"停止托盘图标时出错: {e}")

        # 退出主窗口
        if self.main_root:
            try:
                # 先尝试退出主循环
                self.main_root.quit()

                # 销毁主窗口
                try:
                    self.main_root.destroy()
                except:
                    pass
                print("主窗口已销毁")
            except Exception as e:
                print(f"销毁主窗口时出错: {e}")

        print("程序已完全退出")

        # 强制退出进程（确保完全退出）
        import os
        import signal
        try:
            # 在Windows上使用os._exit强制退出
            if sys.platform == 'win32':
                os._exit(0)
            else:
                # 在Linux/Mac上发送终止信号
                os.kill(os.getpid(), signal.SIGTERM)
        except:
            pass

        # 最后尝试退出
        sys.exit(0)

    def init_audio(self):
        """初始化音频播放器（兼容32位和64位）"""
        print("初始化音频播放器...")
        try:
            # 先尝试初始化默认频率
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                print("PyGame mixer初始化成功（44100Hz）")
            except Exception as e:
                print(f"44100Hz初始化失败，尝试22050Hz: {e}")
                try:
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
                    print("PyGame mixer初始化成功（22050Hz）")
                except Exception as e:
                    print(f"22050Hz初始化失败，尝试默认参数: {e}")
                    pygame.mixer.init()
                    print("PyGame mixer初始化成功（默认参数）")

            # 虽然文件名是Audio.mp3，但实际可能是WAV文件
            audio_files = ["Audio.mp3", "audio.mp3", "AUDIO.MP3"]

            audio_file = None
            is_actually_wav = False

            # 首先查找是否存在Audio.mp3文件
            for audio_name in audio_files:
                if os.path.exists(audio_name):
                    audio_file = audio_name
                    print(f"找到音频文件: {audio_file}")

                    # 检查文件内容，判断是否是WAV格式
                    try:
                        with open(audio_file, 'rb') as f:
                            header = f.read(12)
                            # WAV文件头部标志是"RIFF"和"WAVE"
                            if header.startswith(b'RIFF') and b'WAVE' in header:
                                is_actually_wav = True
                                print(f"检测到文件 {audio_file} 实际上是WAV格式")
                    except:
                        pass

                    break

            if audio_file:
                # 尝试多种方法加载音频
                load_success = False

                # 方法1：作为WAV加载（兼容性最好）
                if not load_success:
                    try:
                        print("尝试作为WAV文件加载...")
                        self.wav_sound = pygame.mixer.Sound(audio_file)
                        self.audio_loaded = True
                        self.is_wav = True
                        load_success = True
                        print("作为WAV文件加载成功")
                    except Exception as e:
                        print(f"作为WAV加载失败: {e}")

                # 方法2：作为MP3加载
                if not load_success:
                    try:
                        print("尝试作为MP3文件加载...")
                        pygame.mixer.music.load(audio_file)
                        self.audio_loaded = True
                        self.is_wav = False
                        load_success = True
                        print("作为MP3文件加载成功")
                    except Exception as e:
                        print(f"作为MP3加载失败: {e}")

                # 方法3：重新初始化mixer后再次尝试作为WAV加载
                if not load_success:
                    try:
                        print("重新初始化mixer后再次尝试...")
                        pygame.mixer.quit()
                        time.sleep(0.1)
                        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
                        self.wav_sound = pygame.mixer.Sound(audio_file)
                        self.audio_loaded = True
                        self.is_wav = True
                        load_success = True
                        print("重新初始化后作为WAV加载成功")
                    except Exception as e:
                        print(f"重新初始化后加载失败: {e}")

                if not load_success:
                    print("警告: 所有音频加载方法都失败")
            else:
                print("警告: 未找到音频文件，继续仅弹窗播放")

            self.audio_ready.set()
        except Exception as e:
            print(f"音频播放器初始化失败: {e}")
            self.audio_ready.set()

            self.audio_ready.set()
        except Exception as e:
            print(f"音频播放器初始化失败: {e}")
            self.audio_ready.set()

    def start_audio_playback(self):
        """开始音频播放（兼容32位和64位）"""
        if self.audio_loaded and not self.audio_started:
            try:
                if hasattr(self, 'is_wav') and self.is_wav and hasattr(self, 'wav_sound'):
                    # 播放WAV文件
                    self.wav_sound.play()
                    self.audio_started = True
                    print("开始播放WAV音频")
                else:
                    # 播放MP3文件
                    try:
                        pygame.mixer.music.play()
                        self.audio_started = True
                        print("开始播放MP3音频")
                    except Exception as e:
                        print(f"MP3播放失败，尝试重新初始化: {e}")
                        # 如果MP3播放失败，尝试重新初始化后作为WAV播放
                        try:
                            pygame.mixer.quit()
                            time.sleep(0.1)
                            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
                            if hasattr(self, 'wav_sound') and self.wav_sound:
                                self.wav_sound.play()
                                self.audio_started = True
                                print("重新初始化后播放WAV音频")
                        except Exception as e2:
                            print(f"重新初始化后播放失败: {e2}")
            except Exception as e:
                print(f"音频播放失败: {e}")
                import traceback
                traceback.print_exc()

    def schedule_window_creation(self, note_info):
        """调度窗口创建"""
        if self.prevent_new_windows:
            print(f"阻止创建新窗口: {note_info['note'].get('cze_makers', {}).get('window_title', '未知')}")
            return
        # 检查程序是否还在运行
        if not self.running:
            print("程序已退出，停止创建窗口")
            return
        if self.main_root:
            try:
                self.main_root.after(0, lambda: self.create_window_now(note_info['note']))
            except:
                pass

    def schedule_command_execution(self, command_info):
        """调度命令执行"""
        # 如果已经阻止新窗口，但仍然允许执行某些命令
        if self.prevent_new_windows:
            cmd = command_info.get('command', '')
            # 允许执行的命令类型：关闭类命令、退出程序、窗口动画、自定义CMD
            allowed_commands = ['close_', 'exit_program', 'window_animation', 'custom_cmd']
            if not any(cmd.startswith(allowed) for allowed in allowed_commands):
                print(f"阻止执行命令: {cmd}")
                return
        # 检查程序是否还在运行
        if not self.running:
            print("程序已退出，停止执行命令")
            return
        if self.main_root:
            try:
                self.main_root.after(0, lambda: self.command_executor.execute_command(command_info['command']))
            except:
                pass

    def run_main_loop(self):
        """运行主事件循环"""
        self.main_root = tk.Tk()
        self.main_root.withdraw()
        self.init_icons(self.main_root)

        # 创建托盘图标以支持气泡通知
        if TRAY_AVAILABLE and sys.platform == 'win32':
            self.create_tray_icon()

        self.ui_ready.set()
        print("UI准备就绪")
        self.main_root.mainloop()

    def play(self):
        """播放所有音符事件"""
        if not self.notes:
            print("没有可播放的音符")
            return

        print("\n=== 准备开始播放 ===")
        self.ui_ready.wait()
        self.audio_ready.wait()
        print("UI和音频都已准备就绪")

        time.sleep(0.5)

        sorted_notes = sorted(self.notes, key=lambda x: x.get('start_s', 0))
        all_events = []

        for i, note in enumerate(sorted_notes, 1):
            if 'cze_makers' in note:
                start_s = note.get('start_s', 0)
                position_info = note['cze_makers'].get('window_position')
                geometry = self.calculate_position(position_info)

                window_life_ms = self.get_window_life_time(note)
                has_life = window_life_ms is not None

                window_class = note['cze_makers'].get('window_class', '')
                has_class = bool(window_class)

                window_group = note['cze_makers'].get('window_group', '')
                has_group = bool(window_group)

                is_random = position_info and position_info.get('type') == 'random' if position_info else False

                window_type = note['cze_makers'].get('window_type', '信息框')

                image_info = ''
                if window_type == '图片框' and 'image_path' in note['cze_makers']:
                    image_path = note['cze_makers']['image_path']
                    filename = os.path.basename(image_path)
                    image_info = f" (图片: {filename})"

                notice_info = ''
                if window_type == '气泡/通知' and 'notice_content' in note['cze_makers']:
                    notice_content = note['cze_makers']['notice_content']
                    if len(notice_content) > 30:
                        notice_info = f" (通知: {notice_content[:30]}...)"
                    else:
                        notice_info = f" (通知: {notice_content})"

                all_events.append({
                    'type': 'note',
                    'index': i,
                    'start_s': start_s,
                    'title': note['cze_makers'].get('window_title', '信息框'),
                    'note': note,
                    'window_type': window_type,
                    'trigger_time': start_s,
                    'geometry': geometry,
                    'has_life': has_life,
                    'life_ms': window_life_ms,
                    'has_class': has_class,
                    'window_class': window_class,
                    'has_group': has_group,
                    'window_group': window_group,
                    'is_random': is_random,
                    'image_info': image_info,
                    'notice_info': notice_info
                })
            else:
                print(f"[{i}] 在 {note.get('start_s', 0):.3f} 秒 (无弹窗)")

        for i, cmd in enumerate(self.global_commands, 1):
            all_events.append({
                'type': 'command',
                'index': i,
                'start_s': cmd.get('time_s', 0),
                'command': cmd.get('command', ''),
                'description': cmd.get('description', '全局命令'),
                'trigger_time': cmd.get('time_s', 0)
            })

        all_events.sort(key=lambda x: x['start_s'])

        print(
            f"总共 {len(all_events)} 个事件（{len([e for e in all_events if e['type'] == 'note'])} 个音符，{len([e for e in all_events if e['type'] == 'command'])} 个命令）")

        print("\n=== 开始同步播放 ===")
        print("音频、弹窗和全局命令将在同一时刻开始...")

        self.start_time = time.time()

        def delayed_audio_start():
            time.sleep(0.2)
            self.start_audio_playback()

        audio_thread = threading.Thread(target=delayed_audio_start, daemon=True)
        audio_thread.start()

        def event_scheduler():
            try:
                for event in all_events:
                    # 检查程序是否还在运行
                    if not self.running:
                        print("程序已退出，停止事件调度")
                        return

                    wait_time = event['trigger_time']

                    if wait_time > 0:
                        elapsed = time.time() - self.start_time
                        sleep_time = max(0, wait_time - elapsed)

                        if sleep_time > 0:
                            # 分段睡眠，以便检查程序是否退出
                            sleep_interval = 0.1
                            while sleep_time > 0 and self.running:
                                time.sleep(min(sleep_interval, sleep_time))
                                sleep_time -= sleep_interval

                    # 再次检查程序是否还在运行
                    if not self.running:
                        print("程序已退出，停止事件调度")
                        return

                    elapsed_time = time.time() - self.start_time

                    if event['type'] == 'note':
                        print(
                            f"[音符 {event['index']}] 在 {elapsed_time:.3f} 秒显示弹窗 (预期: {event['start_s']:.3f}秒)")
                        print(f"    标题: {event['title']}")
                        print(
                            f"    类型: {event['window_type']}{event.get('image_info', '')}{event.get('notice_info', '')}")
                        if event['is_random']:
                            print(f"    位置: 随机位置")
                        elif event['geometry']:
                            print(f"    位置: {event['geometry']}")
                        if event['has_life']:
                            print(f"    窗口寿命: {event['life_ms']}毫秒")
                        if event['has_class']:
                            print(f"    窗口类名: {event['window_class']}")
                        if event['has_group']:
                            print(f"    窗口编组: {event['window_group']}")

                        if self.main_root and self.running:
                            try:
                                self.main_root.after(0, lambda e=event: self.create_window_now(e['note']))
                            except:
                                # 主循环可能已销毁
                                pass

                    elif event['type'] == 'command':
                        print(
                            f"[命令 {event['index']}] 在 {elapsed_time:.3f} 秒执行全局命令 (预期: {event['start_s']:.3f}秒)")
                        print(f"    命令: {event['command']}")
                        print(f"    描述: {event['description']}")

                        if self.main_root and self.running:
                            try:
                                self.main_root.after(0, lambda e=event: self.schedule_command_execution(e))
                            except:
                                # 主循环可能已销毁
                                pass

                if self.running:
                    print("\n=== Itoc播放完成 ===")
                    print("所有弹窗和命令已处理，等待用户关闭窗口...")
                    print("按 Ctrl+C 提前结束程序")

            except Exception as e:
                # 如果程序正在运行才打印错误，否则忽略
                if self.running:
                    print(f"事件调度器出错: {e}")
                # 不打印异常堆栈信息

        scheduler_thread = threading.Thread(target=event_scheduler, daemon=True)
        scheduler_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n用户中断程序")
        finally:
            if self.audio_loaded:
                try:
                    if hasattr(self, 'is_wav') and self.is_wav and hasattr(self, 'wav_sound'):
                        # 停止WAV播放
                        self.wav_sound.stop()
                    else:
                        pygame.mixer.music.stop()
                except:
                    pass

            if self.main_root:
                try:
                    self.main_root.quit()
                except:
                    pass

    def run(self):
        """运行播放器"""
        self.get_screen_resolution()
        filename = "runcze.CzeData"
        if not os.path.exists(filename):
            alt_names = ["runcze.CzeData", "runcze.czedata", "RUNCZE.CZEDATA"]
            for alt_name in alt_names:
                if os.path.exists(alt_name):
                    filename = alt_name
                    break

        print(f"加载文件: {filename}")
        if self.load_czedata(filename):
            audio_thread = threading.Thread(target=self.init_audio, daemon=True)
            audio_thread.start()

            ui_thread = threading.Thread(target=self.run_main_loop, daemon=True)
            ui_thread.start()

            time.sleep(0.5)
            self.play()
        else:
            print("请确保文件存在且格式正确")
            input("按回车键退出...")


def main():
    """主函数"""
    print("=== CzeData 小小电子xxdz Itoc v1 弹窗播放器 ===")

    print("=" * 50)

    if not NOTIFICATION_AVAILABLE:
        print("\n警告: plyer库未安装，Windows通知功能不可用")
        print("如果要使用Windows系统通知，请运行: pip install plyer")
        input("按回车键继续...")

    player = CzePlayer()
    player.run()


if __name__ == "__main__":
    main()

