#!/usr/bin/env python3
"""
to_py.py - 将CZE工程文件渲染为Python代码
现在会先生成CzeData内容，再将其嵌入到Python模板中
"""

import sys
import os
import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import re


def load_original_template():
    """加载原始模板文件"""
    try:
        # 查找模板文件路径
        template_paths = [
            os.path.join(os.path.dirname(__file__), "to_py_Original.py"),
            "sys_accessories/to_py/to_py_Original.py",
            "./sys_accessories/to_py/to_py_Original.py",
            "../sys_accessories/to_py/to_py_Original.py"
        ]

        for path in template_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()

        print(f"错误: 找不到模板文件 to_py_Original.py")
        print(f"搜索路径: {template_paths}")
        return None

    except Exception as e:
        print(f"加载模板文件失败: {e}")
        return None


def beats_to_seconds_precise(beats, bpm):
    """将节拍数转换为秒（高精度计算）"""
    if bpm <= 0:
        return 0.0
    seconds_per_beat = 60.0 / bpm
    seconds = beats * seconds_per_beat
    return seconds


def format_time_seconds(time_seconds):
    """格式化秒时间显示"""
    if time_seconds == 0:
        return "0"
    formatted = f"{time_seconds:.6f}"
    formatted = formatted.rstrip('0').rstrip('.')
    if '.' not in formatted:
        return formatted
    if len(formatted.split('.')[1]) == 0:
        return formatted + "0"
    return formatted


def convert_notes_to_seconds(notes_data, target_bpm):
    """将音符数据从节拍单位转换为秒单位"""
    converted_notes = []

    for note in notes_data:
        start_beats = float(note.get("start_beat", 0))
        duration_beats = float(note.get("duration_beat", 1))

        start_s = beats_to_seconds_precise(start_beats, target_bpm)
        duration_s = beats_to_seconds_precise(duration_beats, target_bpm)
        end_s = start_s + duration_s

        new_note = {
            "note_value": note.get("note_value", 0),
            "start_s": start_s,
            "duration_s": duration_s,
            "end_s": end_s
        }

        if "cze_makers" in note and note["cze_makers"]:
            new_note["cze_makers"] = note["cze_makers"]

        converted_notes.append(new_note)

    return converted_notes


def convert_commands_to_seconds(commands_data, target_bpm):
    """将全局命令数据从节拍单位转换为秒单位"""
    converted_commands = []

    for command in commands_data:
        beat_position = float(command.get("beat", 0))
        time_s = beats_to_seconds_precise(beat_position, target_bpm)

        new_command = {
            "description": command.get("description", "未命名命令"),
            "command": command.get("command", ""),
            "color": command.get("color", "#66ccff"),
            "beat": beat_position,
            "time_s": time_s
        }

        converted_commands.append(new_command)

    return converted_commands


class CompactPreviewTable(ttk.Frame):
    """紧凑预览表格控件"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        # 创建Treeview（表格）- 更紧凑
        self.tree = ttk.Treeview(self.main_frame, height=8, show="headings")

        # 定义列（只显示必要信息）
        columns = ("index", "type", "note", "start_s", "duration_s", "end_s")
        self.tree["columns"] = columns

        # 设置列宽度和标题
        col_configs = [
            ("index", "#", 30),
            ("type", "类型", 50),
            ("note", "音高/描述", 80),
            ("start_s", "时间(s)", 70),
            ("duration_s", "时长(s)", 70),
            ("end_s", "结束(s)", 70)
        ]

        for col_id, heading, width in col_configs:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor="center")

        # 添加滚动条
        vsb = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 使用pack布局，不要混合使用grid和pack
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # 统计信息标签（更简洁）
        self.stats_label = ttk.Label(self, text="", font=("Segoe UI", 9))
        self.stats_label.pack(pady=(3, 0))

    def update_data(self, converted_notes, converted_commands, bpm):
        """更新表格数据"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 检查是否有数据
        has_notes = converted_notes and len(converted_notes) > 0
        has_commands = converted_commands and len(converted_commands) > 0

        if not has_notes and not has_commands:
            self.stats_label.config(text="没有音符或命令数据")
            return

        # 合并音符和命令数据，用于显示
        all_items = []

        # 添加音符数据
        if has_notes:
            for i, note in enumerate(converted_notes[:80]):  # 最多显示80个音符
                all_items.append({
                    "type": "音符",
                    "display": note.get("note_value", 0),
                    "time": note.get("start_s", 0),
                    "duration": note.get("duration_s", 0),
                    "end": note.get("end_s", 0)
                })

        # 添加命令数据
        if has_commands:
            for i, command in enumerate(converted_commands[:20]):  # 最多显示20个命令
                all_items.append({
                    "type": "命令",
                    "display": command.get("description", "命令")[:15],
                    "time": command.get("time_s", 0),
                    "duration": 0,  # 命令是瞬时事件，持续时间为0
                    "end": command.get("time_s", 0)
                })

        # 按时间排序
        all_items.sort(key=lambda x: x["time"])

        # 添加数据行
        for i, item in enumerate(all_items[:100]):  # 最多显示100行
            time_str = format_time_seconds(item["time"])
            duration_str = format_time_seconds(item["duration"])
            end_str = format_time_seconds(item["end"])

            self.tree.insert("", "end", values=(
                i + 1,
                item["type"],
                item["display"],
                time_str,
                duration_str,
                end_str
            ))

        # 更新统计信息
        notes_count = len(converted_notes) if converted_notes else 0
        commands_count = len(converted_commands) if converted_commands else 0
        total_items = notes_count + commands_count

        cze_notes = 0
        if converted_notes:
            cze_notes = sum(1 for note in converted_notes if "cze_makers" in note)

        # 计算总时长（取音符和命令的最晚时间）
        all_end_times = []
        if converted_notes:
            all_end_times.extend([note["end_s"] for note in converted_notes])
        if converted_commands:
            all_end_times.extend([command["time_s"] for command in converted_commands])

        total_duration = max(all_end_times) if all_end_times else 0

        # 转换为分钟:秒格式
        minutes = int(total_duration // 60)
        seconds = total_duration % 60

        stats_text = f"音符: {notes_count} | 命令: {commands_count} | CZE配置: {cze_notes} | 时长: {minutes}:{seconds:05.2f}"

        if total_items > 100:
            stats_text += f" (显示前100个)"

        self.stats_label.config(text=stats_text)


class CodePreviewText(tk.Text):
    """代码预览文本框，PyCharm风格语法高亮"""

    def __init__(self, parent, **kwargs):
        # 设置默认字体
        default_font = ("Consolas", 10) if sys.platform == 'win32' else ("Monaco", 11)

        super().__init__(parent,
                         font=default_font,
                         bg='#1E1E1E',  # 更深的暗色背景
                         fg='#D4D4D4',  # 更亮的默认文本颜色
                         insertbackground='#FFFFFF',  # 光标颜色
                         selectbackground='#264F78',  # 更亮的选中背景色
                         selectforeground='#FFFFFF',  # 选中文本颜色
                         relief=tk.FLAT,
                         **kwargs)

        self.setup_highlighting()

    def setup_highlighting(self):
        """设置更鲜艳的语法高亮标签"""
        # 配置更鲜艳的标签样式
        self.tag_config('keyword', foreground='#FF3333', font=('Consolas', 10, 'bold'))  # 关键字 - 亮红色
        self.tag_config('string', foreground='#33CC33')   # 字符串 - 亮绿色
        self.tag_config('number', foreground='#FF9933')   # 数字 - 亮橙色
        self.tag_config('comment', foreground='#999999', font=('Consolas', 10, 'italic'))  # 注释 - 亮灰色斜体
        self.tag_config('brace', foreground='#CCCCCC')    # 括号 - 亮灰色
        self.tag_config('colon', foreground='#00FFFF')    # 冒号 - 亮青色
        self.tag_config('comma', foreground='#CCCCCC')    # 逗号 - 亮灰色
        self.tag_config('boolean', foreground='#00FFFF', font=('Consolas', 10, 'bold'))  # 布尔值 - 亮青色加粗
        self.tag_config('null', foreground='#00FFFF', font=('Consolas', 10, 'bold'))     # None - 亮青色加粗
        self.tag_config('function', foreground='#3399FF') # 函数 - 亮蓝色
        self.tag_config('class', foreground='#FFCC00')    # 类 - 亮黄色
        self.tag_config('import', foreground='#CC33FF')   # 导入 - 亮紫色
        self.tag_config('operator', foreground='#00FFFF') # 运算符 - 亮青色
        self.tag_config('def_name', foreground='#3399FF', font=('Consolas', 10, 'bold')) # 函数名 - 亮蓝色加粗
        self.tag_config('class_name', foreground='#FFCC00', font=('Consolas', 10, 'bold')) # 类名 - 亮黄色加粗
    def highlight_code(self, code_text):
        """应用的语法高亮"""
        # 清空内容
        self.delete(1.0, tk.END)

        # 插入文本
        self.insert(1.0, code_text)

        # 应用的高亮规则
        # Python关键字
        self.highlight_pattern(
            r'\b(import|from|as|def|class|return|if|elif|else|for|while|try|except|finally|with|as|global|nonlocal|lambda|yield|assert|break|continue|del|pass|raise)\b',
            'keyword')

        # 布尔值和None
        self.highlight_pattern(r'\b(True|False)\b', 'boolean')
        self.highlight_pattern(r'\bNone\b', 'null')

        # 字符串
        self.highlight_pattern(r'"[^"]*"', 'string')
        self.highlight_pattern(r"'[^']*'", 'string')

        # 数字
        self.highlight_pattern(r'\b\d+(\.\d+)?\b', 'number')

        # 注释
        self.highlight_pattern(r'#.*$', 'comment', multiline=True)

        # 括号
        self.highlight_pattern(r'[{}[\]]', 'brace')

        # 冒号和逗号
        self.highlight_pattern(r':', 'colon')
        self.highlight_pattern(r',', 'comma')

        # 运算符
        self.highlight_pattern(r'[+\-*/%=&|^<>!~]', 'operator')

        # 函数定义
        self.highlight_pattern(r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', 'def_name')

        # 类定义
        self.highlight_pattern(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class_name')

        # 函数调用
        self.highlight_pattern(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', 'function')

        # 导入语句
        self.highlight_pattern(r'^\s*(import|from)\s+', 'import', multiline=True)

    def highlight_pattern(self, pattern, tag, multiline=False):
        """应用正则表达式模式高亮"""
        start = "1.0"
        end = tk.END

        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd", "searchLimit",
                                count=count, regexp=True)
            if index == "":
                break
            if count.get() == 0:
                break

            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", f"{index}+{count.get()}c")
            self.tag_add(tag, "matchStart", "matchEnd")


def dict_to_python_literal(data, indent=0):
    """
    将Python字典转换为Python字面量字符串

    Args:
        data: Python字典或列表
        indent: 当前缩进级别

    Returns:
        Python字面量字符串
    """
    if isinstance(data, dict):
        items = []
        for key, value in data.items():
            # 递归处理值
            value_str = dict_to_python_literal(value, indent + 1)
            items.append(f"{' ' * (indent + 2)}{json.dumps(key)}: {value_str}")

        if not items:
            return "{}"

        if len(items) == 1 and len(items[0]) < 60:  # 短字典可以单行显示
            return f"{{{items[0].strip()}}}"
        else:
            return "{\n" + ",\n".join(items) + f"\n{' ' * indent}}}"

    elif isinstance(data, list):
        items = []
        for item in data:
            # 递归处理列表项
            item_str = dict_to_python_literal(item, indent + 1)
            items.append(f"{' ' * (indent + 2)}{item_str}")

        if not items:
            return "[]"

        if len(items) == 1 and len(items[0]) < 60:  # 短列表可以单行显示
            return f"[{items[0].strip()}]"
        else:
            return "[\n" + ",\n".join(items) + f"\n{' ' * indent}]"

    elif isinstance(data, str):
        # 转义字符串
        escaped = json.dumps(data, ensure_ascii=False)
        return escaped

    elif isinstance(data, bool):
        return "True" if data else "False"

    elif data is None:
        return "None"

    elif isinstance(data, (int, float)):
        return str(data)

    else:
        return json.dumps(data, ensure_ascii=False)


def show_cze_data_conversion_window(project_path, callback):
    """
    显示CZE数据转换窗口（类似to_cze_data.py的界面）

    Args:
        project_path: 工程文件路径
        callback: 回调函数，接收生成的CzeData内容
    """
    # 用于跟踪转换是否被取消
    conversion_cancelled = False

    try:
        # 先加载模板文件
        template_content = load_original_template()
        if template_content is None:
            messagebox.showerror("错误", "无法加载模板文件")
            callback(None)
            return

        # 创建渲染窗口（更大以适应完整代码预览）
        render_window = tk.Toplevel()
        render_window.title("转换CZE数据")
        render_window.geometry("1500x850")  # 加大窗口尺寸以适应完整数据
        render_window.transient(None)
        render_window.grab_set()

        def on_window_close():
            nonlocal conversion_cancelled
            conversion_cancelled = True
            callback(None)  # 明确通知取消
            render_window.destroy()

        render_window.protocol("WM_DELETE_WINDOW", on_window_close)

        # 使用PanedWindow实现左右分割
        main_paned = ttk.PanedWindow(render_window, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True, padx=8, pady=8)

        # 左侧：设置和预览区域
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)

        # 左侧内容容器
        left_container = ttk.Frame(left_frame)
        left_container.pack(fill="both", expand=True, padx=5, pady=5)

        # 标题（简洁）
        title_label = ttk.Label(left_container,
                                text="CZE数据转换器",
                                font=("Segoe UI", 13, "bold"))
        title_label.pack(pady=(0, 8))

        # 工程信息区域（紧凑）
        info_frame = ttk.LabelFrame(left_container, text="工程信息", padding="8")
        info_frame.pack(fill="x", pady=(0, 8))

        # 读取工程文件
        project_data = None
        notes_count = 0
        commands_count = 0
        target_bpm = 120.0

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # 获取基本信息
            midi_info = project_data.get("midi_info", {})
            target_bpm = float(midi_info.get("target_bpm", 120.0))
            notes_count = midi_info.get("total_notes", 0)

            # 获取全局命令信息
            global_commands = project_data.get("global_commands", [])
            commands_count = len(global_commands) if global_commands else 0

            # 紧凑显示工程信息
            info_grid = ttk.Frame(info_frame)
            info_grid.pack(fill="x", expand=True)

            infos = [
                ("文件:", os.path.basename(project_path)),
                ("音符数:", f"{notes_count}"),
                ("命令数:", f"{commands_count}"),
                ("目标BPM:", f"{target_bpm}")
            ]

            for i, (label, value) in enumerate(infos):
                row = ttk.Frame(info_grid)
                row.pack(fill="x", pady=1)
                ttk.Label(row, text=label, width=8, anchor="e").pack(side="left", padx=(0, 3))
                ttk.Label(row, text=value, font=("Segoe UI", 9)).pack(side="left")

        except Exception as e:
            ttk.Label(info_frame, text=f"读取失败: {str(e)}",
                      foreground="red", font=("Segoe UI", 9)).pack(anchor="w", pady=2)

        # BPM设置区域（紧凑）
        bpm_frame = ttk.LabelFrame(left_container, text="BPM设置", padding="8")
        bpm_frame.pack(fill="x", pady=(0, 8))

        # BPM输入
        bpm_row = ttk.Frame(bpm_frame)
        bpm_row.pack(fill="x", pady=2)

        ttk.Label(bpm_row, text="BPM:", width=6).pack(side="left")
        bpm_var = tk.StringVar(value=str(target_bpm))
        bpm_entry = ttk.Entry(bpm_row, textvariable=bpm_var, width=10)
        bpm_entry.pack(side="left", padx=3)

        # 显示每拍秒数
        spb_label = ttk.Label(bpm_row, text="", font=("Segoe UI", 9))
        spb_label.pack(side="left", padx=8)

        def update_spb():
            try:
                bpm = float(bpm_var.get())
                if bpm > 0:
                    spb = 60.0 / bpm
                    spb_label.config(text=f"{spb:.3f}s/拍")
                else:
                    spb_label.config(text="")
            except:
                spb_label.config(text="")

        update_spb()
        bpm_var.trace("w", lambda *args: update_spb())

        # 选项设置（紧凑）
        options_frame = ttk.LabelFrame(left_container, text="选项", padding="8")
        options_frame.pack(fill="x", pady=(0, 8))

        # 选项网格布局
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill="x")

        include_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_grid, text="包含CZEmaker", variable=include_var).grid(row=0, column=0, sticky="w",
                                                                                      pady=2)

        include_beats_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_grid, text="保留节拍数据", variable=include_beats_var).grid(row=0, column=1, sticky="w",
                                                                                            pady=2, padx=10)

        include_commands_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_grid, text="包含全局命令", variable=include_commands_var).grid(row=1, column=0,
                                                                                               sticky="w", pady=2)

        # 右侧：双分割区域（数据预览和代码预览）
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)  # 给右侧更多空间

        # 使用垂直分割
        right_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # 数据预览区域
        data_preview_frame = ttk.Frame(right_paned, height=250)
        right_paned.add(data_preview_frame, weight=1)

        # 数据预览标题
        data_preview_header = ttk.Frame(data_preview_frame)
        data_preview_header.pack(fill="x", pady=(0, 5))

        ttk.Label(data_preview_header, text="数据预览",
                  font=("Segoe UI", 11, "bold")).pack(side="left")

        # 创建紧凑预览表格
        preview_table = CompactPreviewTable(data_preview_frame)
        preview_table.pack(fill="both", expand=True, padx=2, pady=2)

        # 代码预览区域
        code_preview_frame = ttk.Frame(right_paned)
        right_paned.add(code_preview_frame, weight=2)

        # 代码预览标题
        code_preview_header = ttk.Frame(code_preview_frame)
        code_preview_header.pack(fill="x", pady=(0, 5))

        ttk.Label(code_preview_header, text="Python代码预览",
                  font=("Segoe UI", 11, "bold")).pack(side="left")

        # 创建代码预览文本框
        code_preview_text = CodePreviewText(code_preview_frame, height=30)
        code_preview_scroll = ttk.Scrollbar(code_preview_frame, orient="vertical", command=code_preview_text.yview)
        code_preview_text.configure(yscrollcommand=code_preview_scroll.set)

        # 添加水平滚动条
        code_preview_hscroll = ttk.Scrollbar(code_preview_frame, orient="horizontal", command=code_preview_text.xview)
        code_preview_text.configure(xscrollcommand=code_preview_hscroll.set)

        # 使用pack布局，不要混合使用grid和pack
        code_preview_text.pack(side="left", fill="both", expand=True)
        code_preview_scroll.pack(side="right", fill="y")
        code_preview_hscroll.pack(side="bottom", fill="x")

        # 转换结果存储
        conversion_result = {"content": None, "bpm": target_bpm}

        def generate_full_preview_code():
            """生成完整的预览代码"""
            try:
                render_bpm = float(bpm_var.get())
                if render_bpm <= 0:
                    return template_content  # 返回原始模板

                if not project_data:
                    return template_content

                notes_data = project_data.get("notes", [])
                commands_data = project_data.get("global_commands", [])

                if not notes_data and not commands_data:
                    return template_content

                # 转换音符数据 - 使用完整数据
                converted_notes = []
                if notes_data:
                    converted_notes = convert_notes_to_seconds(notes_data, render_bpm)

                # 转换命令数据
                converted_commands = []
                if commands_data and include_commands_var.get():
                    converted_commands = convert_commands_to_seconds(commands_data, render_bpm)

                # 如果不包含CZEmaker配置，移除cze_makers字段
                if not include_var.get():
                    for note in converted_notes:
                        note.pop("cze_makers", None)

                # 构建预览数据结构 - 使用完整数据
                preview_data = {
                    "version": "1.0",
                    "source_project": os.path.basename(project_path),
                    "render_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "render_bpm": render_bpm,
                    "notes": converted_notes  # 完整数据
                }

                if converted_commands and include_commands_var.get():
                    preview_data["global_commands"] = converted_commands  # 完整数据

                # 只添加音频文件信息（如果存在）
                audio_file = project_data.get("audio_file", "")
                if audio_file:
                    preview_data["audio_file"] = audio_file

                # 转换为Python字面量 - 显示完整数据
                preview_cze_content = dict_to_python_literal(preview_data)

                # 替换模板中的占位符
                placeholder_text = "【=CzeData=】"

                if placeholder_text in template_content:
                    # 直接替换占位符
                    preview_code = template_content.replace(placeholder_text, preview_cze_content)
                else:
                    # 查找CZEDATA_CONTENT变量定义
                    lines = template_content.split('\n')
                    found_czedata = False

                    for i, line in enumerate(lines):
                        if 'CZEDATA_CONTENT' in line and '=' in line and '【=CzeData=】' in line:
                            # 找到CZEDATA_CONTENT变量定义（带有占位符）
                            indent = line[:len(line) - len(line.lstrip())]
                            lines[i] = f"{indent}CZEDATA_CONTENT = {preview_cze_content}"
                            preview_code = '\n'.join(lines)
                            found_czedata = True
                            break

                    if not found_czedata:
                        # 查找现有的CZEDATA_CONTENT变量
                        for i, line in enumerate(lines):
                            if line.strip().startswith('CZEDATA_CONTENT = '):
                                indent = line[:len(line) - len(line.lstrip())]
                                lines[i] = f"{indent}CZEDATA_CONTENT = {preview_cze_content}"
                                preview_code = '\n'.join(lines)
                                found_czedata = True
                                break

                    if not found_czedata:
                        # 尝试其他可能的占位符格式
                        placeholder_variants = [
                            '# ============================================================================\n# CZEDATA 内容 - 直接将你的CzeData文件内容粘贴到这里\n# ============================================================================\nCZEDATA_CONTENT = 【=CzeData=】\n# ============================================================================\n# 结束 CZEDATA 内容\n# ============================================================================',
                        ]

                        for placeholder in placeholder_variants:
                            if placeholder in template_content:
                                # 替换占位符部分
                                lines = template_content.split('\n')
                                for i, line in enumerate(lines):
                                    if 'CZEDATA_CONTENT = 【=CzeData=】' in line:
                                        indent = line[:len(line) - len(line.lstrip())]
                                        lines[i] = f"{indent}CZEDATA_CONTENT = {preview_cze_content}"
                                        preview_code = '\n'.join(lines)
                                        break
                                else:
                                    # 直接替换整个占位符块
                                    preview_code = template_content.replace(placeholder,
                                                                            f"# ============================================================================\n# CZEDATA 内容\n# ============================================================================\nCZEDATA_CONTENT = {preview_cze_content}\n# ============================================================================\n# 结束 CZEDATA 内容\n# ============================================================================")
                                break
                        else:
                            # 如果找不到，返回原始模板
                            preview_code = template_content

                return preview_code

            except ValueError:
                return template_content
            except Exception as e:
                print(f"生成预览代码错误: {e}")
                return template_content

        # 更新预览函数
        def update_preview():
            try:
                render_bpm = float(bpm_var.get())
                if render_bpm <= 0:
                    return

                if not project_data:
                    return

                notes_data = project_data.get("notes", [])
                commands_data = project_data.get("global_commands", [])

                if not notes_data and not commands_data:
                    return

                # 转换完整数据用于表格预览
                converted_notes = []
                if notes_data:
                    converted_notes = convert_notes_to_seconds(notes_data, render_bpm)

                # 转换命令数据
                converted_commands = []
                if commands_data and include_commands_var.get():
                    converted_commands = convert_commands_to_seconds(commands_data, render_bpm)

                # 如果不包含CZEmaker配置，移除cze_makers字段
                if not include_var.get():
                    for note in converted_notes:
                        note.pop("cze_makers", None)

                # 更新数据预览表格
                preview_table.update_data(converted_notes, converted_commands, render_bpm)

                # 生成完整的预览代码
                preview_code = generate_full_preview_code()
                code_preview_text.highlight_code(preview_code)

                # 存储转换结果
                conversion_result["bpm"] = render_bpm
                conversion_result["include_cze"] = include_var.get()
                conversion_result["include_commands"] = include_commands_var.get()
                conversion_result["include_beats"] = include_beats_var.get()

            except ValueError:
                pass
            except Exception as e:
                print(f"预览更新错误: {e}")

        # 更新预览按钮
        preview_btn = ttk.Button(data_preview_header, text="刷新预览",
                                 command=update_preview, width=10)
        preview_btn.pack(side="right", padx=(5, 0))

        # 转换按钮区域
        button_frame = ttk.Frame(left_container)
        button_frame.pack(fill="x", pady=(8, 0))

        # 开始转换函数
        def start_conversion():
            nonlocal conversion_cancelled
            # 验证BPM值
            try:
                render_bpm = float(bpm_var.get())
                if render_bpm <= 0:
                    messagebox.showwarning("BPM错误", "BPM必须大于0")
                    return
            except ValueError:
                messagebox.showwarning("BPM错误", "请输入有效的BPM数值")
                return

            try:
                # 读取工程数据
                if not project_data:
                    with open(project_path, 'r', encoding='utf-8') as f:
                        current_project_data = json.load(f)
                else:
                    current_project_data = project_data

                # 获取音符数据
                notes_data = current_project_data.get("notes", [])

                # 获取全局命令数据
                commands_data = []
                if include_commands_var.get():
                    commands_data = current_project_data.get("global_commands", [])

                # 转换节拍到秒
                converted_notes = convert_notes_to_seconds(notes_data, render_bpm)

                # 转换命令节拍到秒
                converted_commands = []
                if commands_data:
                    converted_commands = convert_commands_to_seconds(commands_data, render_bpm)

                # 根据选项过滤音符数据
                filtered_notes = []
                for note in converted_notes:
                    new_note = {
                        "note_value": note.get("note_value", 0),
                        "start_s": note.get("start_s", 0),
                        "duration_s": note.get("duration_s", 0),
                        "end_s": note.get("end_s", 0)
                    }

                    # 只添加CZEmaker配置（如果存在且需要）
                    if include_var.get() and "cze_makers" in note and note["cze_makers"]:
                        new_note["cze_makers"] = note["cze_makers"]

                    # 如果保留节拍数据
                    if include_beats_var.get():
                        # 查找原始节拍数据
                        for original_note in notes_data:
                            if original_note.get("note_value") == note.get("note_value") and \
                                    abs(float(original_note.get("start_beat", 0)) - note.get("start_s",
                                                                                             0) * render_bpm / 60) < 0.001:
                                new_note["start_beat"] = original_note.get("start_beat", 0)
                                new_note["duration_beat"] = original_note.get("duration_beat", 0)
                                break

                    filtered_notes.append(new_note)

                # 构建CZE数据结构
                cze_data = {
                    "version": "1.0",
                    "source_project": os.path.basename(project_path),
                    "render_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "render_bpm": render_bpm,
                    "notes": filtered_notes
                }

                # 添加全局命令数据
                if converted_commands:
                    cze_data["global_commands"] = converted_commands

                # 只添加音频文件信息（如果存在）
                audio_file = current_project_data.get("audio_file", "")
                if audio_file:
                    cze_data["audio_file"] = audio_file

                # 将数据传递给回调函数
                render_window.destroy()
                callback(cze_data)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"转换错误详情:\n{error_details}")
                messagebox.showerror("转换错误", f"转换失败:\n{str(e)}")

        def cancel_conversion():
            nonlocal conversion_cancelled
            conversion_cancelled = True
            render_window.destroy()
            callback(None)  # 明确通知取消

        # 按钮布局
        ttk.Button(button_frame, text="转换并继续", command=start_conversion,
                   width=12).pack(side="right", padx=3)
        ttk.Button(button_frame, text="取消", command=cancel_conversion,
                   width=10).pack(side="right", padx=3)

        # 添加预览说明标签
        preview_note = ttk.Label(left_container,
                                 text="注：代码预览显示完整的最终Python代码",
                                 font=("Segoe UI", 8),
                                 foreground="#666666")
        preview_note.pack(pady=(5, 0))

        # 初始更新预览
        render_window.after(100, update_preview)

        # 等待窗口关闭
        render_window.wait_window()

        # 如果窗口关闭但未执行转换，通知取消
        if not conversion_cancelled:
            callback(None)

    except Exception as e:
        messagebox.showerror("初始化失败", f"无法创建转换窗口：{str(e)}")
        callback(None)


def render_cze_to_python(project_path):
    """将CZE工程文件渲染为Python代码（先转换为CzeData）"""
    print(f"正在处理工程文件: {project_path}")

    # 先加载模板文件
    template_content = load_original_template()
    if template_content is None:
        return False

    # 定义回调函数，用于接收CzeData内容
    conversion_completed = False
    conversion_result = None

    def on_cze_data_converted(cze_data_dict):
        nonlocal conversion_completed, conversion_result

        if cze_data_dict is None:
            print("用户取消转换")
            conversion_completed = True
            conversion_result = False
            return False

        # 存储转换结果
        conversion_result = cze_data_dict
        conversion_completed = True
        return True

    # 显示转换窗口，传入回调函数
    show_cze_data_conversion_window(project_path, on_cze_data_converted)

    # 等待转换窗口完成
    while not conversion_completed:
        try:
            tk._default_root.update()
            time.sleep(0.1)
        except:
            break

    # 如果没有转换结果，返回False
    if conversion_result is None or conversion_result is False:
        return False

    # 现在我们有CzeData字典，需要转换为Python代码并替换到模板中
    try:
        # 将字典转换为Python字面量字符串
        cze_content = dict_to_python_literal(conversion_result)

        # 在模板中查找占位符
        placeholder_text = "【=CzeData=】"

        if placeholder_text in template_content:
            # 直接替换占位符
            python_code = template_content.replace(placeholder_text, cze_content)
            print("成功替换模板占位符")
        else:
            # 查找CZEDATA_CONTENT变量定义
            lines = template_content.split('\n')
            found_czedata = False

            for i, line in enumerate(lines):
                if 'CZEDATA_CONTENT' in line and '=' in line and '【=CzeData=】' in line:
                    # 找到CZEDATA_CONTENT变量定义（带有占位符）
                    indent = line[:len(line) - len(line.lstrip())]

                    # 构建新的变量定义
                    new_line = f"{indent}CZEDATA_CONTENT = {cze_content}"
                    lines[i] = new_line
                    python_code = '\n'.join(lines)
                    found_czedata = True
                    print("成功替换CZEDATA_CONTENT变量（占位符）")
                    break

            if not found_czedata:
                # 查找现有的CZEDATA_CONTENT变量
                for i, line in enumerate(lines):
                    if line.strip().startswith('CZEDATA_CONTENT = '):
                        indent = line[:len(line) - len(line.lstrip())]

                        # 构建新的变量定义
                        new_line = f"{indent}CZEDATA_CONTENT = {cze_content}"
                        lines[i] = new_line
                        python_code = '\n'.join(lines)
                        found_czedata = True
                        print("成功替换现有的CZEDATA_CONTENT变量")
                        break

            if not found_czedata:
                # 尝试其他可能的占位符格式
                placeholder_variants = [
                    '# ============================================================================\n# CZEDATA 内容 - 直接将你的CzeData文件内容粘贴到这里\n# ============================================================================\nCZEDATA_CONTENT = 【=CzeData=】\n# ============================================================================\n# 结束 CZEDATA 内容\n# ============================================================================',
                ]

                for placeholder in placeholder_variants:
                    if placeholder in template_content:
                        # 替换占位符部分
                        lines = template_content.split('\n')
                        for i, line in enumerate(lines):
                            if 'CZEDATA_CONTENT = 【=CzeData=】' in line:
                                indent = line[:len(line) - len(line.lstrip())]
                                lines[i] = f"{indent}CZEDATA_CONTENT = {cze_content}"
                                python_code = '\n'.join(lines)
                                print("成功替换CZEDATA_CONTENT占位符（块中）")
                                break
                        else:
                            # 直接替换整个占位符块
                            python_code = template_content.replace(placeholder,
                                                                   f"# ============================================================================\n# CZEDATA 内容\n# ============================================================================\nCZEDATA_CONTENT = {cze_content}\n# ============================================================================\n# 结束 CZEDATA 内容\n# ============================================================================")
                        break
                else:
                    # 如果找不到，在合适的位置添加
                    # 查找导入语句结束的位置
                    import_end = 0
                    for i, line in enumerate(lines):
                        if line.strip() and not line.strip().startswith(('#', 'import ', 'from ')):
                            import_end = i
                            break

                    # 在导入语句后添加CZE数据
                    if import_end > 0:
                        insert_index = import_end
                        insert_text = f"\n# ============================================================================\n# CZEDATA 内容\n# ============================================================================\nCZEDATA_CONTENT = {cze_content}\n# ============================================================================\n# 结束 CZEDATA 内容\n# ============================================================================\n"
                        lines.insert(insert_index, insert_text)
                        python_code = '\n'.join(lines)
                        print(f"在行 {insert_index} 插入CZE数据内容")
                    else:
                        # 如果还是找不到，在文件末尾添加
                        python_code = template_content + f"\n\n# ===== CZE数据内容 =====\nCZEDATA_CONTENT = {cze_content}"
                        print("在文件末尾添加CZE数据内容")

        # 让用户选择保存路径
        root = tk.Tk()
        root.withdraw()

        # 获取工程文件名（不含扩展名）
        project_name = os.path.splitext(os.path.basename(project_path))[0]

        # 设置默认文件名
        default_filename = f"{project_name}_render.py"

        # 弹出保存对话框
        save_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")],
            title="保存Python代码",
            initialfile=default_filename
        )

        if not save_path:
            print("用户取消保存")
            return False  # 明确返回False表示取消

        # 保存Python文件
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(python_code)

        print(f"Python代码已生成: {save_path}")
        print(f"文件大小: {len(python_code)} 字节")

        # 显示统计信息
        template_size = len(template_content)
        result_size = len(python_code)
        cze_size = len(cze_content)

        print(f"\n统计信息:")
        print(f"  模板文件: {template_size} 字节")
        print(f"  CZE数据: {cze_size} 字节")
        print(f"  生成文件: {result_size} 字节")
        print(f"  数据占比: {(result_size - template_size) / result_size * 100:.1f}%")

        # 显示成功消息
        messagebox.showinfo("转换完成",
                            f"Python代码生成成功！\n\n"
                            f"输出文件: {os.path.basename(save_path)}\n"
                            f"文件大小: {result_size:,} 字节\n"
                            f"CZE数据大小: {cze_size:,} 字节")

        return True

    except Exception as e:
        print(f"生成Python文件失败: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("生成失败", f"生成Python文件失败:\n{str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将CZE工程文件渲染为Python代码')
    parser.add_argument('project_path', help='CZE工程文件路径')

    args = parser.parse_args()

    if not os.path.exists(args.project_path):
        print(f"错误: 文件不存在: {args.project_path}")
        sys.exit(1)

    # 检查模板文件是否存在
    if load_original_template() is None:
        print("错误: 模板文件加载失败，无法继续")
        sys.exit(1)

    # 检查是否是Tkinter环境
    try:
        # 初始化Tkinter但不显示主窗口
        root = tk.Tk()
        root.withdraw()

        # 执行转换
        success = render_cze_to_python(args.project_path)

        if success:
            print("\n转换成功！")
            sys.exit(0)
        else:
            print("\n转换失败或已取消")
            sys.exit(1)

    except Exception as e:
        print(f"Tkinter初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()